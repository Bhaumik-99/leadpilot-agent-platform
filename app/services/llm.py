import json
from typing import Any

from app.config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def structured_decision(self, system: str, user: str) -> dict[str, Any] | None:
        if not self.client:
            return None
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
