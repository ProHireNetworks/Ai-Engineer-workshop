
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from backend.models.schemas import TravelPreferences, ResearchResult


load_dotenv()


def create_research_agent():
    """Create an AI agent for researching travel destinations."""

    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL")

    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is missing in .env file.")

    if not model_name or model_name == "your_model_name_here":
        raise ValueError("GROQ_MODEL is missing in .env file.")

    llm = ChatGroq(
        model=model_name,
        temperature=0.3,
        api_key=api_key,
    )

    structured_llm = llm.with_structured_output(ResearchResult)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are TripMate AI's Travel Research Agent.

                Research the requested travel destination.

                Provide:
                1. Destination overview.
                2. Popular tourist attractions.
                3. Famous local foods.
                4. Local transportation options.
                5. Useful travel tips.
                6. Important safety and travel notes.

                Important rules:
                - Give practical and relevant information.
                - Do not invent exact prices or opening hours.
                - Do not claim live availability or current verification.
                - Clearly mention information that needs verification.
                - Return a complete structured research result.
                """
            ),
            (
                "human",
                "Research this destination using these preferences:\n{preferences}"
            ),
        ]
    )

    return prompt | structured_llm


def research_destination(
    preferences: TravelPreferences
) -> ResearchResult:
    """Research a destination based on user preferences."""

    agent = create_research_agent()

    result = agent.invoke(
        {
            "preferences": preferences.model_dump_json()
        }
    )

    return result
