import uuid
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import service as audit
from app.auth.deps import CarerUser, ClinicianUser, CurrentUserDep, DbDep
from app.carers.access import get_supported_patient
from app.exercises.models import Stimulus
from app.patients.access import get_accessible_patient
from app.patients.models import Patient
from app.personal import service
from app.personal.models import PersonalPhoto
from app.users.models import Role, User

carer_router = APIRouter(prefix="/carer/patients/{patient_id}/words", tags=["personal words"])
clinician_router = APIRouter(
    prefix="/patients/{patient_id}/personal-words", tags=["personal words"]
)
photo_router = APIRouter(prefix="/personal-photos", tags=["personal words"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")


class PersonalWord(BaseModel):
    id: str
    word: str
    also_accepted: list[str]
    image_url: str
    added_by: str | None


async def _out(db: AsyncSession, words: list[Stimulus]) -> list[PersonalWord]:
    names = dict(
        (
            await db.execute(
                select(User.id, User.display_name).where(
                    User.id.in_({w.added_by for w in words if w.added_by})
                )
            )
        ).all()
    )
    return [
        PersonalWord(
            id=str(w.id),
            word=w.target,
            also_accepted=[a for a in w.accepted_answers if a != w.target.lower()],
            image_url=w.image_path,
            added_by=names.get(w.added_by),
        )
        for w in words
    ]


async def _add(
    db: AsyncSession, patient: Patient, actor_id: uuid.UUID, word: str, also: str, photo: UploadFile
) -> PersonalWord:
    raw = await photo.read(service.MAX_UPLOAD_BYTES + 1)
    try:
        stim = await service.add_word(db, patient.id, actor_id, word, also.split(","), raw)
    except service.PhotoError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None
    await audit.record(
        db,
        "personal_word.added",
        "success",
        actor_user_id=actor_id,
        target_type="patient",
        target_id=patient.id,
        details={"stimulus_id": str(stim.id)},
    )
    return (await _out(db, [stim]))[0]


async def _remove(db: AsyncSession, patient: Patient, actor_id: uuid.UUID, word_id: uuid.UUID):
    if not await service.remove_word(db, patient.id, word_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Word not found.")
    await audit.record(
        db,
        "personal_word.removed",
        "success",
        actor_user_id=actor_id,
        target_type="patient",
        target_id=patient.id,
        details={"stimulus_id": str(word_id)},
    )


Word = Annotated[str, Form(min_length=1, max_length=40)]
Also = Annotated[str, Form(max_length=200)]


# ---------- carers ----------


@carer_router.get("", response_model=list[PersonalWord])
async def carer_list(patient_id: uuid.UUID, user: CarerUser, db: DbDep) -> list[PersonalWord]:
    if (patient := await get_supported_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    return await _out(db, await service.words_of(db, patient.id))


@carer_router.post("", response_model=PersonalWord, status_code=status.HTTP_201_CREATED)
async def carer_add(
    patient_id: uuid.UUID,
    user: CarerUser,
    db: DbDep,
    photo: UploadFile,
    word: Word,
    also: Also = "",
) -> PersonalWord:
    if (patient := await get_supported_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    return await _add(db, patient, user.id, word, also, photo)


@carer_router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def carer_remove(patient_id: uuid.UUID, word_id: uuid.UUID, user: CarerUser, db: DbDep):
    if (patient := await get_supported_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    await _remove(db, patient, user.id, word_id)


# ---------- clinicians ----------


@clinician_router.get("", response_model=list[PersonalWord])
async def clinician_list(
    patient_id: uuid.UUID, user: ClinicianUser, db: DbDep
) -> list[PersonalWord]:
    if (patient := await get_accessible_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    return await _out(db, await service.words_of(db, patient.id))


@clinician_router.post("", response_model=PersonalWord, status_code=status.HTTP_201_CREATED)
async def clinician_add(
    patient_id: uuid.UUID,
    user: ClinicianUser,
    db: DbDep,
    photo: UploadFile,
    word: Word,
    also: Also = "",
) -> PersonalWord:
    if (patient := await get_accessible_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    return await _add(db, patient, user.id, word, also, photo)


@clinician_router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clinician_remove(
    patient_id: uuid.UUID, word_id: uuid.UUID, user: ClinicianUser, db: DbDep
):
    if (patient := await get_accessible_patient(db, user, patient_id)) is None:
        raise _NOT_FOUND
    await _remove(db, patient, user.id, word_id)


# ---------- the photo itself ----------


@photo_router.get("/{word_id}")
async def photo(word_id: uuid.UUID, user: CurrentUserDep, db: DbDep) -> Response:
    """Only the patient, their carers and their clinicians; anyone else gets 404."""
    stim = await db.get(Stimulus, word_id)
    row = await db.get(PersonalPhoto, word_id)
    if stim is None or row is None or stim.owner_patient_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found.")
    pid = stim.owner_patient_id
    if user.role is Role.CARER:
        allowed = await get_supported_patient(db, user, pid) is not None
    else:
        allowed = await get_accessible_patient(db, user, pid) is not None
    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found.")
    return Response(
        service.decrypt(word_id, row.data),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )
