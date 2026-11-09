import json
import os
from dataclasses import dataclass
from typing import Protocol

from .budget import BudgetGuard
from .pricing import GENERATION_MAX_TOKENS, GENERATION_MODEL, GENERATION_TEMPERATURE, estimate
from .schemas import DraftSet


class TransientFailure(Exception):
    pass


class ClientFailure(Exception):
    pass


@dataclass
class Reply:
    content: str
    model: str = 'fake'
    usage: dict | None = None
    parsed: DraftSet | None = None  # typed output when the SDK parsed it; content stays the raw audit text


class LLMClient(Protocol):
    def complete(self, messages: list[dict], timeout: float = 30) -> Reply: ...


class OpenAIClient:
    def __init__(self, budget: BudgetGuard):
        self.budget = budget

    def complete(self, messages, timeout=30):
        from openai import (
            APIConnectionError,
            APITimeoutError,
            ContentFilterFinishReasonError,
            InternalServerError,
            LengthFinishReasonError,
            OpenAI,
            RateLimitError,
        )

        if not os.getenv('OPENAI_API_KEY'):
            raise ClientFailure('API credential unavailable in server environment.')
        # UTF-8 bytes are a conservative upper bound for tokenizer input plus message overhead.
        size = len(json.dumps(messages, ensure_ascii=False).encode('utf-8')) + 512
        if size > 20000:
            raise ClientFailure('Context exceeds the supported input limit.')
        reserve = self.budget.reserve(estimate(GENERATION_MODEL, size, GENERATION_MAX_TOKENS))
        try:
            client = OpenAI(max_retries=0, timeout=timeout)
            try:
                # Official SDK structured outputs: the strict JSON schema is derived from the Pydantic model.
                response = client.chat.completions.parse(
                    model=GENERATION_MODEL,
                    messages=messages,
                    max_tokens=GENERATION_MAX_TOKENS,
                    temperature=GENERATION_TEMPERATURE,
                    response_format=DraftSet,
                )
            except (LengthFinishReasonError, ContentFilterFinishReasonError) as exc:
                # Truncated or filtered output: settle the cost and return empty content so the
                # service's validator reports it and the single repair can run.
                response = exc.completion
                usage = response.usage.model_dump() if response.usage else None
                if usage:
                    self.budget.settle(
                        reserve, estimate(GENERATION_MODEL, usage['prompt_tokens'], usage['completion_tokens'])
                    )
                return Reply('', response.model, usage)
            usage = response.usage.model_dump() if response.usage else None
            if usage:
                self.budget.settle(
                    reserve, estimate(GENERATION_MODEL, usage['prompt_tokens'], usage['completion_tokens'])
                )
            message = response.choices[0].message
            return Reply(message.content or '', response.model, usage, message.parsed)
        except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError):
            raise TransientFailure('Temporary provider failure; charge reservation retained.') from None
        except Exception:
            raise ClientFailure(
                'Provider request failed; inspect configuration without exposing credentials.'
            ) from None
