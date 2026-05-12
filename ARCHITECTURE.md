# Architecture

```text
User Browser
    |
    | HTML/CSS/JS SPA
    v
Frontend
    |
    | fetch()
    v
FastAPI Backend
    |
    | validates trip data
    v
Trip Generation Service
    |
    | builds prompt / calls AI
    v
AI Service / Mock AI
    |
    v
Structured itinerary JSON
```

## Future full architecture

```text
Frontend
  - login/register
  - dashboard
  - create trip form
  - itinerary page

Backend API
  - auth routes
  - trip routes
  - itinerary generation routes

Database
  - users
  - trips
  - preferences
  - itinerary days
  - itinerary items

AI Service
  - prompt builder
  - LLM call
  - structured response parser

External APIs, optional
  - maps api
  - weather api
  - places api
```

## Database draft

```text
users
- id
- email
- password_hash
- created_at

trips
- id
- user_id
- destination
- start_date
- end_date
- budget
- travel_style
- created_at

trip_preferences
- id
- trip_id
- interests
- restrictions
- notes

itinerary_days
- id
- trip_id
- day_number
- date
- summary

itinerary_items
- id
- day_id
- title
- description
- location
- start_time
- end_time
- category
- estimated_cost
```
