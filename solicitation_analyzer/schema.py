"""The checklist item and the JSON schema the model must fill."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

CATEGORIES = {
    "deadline": ["response_due", "questions_due", "conference", "other_deadline"],
    "submission": ["submission_method", "submission_contents"],
    "format": ["page_limit", "formatting"],
    "eligibility": ["set_aside", "naics", "registration", "certification", "insurance", "participation_goal", "other_eligibility"],
    "evaluation": ["basis_of_award", "evaluation_factor"],
    "requirement": ["required_content", "work_requirement"],
}
KINDS = [kind for kinds in CATEGORIES.values() for kind in kinds]
CATEGORY_OF = {kind: cat for cat, kinds in CATEGORIES.items() for kind in kinds}

CATEGORY_TITLES = {
    "deadline": "Deadlines",
    "submission": "How to submit",
    "format": "Format and page limits",
    "eligibility": "Eligibility",
    "evaluation": "How it is evaluated",
    "requirement": "What the response must include",
}

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": KINDS},
                    "statement": {"type": "string"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "weight": {"type": "string"},
                },
                "required": ["kind", "statement", "quote", "page", "date", "time", "weight"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


@dataclass
class Item:
    kind: str
    statement: str
    quote: str
    page: int | None
    document: str
    role: str = "base"  # "base", "amendment" or "attachment"
    date: str = ""
    time: str = ""
    weight: str = ""
    verification: str = "unchecked"  # exact, fuzzy, assembled, missing
    similarity: float = 0.0
    cited_page: int | None = None
    end_page: int | None = None
    also_on: list[int] = field(default_factory=list)
    superseded_by: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def category(self) -> str:
        return CATEGORY_OF.get(self.kind, "requirement")

    @property
    def verified(self) -> bool:
        return self.verification in ("exact", "fuzzy", "assembled")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["category"] = self.category
        return data
