from typing import Literal
from pydantic import BaseModel, Field
import re

class ReviewFinding(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]

    category: Literal[
        "security",
        "bug",
        "performance",
        "maintainability",
        "best_practice"
    ]

    title: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    recommendation: str

    source: Literal["ai", "ruff", "bandit"] = "ai"


class ReviewResult(BaseModel):
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)

    overall_risk: Literal[
        "critical", "high", "medium", "low", "none"
    ] = "none"

    review_status: Literal[
        "action_required", "review_recommended", "passed"
    ] = "passed"

    statistics: dict = Field(default_factory=dict)

def clean_json_response(response: str) -> str:
    response = response.strip()

    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(
        r"\s*```$",
        "",
        response
    )
    return response.strip()