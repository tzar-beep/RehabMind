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
IMPLEMENTED_TYPES = frozenset(ExerciseType)

# Answered by tapping one of several pictures; counts as the "text" (typing or tapping) mode.
CHOICE_TYPES = frozenset({ExerciseType.WORD_RECOGNITION, ExerciseType.CATEGORY_NAMING})
# Scored like naming (one word against the target), with the PNT error type for clinicians.
NAMING_FAMILY = frozenset(
    {
        ExerciseType.PICTURE_NAMING,
        ExerciseType.SENTENCE_COMPLETION,
        ExerciseType.WORD_REPETITION,
    }
)

MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5


class Objective(enum.StrEnum):
    """Rehabilitation objectives. Each implemented exercise type trains one of them."""

    WORD_RETRIEVAL = "word_retrieval"
    SENTENCE_FORMATION = "sentence_formation"
    DESCRIPTIVE_LANGUAGE = "descriptive_language"
    REPETITION = "repetition"
    COMPREHENSION = "comprehension"
    WORD_MEANING = "word_meaning"


OBJECTIVES: dict[str, Objective] = {
    ExerciseType.PICTURE_NAMING: Objective.WORD_RETRIEVAL,
    ExerciseType.SENTENCE_CONSTRUCTION: Objective.SENTENCE_FORMATION,
    ExerciseType.PICTURE_DESCRIPTION: Objective.DESCRIPTIVE_LANGUAGE,
    # A sentence frame is a context cue for the same skill as naming.
    ExerciseType.SENTENCE_COMPLETION: Objective.WORD_RETRIEVAL,
    ExerciseType.WORD_REPETITION: Objective.REPETITION,
    ExerciseType.WORD_RECOGNITION: Objective.COMPREHENSION,
    ExerciseType.CATEGORY_NAMING: Objective.WORD_MEANING,
}

OBJECTIVE_LABELS: dict[Objective, str] = {
    Objective.WORD_RETRIEVAL: "Improve word retrieval",
    Objective.SENTENCE_FORMATION: "Improve sentence formation",
    Objective.DESCRIPTIVE_LANGUAGE: "Improve descriptive language",
    Objective.REPETITION: "Improve word repetition",
    Objective.COMPREHENSION: "Improve word understanding",
    Objective.WORD_MEANING: "Improve word meaning",
}

TARGET_SKILLS: dict[Objective, str] = {
    Objective.WORD_RETRIEVAL: "finding and saying the name of an everyday object",
    Objective.SENTENCE_FORMATION: "putting words in the right order to make a simple sentence",
    Objective.DESCRIPTIVE_LANGUAGE: "describing who is in a picture, what is happening and where",
    Objective.REPETITION: "listening to a word and saying it back clearly",
    Objective.COMPREHENSION: "matching a heard or written word to the right picture",
    Objective.WORD_MEANING: "finding the picture that belongs to a group",
}
