# AI Travel Planner

## Project description

AI Travel Planner is a web application that helps users create personalized travel itineraries.  
The user enters destination, travel dates, budget, interests and restrictions, and the system generates a day-by-day trip plan.

## Problem

Planning a trip is time-consuming and chaotic. Users need to search across many websites, compare attractions, check opening hours, estimate distances, consider budget and fit activities into a realistic schedule.

## Solution

The app collects user preferences and uses AI to generate a structured travel itinerary. The plan includes morning / afternoon / evening activities, estimated costs, travel notes and alternative suggestions.

## Target users

- tourists visiting a city for the first time
- students planning low-budget trips
- groups of friends
- users who want personalized recommendations instead of generic top-10 lists

## Main user story

As a user, I want to enter my destination, dates, budget and interests, so that I can receive a personalized day-by-day travel itinerary without spending hours searching manually.

## Additional user stories

- As a user, I want to save generated trips, so that I can return to them later.
- As a user, I want to edit generated activities, so that the plan matches my preferences.
- As a user, I want to regenerate one day of the itinerary, so that I do not need to recreate the whole trip.
- As a user, I want to get budget-friendly recommendations, so that I can plan within my financial limits.
- As a user, I want to get alternative indoor activities, so that the trip remains useful in bad weather.

## MVP scope

- Create trip form
- AI/mock AI itinerary generation
- Day-by-day itinerary view
- Save generated trips
- View saved trips

## Architecture

Frontend:
- SPA-like interface
- trip creation form
- itinerary visualization

Backend:
- FastAPI API
- validation
- trip generation endpoint
- future auth and saved trips support

Database:
- users
- trips
- trip_preferences
- itinerary_days
- itinerary_items

AI service:
- builds prompt from trip preferences
- calls LLM or mock generator
- returns structured itinerary

Optional external APIs:
- maps
- weather
- places

## Prototype

The current prototype includes a web form and a mock AI endpoint:

`POST /api/generate-itinerary`

It returns a structured itinerary that can be shown in the UI.
