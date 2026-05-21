# AI Travel Planner Prototype

A small prototype for a group WAD project: **AI-powered travel planner**.

The app lets a user enter destination, dates, budget, travel style, interests, and restrictions. FastAPI sends those preferences to OpenRouter with the async OpenRouter SDK, reads the streamed response chunks, validates the final itinerary with Pydantic, and returns the frontend-ready JSON shape used by the single-page UI.

## Stack

- Python 3.13+
- FastAPI
- Pydantic v2
- OpenRouter Python SDK
- HTML / CSS / JavaScript frontend served from `app/static/index.html`

## Run

Install dependencies and run the FastAPI app with `uv`:

```powershell
$env:OPENROUTER_API_KEY="your_openrouter_key"
uv run uvicorn app.main:app --reload
```

Or create a local `.env` file:

```text
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openrouter/free
LOG_LEVEL=INFO
```

Optional shell overrides:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-5.2"
$env:LOG_LEVEL="DEBUG"
```

Open the app:

```text
http://localhost:8000
```

## Configuration

`OPENROUTER_API_KEY` is required.

`OPENROUTER_MODEL` is optional. If it is not set, the backend uses `openrouter/free`.

`LOG_LEVEL` is optional. It defaults to `INFO`.

The backend currently uses async streaming with a 90-second OpenRouter timeout and retries retryable OpenRouter failures, including 504 stream aborts, up to 3 attempts.

## API

### `GET /`

Serves the frontend.

### `GET /health`

Returns:

```json
{
  "status": "ok"
}
```

### `POST /api/generate-itinerary`

Request:

```json
{
  "destination": "Paris",
  "start_date": "2026-06-01",
  "end_date": "2026-06-03",
  "budget": "medium",
  "travel_style": "balanced",
  "interests": ["museums", "food", "architecture"],
  "restrictions": "no long walks"
}
```

Response:

```json
{
  "destination": "Paris",
  "dates": "2026-06-01 to 2026-06-03",
  "budget": "medium",
  "travel_style": "balanced",
  "pace_note": "A balanced route with shorter walking segments.",
  "budget_note": "Mix paid attractions with low-cost cafes and public transport.",
  "restrictions_note": "Avoids long walks where possible.",
  "days": [
    {
      "summary": "Central Paris museums and food",
      "activities": [
        {
          "time": "Morning",
          "title": "Louvre area",
          "description": "Start near the museum and explore nearby covered passages.",
          "estimated_cost": "20-35 EUR"
        }
      ]
    }
  ],
  "alternatives": [
    "Replace a crowded museum with Musee de l'Orangerie if access is challenging."
  ]
}
```

Allowed request values:

- `budget`: `low`, `medium`, `high`
- `travel_style`: `relaxed`, `balanced`, `intensive`

The response is validated against the backend Pydantic model before it is returned. Extra model-generated fields are ignored so the frontend receives only the fields it uses.

## Project Idea

Problem: travel planning is time-consuming and chaotic.

Solution: AI generates a personalized itinerary based on user preferences.

## MVP

- Trip creation form
- AI itinerary generation through OpenRouter streaming
- Day-by-day plan view
- Activity cards with time, title, description, and estimated cost
- Pace, budget, and restrictions notes
- Alternative suggestions
