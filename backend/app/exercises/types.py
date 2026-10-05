import enum


class ExerciseType(enum.StrEnum):
    PICTURE_NAMING = "picture_naming"
    WORD_REPETITION = "word_repetition"
    WORD_RECOGNITION = "word_recognition"
    SENTENCE_COMPLETION = "sentence_completion"
    SENTENCE_CONSTRUCTION = "sentence_construction"
    PICTURE_DESCRIPTION = "picture_description"
    CATEGORY_NAMING = "category_naming"


class ResponseMode(enum.StrEnum):
    TEXT = "text"
    SPEECH = "speech"


# Types with a working generator and scorer. Clinicians may allow others in advance;
# they are simply not issued until implemented.
IMPLEMENTED_TYPES = frozenset({ExerciseType.PICTURE_NAMING})

MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5
