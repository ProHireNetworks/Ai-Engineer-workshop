# âœˆï¸ TripMate AI â€“ Multi-Agent Travel Planning Assistant

TripMate AI is an AI-powered travel planning application that helps users generate personalized travel itineraries, research destinations, and analyze trip budgets using multiple AI agents.

## ðŸŒŸ Features

- **Destination Research Agent:** Provides destination overviews, popular attractions, local foods, transportation options, travel tips, and important notes.
- **Travel Planner Agent:** Generates personalized day-by-day travel itineraries based on user preferences.
- **Budget Analysis Agent:** Compares estimated trip expenses against the user's budget and provides recommendations.
- **Multi-Agent Workflow:** Uses LangGraph to coordinate the three agents.
- **REST API:** FastAPI backend for travel planning requests.
- **Interactive Frontend:** React application for entering preferences and viewing generated travel plans.

## ðŸ› ï¸ Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| AI Framework | LangChain |
| Agent Orchestration | LangGraph |
| LLM Provider | Groq |
| Data Validation | Pydantic |
| Testing | Pytest, HTTPX |

## ðŸ“ Project Structure

```text
TripMate-AI/
â”‚
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ agents/
â”‚   â”‚   â”œâ”€â”€ research_agent.py
â”‚   â”‚   â”œâ”€â”€ travel_planner.py
â”‚   â”‚   â””â”€â”€ budget_agent.py
â”‚   â”‚
â”‚   â”œâ”€â”€ graph/
â”‚   â”‚   â””â”€â”€ trip_graph.py
â”‚   â”‚
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â””â”€â”€ schemas.py
â”‚   â”‚
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â””â”€â”€ routes.py
â”‚   â”‚
â”‚   â””â”€â”€ main.py
â”‚
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ App.jsx
â”‚   â”‚   â”œâ”€â”€ App.css
â”‚   â”‚   â””â”€â”€ main.jsx
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_schemas.py
â”‚   â””â”€â”€ test_api.py
â”‚
â”œâ”€â”€ knowledge_base/
â”œâ”€â”€ docs/
â”œâ”€â”€ .env.example
â”œâ”€â”€ .gitignore
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
```

## âš™ï¸ Installation and Setup

### 1. Clone the repository

```bash
git clone -b resolve-week3-conflicts https://github.com/Manasa-Pandranki/indigo-ai.git
cd indigo-ai/Week-7/TripMate-AI
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

APP_NAME=TripMate AI
DEBUG=True
```

Add your own valid Groq API key. Never commit your `.env` file.

### 5. Start the backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 6. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## ðŸ”„ Multi-Agent Workflow

The application uses LangGraph to coordinate the travel planning process.

```text
User Travel Preferences
          |
          v
   Research Agent
          |
          v
   Travel Planner Agent
          |
          v
    Budget Agent
          |
          v
  Complete Travel Plan
```

### Agent Responsibilities

1. **Research Agent:** Collects general destination information using the configured LLM.
2. **Travel Planner Agent:** Creates a structured itinerary using user preferences and research.
3. **Budget Agent:** Calculates estimated remaining budget and checks whether the trip is within budget.

## ðŸ”Œ API Endpoint

**POST** `/api/plan-trip`

Example request:

```json
{
  "origin": "Hyderabad",
  "destination": "Goa",
  "start_date": "2026-12-10",
  "end_date": "2026-12-13",
  "travelers": 2,
  "budget": 15000,
  "currency": "INR",
  "travel_style": "balanced",
  "interests": ["beaches", "local food", "sightseeing"],
  "special_requirements": "Prefer budget-friendly accommodation and local food."
}
```

The response contains three main sections:

- `research`
- `itinerary`
- `budget_analysis`

## ðŸ§ª Testing

Run the backend tests from the project root:

```bash
python -m pytest -v
```

The test suite covers:

- Travel preference validation
- Invalid travel dates
- Traveler count validation
- Activity defaults
- Budget analysis
- FastAPI home and health endpoints
- Invalid API requests
- OpenAPI documentation

## âš ï¸ Important Note

Destination research is generated using the configured language model and is not a live travel-data verification service. Verify current prices, transport schedules, opening hours, availability, and local travel advisories before booking.

## ðŸš€ Future Improvements

- Live destination search and travel information.
- Accommodation and transport integrations.
- Interactive maps and route planning.
- Detailed expense breakdowns and visual charts.
- User authentication and saved itineraries.

## ðŸ‘©â€ðŸ’» Project

**TripMate AI â€“ Multi-Agent Travel Planning Assistant**

Built as part of the AI Engineer Workshop â€“ Week 7 Project.
