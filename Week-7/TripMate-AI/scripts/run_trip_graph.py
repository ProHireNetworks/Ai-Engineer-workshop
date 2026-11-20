
import traceback

from backend.models.schemas import TravelPreferences
from backend.graph.trip_graph import create_trip_graph


preferences = TravelPreferences(
    origin="Hyderabad",
    destination="Goa",
    start_date="2026-12-10",
    end_date="2026-12-13",
    travelers=2,
    budget=15000,
    interests=["beaches", "local food", "sightseeing"],
)

try:
    graph = create_trip_graph()
    result = graph.invoke({"preferences": preferences})

    print("\nRESEARCH:")
    print(result["research"].model_dump_json(indent=2))

    print("\nITINERARY:")
    print(result["itinerary"].model_dump_json(indent=2))

    print("\nBUDGET:")
    print(result["budget_analysis"].model_dump_json(indent=2))

except Exception:
    traceback.print_exc()
