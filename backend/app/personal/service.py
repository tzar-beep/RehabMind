"""A patient's own words: photos of their people, pets and things, added by their family or
clinician. Personally relevant words are among the best-supported targets in naming
therapy, and they make practice about the patient's own life.

Privacy: a photo is re-encoded (which drops location and camera metadata), downsized, and
encrypted with AES-256-GCM before it is stored. Only the patient, their linked carers and
their assigned clinicians can load it, and deleting the word deletes the photo.
"""

import base64
import io
import os
import re
import uuid
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.exercises.models import Stimulus
from app.exercises.types import ExerciseType
from app.personal.models import PersonalPhoto

CATEGORY = "my_words"
MAX_UPLOAD_BYTES = 10_000_000
MAX_SIDE = 900  # pixels: plenty for a practice picture, small to store
MAX_WORDS = 60  # per patient
# Familiar words are usually easier; each is offered at this level, clamped to the plan.
DIFFICULTY = 1
EXERCISE_TYPES = [ExerciseType.PICTURE_NAMING.value, ExerciseType.WORD_REPETITION.value]
_WORD = re.compile(r"^[A-Za-z][A-Za-z '\-]{0,39}$")
_FORMAT = b"p1"
Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse decompression bombs


class PhotoError(ValueError):
    pass


@lru_cache
def _key() -> bytes:
    """A key for photos only, derived from the application's encryption key."""
    master = base64.b64decode(get_settings().audio_encryption_key.get_secret_value())
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"personal-photos").derive(
        master
    )


def encrypt(stimulus_id: uuid.UUID, data: bytes) -> bytes:
    nonce = os.urandom(12)
    return _FORMAT + nonce + AESGCM(_key()).encrypt(nonce, data, stimulus_id.bytes)


def decrypt(stimulus_id: uuid.UUID, blob: bytes) -> bytes:
    if blob[:2] != _FORMAT:
        raise ValueError("unknown photo format")
    # Associated data binds the photo to its word: rows cannot be swapped.
    return AESGCM(_key()).decrypt(blob[2:14], blob[14:], stimulus_id.bytes)


def process(raw: bytes) -> bytes:
    """Any common photo -> an upright JPEG at most MAX_SIDE pixels, without metadata."""
    if len(raw) > MAX_UPLOAD_BYTES:
        raise PhotoError("The photo is too large (10 MB at most).")
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.load()
            upright = ImageOps.exif_transpose(img).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise PhotoError("That file is not a photo we can read.") from None
    upright.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    upright.save(out, "JPEG", quality=85, optimize=True)  # no EXIF is written
    return out.getvalue()


def clean_word(word: str) -> str:
    word = " ".join(word.split())
    if not _WORD.match(word):
        raise PhotoError("Use letters only (up to 40), like “Priya” or “my garden”.")
    return word


async def add_word(
    db: AsyncSession,
    patient_id: uuid.UUID,
    actor_id: uuid.UUID,
    word: str,
    also: list[str],
    photo: bytes,
) -> Stimulus:
    word = clean_word(word)
    alternatives = [clean_word(a) for a in also if a.strip()][:5]
    count = await db.scalar(
        select(func.count()).where(Stimulus.owner_patient_id == patient_id, Stimulus.is_active)
    )
    if (count or 0) >= MAX_WORDS:
        raise PhotoError(f"Up to {MAX_WORDS} own words. Remove one to add another.")
    image = process(photo)
    stim_id = uuid.uuid4()
    stim = Stimulus(
        id=stim_id,
        slug=f"own-{stim_id.hex[:16]}",
        target=word,
        accepted_answers=sorted({word.lower(), *(a.lower() for a in alternatives)}),
        category=CATEGORY,
        difficulty=DIFFICULTY,
        image_path=f"/api/v1/personal-photos/{stim_id}",
        kind="photo",
        exercise_types=EXERCISE_TYPES,
        task={},
        license="own",
        attribution=None,
        source_url=None,
        catalog_version=0,
        owner_patient_id=patient_id,
        added_by=actor_id,
    )
    db.add(stim)
    await db.flush()
    db.add(PersonalPhoto(stimulus_id=stim_id, data=encrypt(stim_id, image)))
    await db.commit()
    return stim


async def words_of(db: AsyncSession, patient_id: uuid.UUID) -> list[Stimulus]:
    rows = await db.execute(
        select(Stimulus)
        .join(PersonalPhoto, PersonalPhoto.stimulus_id == Stimulus.id)
        .where(Stimulus.owner_patient_id == patient_id, Stimulus.is_active)
        .order_by(PersonalPhoto.created_at.desc())
    )
    return list(rows.scalars())


async def remove_word(db: AsyncSession, patient_id: uuid.UUID, stimulus_id: uuid.UUID) -> bool:
    """The word stops being practised and its photo is deleted. The word row stays, so
    past exercises keep their record (they show no picture)."""
    stim = await db.get(Stimulus, stimulus_id)
    if stim is None or stim.owner_patient_id != patient_id:
        return False
    stim.is_active = False
    photo = await db.get(PersonalPhoto, stimulus_id)
    if photo is not None:
        await db.delete(photo)
    await db.commit()
    return True
