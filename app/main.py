import asyncio
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openrouter import OpenRouter, errors
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

app = FastAPI(title="AI Travel Planner Prototype")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("ai_travel_planner")

DEFAULT_OPENROUTER_MODEL = "openrouter/free"
LOCAL_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
OPENROUTER_TIMEOUT_MS = 90_000
OPENROUTER_MAX_ATTEMPTS = 3
RETRYABLE_OPENROUTER_CODES = {408, 429, 500, 502, 503, 504, 524, 529}


def read_setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    if not LOCAL_ENV_PATH.exists():
        return default

    for line in LOCAL_ENV_PATH.read_text().splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue

        key, raw_value = clean_line.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")

    return default


class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    budget: Literal["low", "medium", "high"]
    travel_style: Literal["relaxed", "balanced", "intensive"]
    interests: list[str] = Field(default_factory=list)
    restrictions: str = ""

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ItineraryActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=800)
    estimated_cost: str = Field(min_length=1, max_length=120)


class ItineraryDay(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=1, max_length=200)
    activities: list[ItineraryActivity] = Field(min_length=1, max_length=8)


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    destination: str = Field(min_length=1, max_length=120)
    dates: str = Field(min_length=1, max_length=120)
    budget: Literal["low", "medium", "high"]
    travel_style: Literal["relaxed", "balanced", "intensive"]
    pace_note: str = Field(min_length=1, max_length=320)
    budget_note: str = Field(min_length=1, max_length=320)
    restrictions_note: str = Field(min_length=1, max_length=320)
    days: list[ItineraryDay] = Field(min_length=1, max_length=14)
    alternatives: list[str] = Field(default_factory=list, max_length=5)


def itinerary_schema() -> dict:
    activity_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "time": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "estimated_cost": {"type": "string"},
        },
        "required": [
            "time",
            "title",
            "description",
            "estimated_cost",
        ],
    }
    day_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "activities": {
                "type": "array",
                "items": activity_schema,
                "minItems": 1,
                "maxItems": 8,
            },
        },
        "required": ["summary", "activities"],
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "destination": {"type": "string"},
            "dates": {"type": "string"},
            "budget": {"type": "string", "enum": ["low", "medium", "high"]},
            "travel_style": {
                "type": "string",
                "enum": ["relaxed", "balanced", "intensive"],
            },
            "pace_note": {"type": "string"},
            "budget_note": {"type": "string"},
            "restrictions_note": {"type": "string"},
            "days": {
                "type": "array",
                "items": day_schema,
                "minItems": 1,
                "maxItems": 14,
            },
            "alternatives": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
            },
        },
        "required": [
            "destination",
            "dates",
            "budget",
            "travel_style",
            "pace_note",
            "budget_note",
            "restrictions_note",
            "days",
            "alternatives",
        ],
    }


def build_prompt(payload: TripRequest) -> str:
    trip_days = (payload.end_date - payload.start_date).days + 1
    interests = (
        ", ".join(payload.interests) if payload.interests else "culture, food, walking"
    )
    restrictions = payload.restrictions.strip() or "No special restrictions."

    return (
        "Generate a practical, personalized travel itinerary.\n"
        f"Destination: {payload.destination}\n"
        f"Dates: {payload.start_date} to {payload.end_date} ({trip_days} day(s))\n"
        f"Budget: {payload.budget}\n"
        f"Travel style: {payload.travel_style}\n"
        f"Interests: {interests}\n"
        f"Restrictions / notes: {restrictions}\n\n"
        "Requirements:\n"
        "- Return exactly one itinerary day for each trip day.\n"
        "- Use specific, realistic places or neighborhoods when possible.\n"
        "- Keep walking distances and restrictions in mind.\n"
        "- Estimated costs should use a concise range and currency.\n"
        "- Do not include markdown, comments, or text outside the JSON object."
    )


def openrouter_stream_error_message(error: Any) -> str:
    message = getattr(error, "message", None)
    if message:
        return str(message)

    return "OpenRouter request failed."


class OpenRouterStreamError(Exception):
    def __init__(self, error: Any):
        self.code = getattr(error, "code", None)
        self.message = openrouter_stream_error_message(error)
        super().__init__(self.message)


def is_retryable_openrouter_error(code: int | None) -> bool:
    return code in RETRYABLE_OPENROUTER_CODES


def openrouter_sdk_error_message(exc: errors.OpenRouterError) -> str:
    return exc.message or exc.body or "OpenRouter request failed."


def parse_itinerary(content: str) -> ItineraryResponse:
    decoder = json.JSONDecoder()
    validation_error: ValidationError | None = None

    for index, character in enumerate(content):
        if character != "{":
            continue

        try:
            raw_itinerary, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue

        if not isinstance(raw_itinerary, dict):
            continue

        try:
            return ItineraryResponse.model_validate(raw_itinerary)
        except ValidationError as exc:
            if validation_error is None:
                validation_error = exc

    if validation_error:
        logger.error(
            "OpenRouter itinerary validation failed. errors=%s content_preview=%r",
            validation_error.errors(),
            content[:1000],
        )
        raise HTTPException(
            status_code=502,
            detail="OpenRouter returned an invalid itinerary shape.",
        ) from validation_error

    logger.error("OpenRouter returned invalid JSON. content_preview=%r", content[:1000])
    raise HTTPException(
        status_code=502,
        detail="OpenRouter returned invalid JSON.",
    )


async def read_openrouter_stream(response_stream: Any) -> str:
    content_parts: list[str] = []
    chunk_count = 0

    async for chunk in response_stream :
        if chunk.error:
            raise OpenRouterStreamError(chunk.error)

        for choice in chunk.choices:
            if choice.finish_reason == "error":
                logger.error("OpenRouter stream ended with finish_reason=error.")
                raise HTTPException(
                    status_code=502,
                    detail="OpenRouter stream ended with an error.",
                )

            if choice.delta.content:
                chunk_count += 1
                content_parts.append(choice.delta.content)

    logger.info("OpenRouter stream completed. chunks=%s", chunk_count)

    content = "".join(content_parts).strip()
    if not content:
        logger.error(
            "OpenRouter stream ended without content. chunks=%s",
            chunk_count,
        )
        raise HTTPException(
            status_code=502, detail="OpenRouter returned an empty itinerary."
        )

    logger.info(
        "OpenRouter stream content assembled. chunks=%s characters=%s",
        chunk_count,
        len(content),
    )

    return content


async def generate_ai_itinerary(payload: TripRequest) -> ItineraryResponse:
    api_key = read_setting("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY is not configured.")
        raise HTTPException(
            status_code=500, detail="OPENROUTER_API_KEY is not configured."
        )

    model = read_setting("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    trip_days = (payload.end_date - payload.start_date).days + 1
    max_completion_tokens = min(8000, 900 + trip_days * 650)
    logger.info(
        "Generating itinerary. destination=%r start_date=%s end_date=%s "
        "budget=%s style=%s interests=%s model=%s stream=%s",
        payload.destination,
        payload.start_date,
        payload.end_date,
        payload.budget,
        payload.travel_style,
        payload.interests,
        model,
        True,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a travel-planning assistant. Produce accurate, "
                "useful, concise itineraries "
                "as valid JSON matching the supplied schema."
            ),
        },
        {"role": "user", "content": build_prompt(payload)},
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "travel_itinerary",
            "strict": True,
            "schema": itinerary_schema(),
        },
    }

    response_content = ""
    async with OpenRouter(
        api_key=api_key,
        timeout_ms=OPENROUTER_TIMEOUT_MS,
    ) as open_router:
        for attempt in range(1, OPENROUTER_MAX_ATTEMPTS + 1):
            try:
                response_stream = await open_router.chat.send_async(
                    model=model,
                    messages=messages,
                    response_format=response_format,
                    reasoning=None,
                    max_completion_tokens=max_completion_tokens,
                    stream=True,
                )
                response_content = await read_openrouter_stream(response_stream)
                break
            except OpenRouterStreamError as exc:
                should_retry = (
                    is_retryable_openrouter_error(exc.code)
                    and attempt < OPENROUTER_MAX_ATTEMPTS
                )
                logger.warning(
                    "OpenRouter stream error. attempt=%s/%s code=%s "
                    "retry=%s error=%s",
                    attempt,
                    OPENROUTER_MAX_ATTEMPTS,
                    exc.code,
                    should_retry,
                    exc.message,
                )
                if not should_retry:
                    raise HTTPException(
                        status_code=502,
                        detail=f"OpenRouter stream failed: {exc.message}",
                    ) from exc
                await asyncio.sleep(0.5 * attempt)
            except errors.OpenRouterError as exc:
                should_retry = (
                    is_retryable_openrouter_error(exc.status_code)
                    and attempt < OPENROUTER_MAX_ATTEMPTS
                )
                logger.warning(
                    "OpenRouter SDK request failed. attempt=%s/%s status=%s "
                    "retry=%s body_preview=%r",
                    attempt,
                    OPENROUTER_MAX_ATTEMPTS,
                    exc.status_code,
                    should_retry,
                    exc.body[:1000],
                )
                if not should_retry:
                    raise HTTPException(
                        status_code=502,
                        detail=openrouter_sdk_error_message(exc),
                    ) from exc
                await asyncio.sleep(0.5 * attempt)

    itinerary = parse_itinerary(response_content)
    logger.info(
        "Itinerary generated successfully. destination=%r days=%s characters=%s",
        itinerary.destination,
        len(itinerary.days),
        len(response_content),
    )
    return itinerary


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/generate-itinerary", response_model=ItineraryResponse)
async def generate_itinerary(payload: TripRequest):
    return await generate_ai_itinerary(payload)
