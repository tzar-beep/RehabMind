import io
import uuid

from PIL import Image
from sqlalchemy import select

from app.core.db import SessionLocal
from app.exercises.models import Exercise
from app.personal import service
from app.personal.models import PersonalPhoto
from app.users.models import Role
from tests.conftest import assign, create_user
from tests.test_carers import _carer
from tests.test_clinician_insights import base
from tests.test_practice import START, as_user, care, set_plan  # noqa: F401


def jpeg_with_location() -> bytes:
    """A photo carrying GPS metadata, as phones write it."""
    img = Image.new("RGB", (1600, 1200), (180, 120, 90))
    exif = Image.Exif()
    exif[0x8825] = {2: (51.0, 30.0, 0.0), 4: (0.0, 7.0, 0.0)}  # GPSInfo: latitude, longitude
    out = io.BytesIO()
    img.save(out, "JPEG", exif=exif)
    return out.getvalue()


async def _add(client, url, word="Priya", also="", photo=None):
    return await client.post(
        url,
        data={"word": word, "also": also},
        files={"photo": ("p.jpg", photo or jpeg_with_location(), "image/jpeg")},
    )


async def test_family_adds_a_word_that_the_patient_then_practises(care):  # noqa: F811
    patient, clinician, pid = care
    await create_user("admin@x.test", Role.ADMIN)
    carer = await _carer(await as_user("admin@x.test"), "p@x.test")
    url = f"/api/v1/carer/patients/{pid}/words"

    r = await _add(carer, url, "Priya", "my daughter")
    assert r.status_code == 201, r.text
    word = r.json()
    assert word["word"] == "Priya" and word["also_accepted"] == ["my daughter"]
    assert word["added_by"] == "Priya"

    # Stored encrypted, re-encoded and small, with no location metadata.
    async with SessionLocal() as db:
        row = await db.get(PersonalPhoto, uuid.UUID(word["id"]))
    assert b"\xff\xd8" not in row.data[:20]  # not a readable JPEG at rest
    stored = Image.open(io.BytesIO(service.decrypt(uuid.UUID(word["id"]), row.data)))
    assert max(stored.size) <= service.MAX_SIDE and 0x8825 not in stored.getexif()

    # Practised like any picture when the plan includes "My words".
    await set_plan(
        clinician,
        pid,
        allowed_exercise_types=["picture_naming"],
        allowed_categories=["my_words"],
        min_difficulty=2,
        max_difficulty=4,
    )
    started = (await patient.post(START)).json()
    assert "exercise" in started, started
    ex = started["exercise"]
    assert ex["image_url"] == word["image_url"]
    async with SessionLocal() as db:
        issued = await db.get(Exercise, uuid.UUID(ex["id"]))
    assert issued.difficulty == 2  # clamped into the plan
    assert issued.source != "ai"  # the AI never sees the patient's own words

    # The photo: the patient, their carer and clinician; nobody else.
    for client in (patient, carer, clinician):
        r = await client.get(word["image_url"])
        assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    stranger = await create_user("c2@x.test", Role.CLINICIAN)
    other = await create_user("p2@x.test", Role.PATIENT)
    await assign(other, stranger)
    for email in ("c2@x.test", "p2@x.test"):
        assert (await (await as_user(email)).get(word["image_url"])).status_code == 404

    # Removing the word deletes the photo.
    assert (await carer.delete(f"{url}/{word['id']}")).status_code == 204
    assert (await patient.get(word["image_url"])).status_code == 404
    assert (await carer.get(url)).json() == []


async def test_own_words_stay_with_their_patient(care):  # noqa: F811
    patient, clinician, pid = care
    url = f"{base(pid)}/personal-words"
    assert (await _add(clinician, url, "Rex")).status_code == 201
    # Another patient never gets this word, even with every category allowed.
    other = await create_user("p2@x.test", Role.PATIENT)
    c2 = await create_user("c2@x.test", Role.CLINICIAN)
    await assign(other, c2)
    pid2 = str(
        (await (await as_user("c2@x.test")).get("/api/v1/clinicians/me/patients")).json()[0]["id"]
    )
    await set_plan(await as_user("c2@x.test"), pid2, allowed_exercise_types=["picture_naming"])
    p2 = await as_user("p2@x.test")
    for _ in range(8):
        state = (await p2.post(START)).json()
        ex = state["exercise"]
        assert "personal-photos" not in (ex["image_url"] or "")
        await p2.post(
            f"/api/v1/practice/exercises/{ex['id']}/responses",
            json={"skipped": True},
        )
    async with SessionLocal() as db:
        owners = (await db.execute(select(Exercise.stimulus_id))).scalars().all()
    assert owners  # practice happened


async def test_bad_photos_and_words_are_refused(care):  # noqa: F811
    _, clinician, pid = care
    url = f"{base(pid)}/personal-words"
    assert (await _add(clinician, url, photo=b"not an image")).status_code == 422
    assert (await _add(clinician, url, word="<script>")).status_code == 422
    assert (await _add(clinician, url, word="Priya")).status_code == 201


def test_issuer_refuses_another_patients_word():
    from types import SimpleNamespace

    from app.exercises.generator import Proposal
    from app.exercises.issuer import validate

    owner, other = uuid.uuid4(), uuid.uuid4()
    stim = SimpleNamespace(
        is_active=True,
        exercise_types=["picture_naming"],
        difficulty=1,
        category="my_words",
        owner_patient_id=owner,
    )
    cs = SimpleNamespace(
        allowed_exercise_types=["picture_naming"],
        allowed_response_modes=["text"],
        allowed_categories=None,
        min_difficulty=1,
        max_difficulty=3,
        max_exercises_per_session=8,
        patient_id=other,
    )
    proposal = Proposal("picture_naming", 1, ["text"], stim, {}, {}, "rule")
    session = SimpleNamespace(planned_exercises=8, patient_id=other)
    assert "stimulus_not_this_patients" in validate(proposal, cs, session, 1)


async def test_patient_lists_their_own_words(care):  # noqa: F811
    patient, clinician, pid = care
    await _add(clinician, f"{base(pid)}/personal-words", "Rex")
    mine = (await patient.get("/api/v1/practice/my-words")).json()
    assert [w["word"] for w in mine] == ["Rex"]
    assert (await clinician.get("/api/v1/practice/my-words")).status_code == 403
