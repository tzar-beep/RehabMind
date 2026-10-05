"""Deterministic cues for picture naming (cueing hierarchy: meaning, then first sound)."""

SEMANTIC_CUES = {
    "food": "It's something you can eat or drink.",
    "animals": "It's an animal.",
    "household": "You would find this at home.",
    "transport": "It helps people travel.",
    "tools": "People use it to make or fix things.",
    "music": "It is used to make or hear music.",
    "personal": "People use this every day.",
    "nature": "You can see this outdoors.",
}
DEFAULT_SEMANTIC_CUE = "Think about where you would see this."


def phonemic_prefix(target: str) -> str:
    return target[: 2 if len(target) > 3 else 1]


def phonemic_cue(prefix: str) -> str:
    return f"It starts with “{prefix}…”"


def rule_cues(category: str, target: str) -> list[str]:
    return [
        SEMANTIC_CUES.get(category, DEFAULT_SEMANTIC_CUE),
        phonemic_cue(phonemic_prefix(target)),
    ]
