
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from backend.models.schemas import TravelPreferences, TravelItinerary
from backend.models.schemas import (
    TravelPreferences,
    TravelItinerary,
    ResearchResult,
)


load_dotenv()


def create_travel_planner_agent():
    """Create an AI agent that generates structured travel itineraries."""

    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL")

    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is missing. Please configure it in your .env file."
        )

    if not model_name or model_name == "your_model_name_here":
        raise ValueError(
            "GROQ_MODEL is missing. Please configure it in your .env file."
        )

    llm = ChatGroq(
        model=model_name,
        temperature=0.3,
        api_key=api_key,
    )

    structured_llm = llm.with_structured_output(
    TravelItinerary,
    method="json_schema",
    strict=False,
)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are TripMate AI, an expert travel planning assistant.

                Create a practical and personalized travel itinerary
                based on the user's preferences.

                Follow these rules:
                1. Create one itinerary day for each date in the requested range.
                2. Keep the itinerary within the user's specified budget.
                3. Consider the number of travelers and travel style.
                4. Include the user's interests wherever possible.
                5. Provide realistic activity descriptions and estimated costs.
                6. Use the requested currency.
                7. Do not claim that bookings, tickets, or hotel availability
                   have been verified.
                8. Treat costs as estimates, not confirmed prices.
                9. Return a complete structured itinerary.
                """
            ),
            (
                "human",
"""
User preferences:
{preferences}

Destination research:
{research}

Create the itinerary using both the preferences and research.
"""
            ),
        ]
    )

    return prompt | structured_llm


def generate_itinerary(
    preferences: TravelPreferences,
    research: ResearchResult | None = None,
) -> TravelItinerary:
    """Generate an itinerary using user preferences and research."""

    agent = create_travel_planner_agent()

    research_data = (
        research.model_dump_json()
        if research is not None
        else "No additional destination research provided."
    )

    result = agent.invoke(
        {
            "preferences": preferences.model_dump_json(),
            "research": research_data,
        }
    )

    return result
