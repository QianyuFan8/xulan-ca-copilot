"""Pydantic contracts for model output (structured outputs).

These models are passed to the OpenAI SDK as ``response_format``. The SDK derives
the strict JSON schema sent to the API and parses the reply into typed objects.
Range checks that the strict schema does not need to enforce (score 1–5, exactly
three reviews) are Python-side validators, so the schema sent to the API stays the
same shape that was used in the evaluated runs.
"""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _one_to_five(value: int) -> int:
    if not 1 <= value <= 5:
        raise ValueError('score must be an integer from 1 to 5')
    return value


Score = Annotated[int, AfterValidator(_one_to_five)]


class DraftSet(BaseModel):
    """Generation output: exactly three independent WeChat drafts."""

    model_config = ConfigDict(extra='forbid')
    candidates: list[str] = Field(min_length=3, max_length=3)


class DimensionScores(BaseModel):
    model_config = ConfigDict(extra='forbid')
    facts: Score
    context: Score
    personalization: Score
    brand: Score
    scenario: Score
    boundaries: Score
    wechat: Score


class MessageReview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scores: DimensionScores
    critical: bool
    uncertain: bool
    issues: list[str]


def _three_reviews(value: list[MessageReview]) -> list[MessageReview]:
    if len(value) != 3:
        raise ValueError('judge must return exactly three message reviews')
    return value


class SetReview(BaseModel):
    """Judge output for one candidate set."""

    model_config = ConfigDict(extra='forbid')
    messages: Annotated[list[MessageReview], AfterValidator(_three_reviews)]
    diversity: Score
    set_notes: str


DIMS = list(DimensionScores.model_fields)
