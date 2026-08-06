import json
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o-mini"


class AIGenerationError(Exception):
    pass


async def generate_json(system_prompt: str, user_input: str) -> dict:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI 호출 실패: {e}")
        raise AIGenerationError(str(e))


async def stream_completion(system_prompt: str, user_input: str) -> AsyncIterator[str]:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        stream = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            stream=True,
        )
    except Exception as e:
        logger.error(f"OpenAI 스트리밍 호출 실패: {e}")
        raise AIGenerationError(str(e))

    async def iterator() -> AsyncIterator[str]:
        try:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"OpenAI 스트리밍 도중 실패: {e}")
            raise AIGenerationError(str(e))

    return iterator()
