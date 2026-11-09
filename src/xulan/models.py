from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Status(str, Enum):  # noqa: UP042 -- StrEnum changes str() output; kept stable for the evaluated runs
    success = 'success'
    needs_information = 'needs_information'
    blocked = 'blocked'
    error = 'error'


class HistoryItem(BaseModel):
    role: Literal['client', 'advisor']
    content: str = Field(min_length=1, max_length=3000)
    timestamp: datetime | None = None


class ClientInformation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = 'synthetic-client'
    preferred_address: str = Field(default='', max_length=80)
    preferences: str = Field(default='', max_length=2000)
    relationship_stage: str = Field(default='Established contact', max_length=200)
    contact_preference: Literal['allowed', 'no_marketing', 'no_contact'] = 'allowed'
    timezone: str | None = 'Asia/Shanghai'
    last_outbound_contact: datetime | None = None


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: Literal['greeting', 'recommendation', 'care', 'reactivation', 'invitation', 'price_objection']
    client_information: ClientInformation
    conversation_history: list[HistoryItem] = Field(default_factory=list, max_length=30)
    product_information: list[str] = Field(default_factory=list, max_length=3)
    scenario_details: dict = Field(default_factory=dict)

    @field_validator('scenario_details')
    @classmethod
    def bounded_details(cls, v):
        import json

        if len(json.dumps(v, ensure_ascii=False).encode()) > 6000:
            raise ValueError('Scenario details exceed 6000 bytes')
        return v

    current_datetime: datetime

    @field_validator('current_datetime')
    @classmethod
    def aware(cls, v):
        if v.tzinfo is None:
            raise ValueError('Reference time must include UTC offset')
        return v


class GenerationResult(BaseModel):
    status: Status
    candidates: list[str] = Field(default_factory=list)
    advisories: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    information_requests: list[str] = Field(default_factory=list)
    validation_findings: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
