# AI Travel Planner Prototype

A small prototype for a group WAD project: **AI-powered travel planner**.

The prototype demonstrates the core MVP idea:

- user enters destination, dates, budget, travel style and interests
- backend receives trip preferences
- OpenRouter streams a structured day-by-day itinerary to the backend
- frontend displays the itinerary in a clean travel-planner UI

Set `OPENROUTER_API_KEY` in your shell or in a local `.env` file before running the backend.

## Stack

- Python
- FastAPI
- HTML / CSS / JavaScript
- SPA-like frontend
- OpenRouter API

## Run

```powershell
$env:OPENROUTER_API_KEY="your_openrouter_key"
uv run uvicorn app.main:app --reload
```

`.env` example:

```text
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-5.2
```

Optional:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-5.2"
$env:LOG_LEVEL="DEBUG"
```

Open:

```text
http://localhost:8000
```

## API

### POST `/api/generate-itinerary`

Request example:

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

Returns a structured AI-generated itinerary.

## Project idea

Problem: travel planning is time-consuming and chaotic.  
Solution: AI generates a personalized itinerary based on user preferences.

## MVP

- Create trip form
- AI itinerary generation
- Day-by-day plan view
- Activity cards
- Estimated budget notes
- Alternative suggestions
