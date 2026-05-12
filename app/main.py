from datetime import date
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="AI Travel Planner Prototype")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    budget: Literal["low", "medium", "high"]
    travel_style: Literal["relaxed", "balanced", "intensive"]
    interests: list[str] = Field(default_factory=list)
    restrictions: str = ""


def build_mock_itinerary(payload: TripRequest) -> dict:
    interests = payload.interests or ["culture", "food", "walking"]
    destination = payload.destination

    if payload.travel_style == "relaxed":
        pace_note = "Relaxed pace with fewer activities and more free time."
        items_per_day = 3
    elif payload.travel_style == "intensive":
        pace_note = "Intensive pace with many activities and active sightseeing."
        items_per_day = 5
    else:
        pace_note = "Balanced pace with enough sightseeing and rest."
        items_per_day = 4

    budget_notes = {
        "low": "Focus on free attractions, public transport and affordable food.",
        "medium": "Mix of paid attractions, local cafes and convenient transport.",
        "high": "Premium experiences, guided tours and comfortable restaurants.",
    }

    templates = [
        ("Morning", "Explore the historic center and main landmarks"),
        ("Late morning", "Visit a museum or cultural attraction"),
        ("Lunch", "Try a local cafe recommended for travelers"),
        ("Afternoon", "Walk through a scenic district or park"),
        ("Evening", "Dinner and optional viewpoint / nightlife area"),
    ]

    days = []
    for day_number in range(1, 4):
        activities = []
        for index, (time_label, base_title) in enumerate(templates[:items_per_day], start=1):
            interest = interests[(index + day_number - 2) % len(interests)]
            activities.append(
                {
                    "time": time_label,
                    "title": f"{base_title} in {destination}",
                    "description": (
                        f"AI suggestion focused on {interest}. "
                        f"Suitable for a {payload.budget}-budget, {payload.travel_style} trip."
                    ),
                    "estimated_cost": {
                        "low": "0–15 EUR",
                        "medium": "15–45 EUR",
                        "high": "45+ EUR",
                    }[payload.budget],
                    "category": interest,
                }
            )

        days.append(
            {
                "day": day_number,
                "summary": f"Day {day_number}: personalized route around {destination}",
                "activities": activities,
            }
        )

    return {
        "destination": destination,
        "dates": f"{payload.start_date} — {payload.end_date}",
        "budget": payload.budget,
        "travel_style": payload.travel_style,
        "pace_note": pace_note,
        "budget_note": budget_notes[payload.budget],
        "restrictions_note": payload.restrictions or "No special restrictions provided.",
        "days": days,
        "alternatives": [
            "Indoor museum route in case of bad weather",
            "Budget-friendly food market instead of restaurant",
            "Short walking route for tired travelers",
        ],
    }


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/generate-itinerary")
def generate_itinerary(payload: TripRequest):
    return build_mock_itinerary(payload)
