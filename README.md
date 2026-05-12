# AI Travel Planner Prototype

A small prototype for a group WAD project: **AI-powered travel planner**.

The prototype demonstrates the core MVP idea:

- user enters destination, dates, budget, travel style and interests
- backend receives trip preferences
- mock AI service generates a structured day-by-day itinerary
- frontend displays the itinerary in a clean travel-planner UI

This version intentionally uses a **mock AI response** instead of a real LLM call.  
It is enough for discussion, architecture presentation and UI/UX demo.

## Stack

- Python
- FastAPI
- HTML / CSS / JavaScript
- SPA-like frontend
- Mock AI service

## Run

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
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

Returns a structured mock itinerary.

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
