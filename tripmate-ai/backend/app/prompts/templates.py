"""
TripMate AI - Prompt Templates
Reusable templates for agent input formatting and conversational context assembly.
"""

from typing import List, Optional


def format_research_prompt(
    destination: str,
    days: int,
    interests: List[str],
    travelers: int = 1,
    special_requirements: Optional[str] = None,
) -> str:
    """Formats input parameters for the Research Agent."""
    interests_str = ", ".join(interests) if interests else "General sightseeing"
    req_str = f"\nSpecial Requirements: {special_requirements}" if special_requirements else ""

    return (
        f"Please research travel recommendations for the following trip:\n"
        f"- Destination: {destination}\n"
        f"- Duration: {days} days\n"
        f"- Travelers: {travelers}\n"
        f"- Key Interests: {interests_str}{req_str}\n\n"
        f"Provide a destination overview, top recommended attractions, recommended activities, "
        f"and regional insights."
    )


def format_budget_prompt(
    destination: str,
    days: int,
    travelers: int,
    total_budget: float,
    currency: str = "INR",
) -> str:
    """Formats budget calculation parameters for the Budget Agent."""
    return (
        f"Calculate and validate the budget for the following trip:\n"
        f"- Destination: {destination}\n"
        f"- Duration: {days} days\n"
        f"- Travelers: {travelers}\n"
        f"- Target Total Budget: {total_budget:,.2f} {currency}\n\n"
        f"Provide a realistic categorical breakdown (accommodation, transportation, food, activities, contingency) "
        f"and evaluate whether this trip is financially feasible."
    )


def format_itinerary_prompt(
    destination: str,
    days: int,
    travelers: int,
    interests: List[str],
    research_summary: str,
    budget_summary: str,
) -> str:
    """Formats combined inputs for the Itinerary Agent."""
    interests_str = ", ".join(interests) if interests else "sightseeing"
    return (
        f"Generate a day-wise travel schedule based on the synthesized research and budget parameters:\n"
        f"- Destination: {destination}\n"
        f"- Days: {days}\n"
        f"- Travelers: {travelers}\n"
        f"- Traveler Interests: {interests_str}\n\n"
        f"### Research Insights:\n{research_summary}\n\n"
        f"### Budget Constraints:\n{budget_summary}\n\n"
        f"Produce a balanced, day-by-day plan with Morning, Afternoon, and Evening activities."
    )


def format_booking_prompt(
    destination: str,
    days: int,
    travelers: int,
    accommodation_budget: float,
    currency: str = "INR",
) -> str:
    """Formats inputs for the Booking Assistant Agent."""
    return (
        f"Recommend accommodation and transportation options for:\n"
        f"- Destination: {destination}\n"
        f"- Duration: {days} days\n"
        f"- Travelers: {travelers}\n"
        f"- Accommodation Budget: {accommodation_budget:,.2f} {currency}\n\n"
        f"Provide 2-3 vetted accommodation options across budget and mid-tier categories, "
        f"along with primary transit recommendations. Do not make any live bookings."
    )

