from __future__ import annotations

from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr

try:
    from pydantic import ConfigDict
except ImportError:  # Pydantic 1.10 compatibility
    ConfigDict = dict  # type: ignore[misc, assignment]

LLMStatus = Literal[
    "not_requested",
    "success",
    "fallback_config",
    "fallback_request",
    "fallback_invalid",
]
FallbackReason = Literal["incomplete_config", "request_failed", "invalid_response"]


class _StrictModel(BaseModel):
    if hasattr(BaseModel, "model_validate"):
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class PreprocessLLMOutput(_StrictModel):
    allowed: StrictBool | None = None
    reason: StrictStr | None = None
    warnings: list[StrictStr] | None = None
    sensitive_keywords: list[StrictStr] | None = None
    similar_record_id: StrictStr | None = None
    suggest_reuse_history: StrictBool | None = None


class InterpretationLLMOutput(_StrictModel):
    summary: StrictStr | None = None
    answer_to_question: StrictStr | None = None
    hexagram_structure: StrictStr | None = None
    current_situation: StrictStr | None = None
    changing_line_focus: StrictStr | None = None
    change_trend: StrictStr | None = None
    actionable_advice: list[StrictStr] | None = None
    risks: list[StrictStr] | None = None
    disclaimer: StrictStr | None = None


class PreprocessResult(_StrictModel):
    schema_version: Literal[2] = 2
    allowed: StrictBool = True
    reason: StrictStr = ""
    warnings: list[StrictStr] = Field(default_factory=list)
    sensitive_keywords: list[StrictStr] = Field(default_factory=list)
    similar_record_id: StrictStr | None = None
    suggest_reuse_history: StrictBool = False
    history_count: StrictInt = 0
    llm_used: StrictBool = False
    llm_status: LLMStatus = "not_requested"
    fallback_reason: FallbackReason | None = None


class InterpretationResult(_StrictModel):
    schema_version: Literal[2] = 2
    summary: StrictStr = ""
    answer_to_question: StrictStr = ""
    hexagram_structure: StrictStr = ""
    current_situation: StrictStr = ""
    changing_line_focus: StrictStr = ""
    change_trend: StrictStr = ""
    actionable_advice: list[StrictStr] = Field(default_factory=list)
    risks: list[StrictStr] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: StrictStr = ""
    llm_used: StrictBool = False
    llm_status: LLMStatus = "not_requested"
    fallback_reason: FallbackReason | None = None


def model_dump(model: BaseModel, *, exclude_none: bool = False) -> dict[str, Any]:
    """Dump models on both Pydantic 1.x and 2.x."""

    dump = getattr(model, "model_dump", None)
    if dump is not None:
        return dump(exclude_none=exclude_none)
    return model.dict(exclude_none=exclude_none)


ModelT = TypeVar("ModelT", bound=BaseModel)


def model_validate(model_type: type[ModelT], value: dict[str, Any]) -> ModelT:
    """Validate models on both Pydantic 1.x and 2.x."""

    validate = getattr(model_type, "model_validate", None)
    if validate is not None:
        return validate(value)
    return model_type.parse_obj(value)
