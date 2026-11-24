"""
TripMate AI - Benchmark Test Case Generator
Generates over 100 realistic, diverse travel benchmark cases covering domestic,
international, budget, luxury, family, solo, and edge-case scenarios.
"""

import json
from pathlib import Path

DESTINATIONS_DATA = [
    # Domestic Heritage & Culture (15)
    ("Jaipur, India", 3, 25000, "INR", 2, ["forts", "palaces", "culture"], "domestic_heritage"),
    ("Udaipur, India", 4, 35000, "INR", 2, ["lakes", "royal architecture", "dining"], "domestic_heritage"),
    ("Agra, India", 2, 18000, "INR", 2, ["Taj Mahal", "monuments", "mughal history"], "domestic_heritage"),
    ("Varanasi, India", 3, 20000, "INR", 1, ["ghats", "spirituality", "silk weaving"], "domestic_heritage"),
    ("Hampi, India", 3, 22000, "INR", 2, ["ruins", "bouldering", "temples"], "domestic_heritage"),
    ("Mysore, India", 3, 24000, "INR", 2, ["palaces", "silk", "gardens"], "domestic_heritage"),
    ("Khajuraho, India", 2, 16000, "INR", 2, ["temple art", "sculptures", "heritage"], "domestic_heritage"),
    ("Amritsar, India", 2, 18000, "INR", 2, ["Golden Temple", "street food", "patriotism"], "domestic_heritage"),
    ("Jodhpur, India", 3, 26000, "INR", 2, ["blue city", "Mehrangarh", "handicrafts"], "domestic_heritage"),
    ("Jaisalmer, India", 3, 30000, "INR", 2, ["desert safari", "dunes", "fort"], "domestic_heritage"),
    ("Madurai, India", 2, 15000, "INR", 2, ["Meenakshi temple", "tamil culture", "food"], "domestic_heritage"),
    ("Tanjore, India", 2, 16000, "INR", 1, ["Brihadisvara", "chola bronzes", "heritage"], "domestic_heritage"),
    ("Bhubaneswar, India", 3, 20000, "INR", 2, ["temples", "caves", "odissi art"], "domestic_heritage"),
    ("Puri, India", 3, 22000, "INR", 3, ["Jagannath temple", "beaches", "artisans"], "domestic_heritage"),
    ("Lucknow, India", 2, 18000, "INR", 2, ["awadhi cuisine", "imambara", "chikan embroidery"], "domestic_heritage"),

    # Domestic Beach & Coastal (12)
    ("Goa, India", 4, 32000, "INR", 2, ["beaches", "shacks", "water sports"], "domestic_coastal"),
    ("South Goa, India", 4, 40000, "INR", 2, ["quiet beaches", "luxury resorts", "nature"], "domestic_coastal"),
    ("Alleppey, India", 3, 30000, "INR", 2, ["houseboats", "backwaters", "seafood"], "domestic_coastal"),
    ("Kovalam, India", 3, 25000, "INR", 2, ["lighthouse beach", "ayurveda", "seafood"], "domestic_coastal"),
    ("Pondicherry, India", 3, 24000, "INR", 2, ["french colony", "promenade", "cafes"], "domestic_coastal"),
    ("Gokarna, India", 3, 18000, "INR", 1, ["trekking", "om beach", "tranquility"], "domestic_coastal"),
    ("Varkala, India", 3, 20000, "INR", 2, ["cliff views", "surfing", "sunset"], "domestic_coastal"),
    ("Andaman, India", 5, 60000, "INR", 2, ["scuba diving", "radhanagar beach", "cellular jail"], "domestic_coastal"),
    ("Diu, India", 2, 15000, "INR", 2, ["portuguese fort", "beaches", "relaxation"], "domestic_coastal"),
    ("Mangalore, India", 2, 16000, "INR", 2, ["coastal cuisine", "panambur beach", "temples"], "domestic_coastal"),
    ("Kochi, India", 3, 26000, "INR", 2, ["chinese nets", "jew town", "kathakali"], "domestic_coastal"),
    ("Alibaug, India", 2, 18000, "INR", 2, ["coastal fort", "weekend getaway", "water sports"], "domestic_coastal"),

    # Domestic Hill & Adventure (15)
    ("Manali, India", 4, 30000, "INR", 2, ["snow", "solang valley", "hiking"], "domestic_mountain"),
    ("Shimla, India", 3, 25000, "INR", 2, ["toy train", "mall road", "colonial vistas"], "domestic_mountain"),
    ("Munnar, India", 3, 28000, "INR", 2, ["tea estates", "eravikulam", "mist"], "domestic_mountain"),
    ("Ooty, India", 3, 26000, "INR", 2, ["botanical gardens", "nilgiri train", "lakes"], "domestic_mountain"),
    ("Darjeeling, India", 3, 28000, "INR", 2, ["tiger hill", "tea gardens", "kanchendzonga"], "domestic_mountain"),
    ("Gangtok, India", 4, 38000, "INR", 2, ["monasteries", "tsomgo lake", "himalayas"], "domestic_mountain"),
    ("Leh Ladakh, India", 6, 65000, "INR", 2, ["pangong lake", "passes", "monasteries"], "domestic_mountain"),
    ("Rishikesh, India", 3, 18000, "INR", 2, ["river rafting", "yoga", "ganga aarti"], "domestic_mountain"),
    ("Kodaikanal, India", 3, 24000, "INR", 2, ["pillar rocks", "lake", "homemade chocolate"], "domestic_mountain"),
    ("Coorg, India", 3, 26000, "INR", 2, ["coffee plantations", "waterfalls", "abbey falls"], "domestic_mountain"),
    ("Wayanad, India", 3, 25000, "INR", 2, ["caves", "wildlife", "tree houses"], "domestic_mountain"),
    ("Nainital, India", 3, 22000, "INR", 2, ["naini lake", "boating", "viewpoints"], "domestic_mountain"),
    ("Mussoorie, India", 3, 24000, "INR", 2, ["kempty falls", "gun hill", "views"], "domestic_mountain"),
    ("Shillong, India", 4, 36000, "INR", 2, ["living root bridges", "waterfalls", "rock music"], "domestic_mountain"),
    ("Kasol, India", 3, 16000, "INR", 1, ["parvati valley", "trekking", "cafes"], "domestic_mountain"),

    # International Cities & Culture (20)
    ("Paris, France", 5, 2500, "EUR", 2, ["Eiffel Tower", "Louvre", "cafes", "art"], "international_city"),
    ("Rome, Italy", 4, 2000, "EUR", 2, ["Colosseum", "Vatican", "pasta", "history"], "international_city"),
    ("London, UK", 5, 2600, "GBP", 2, ["museums", "theatre", "Big Ben", "palaces"], "international_city"),
    ("Tokyo, Japan", 6, 3200, "USD", 2, ["temples", "sushi", "Shibuya", "anime"], "international_city"),
    ("Kyoto, Japan", 4, 2200, "USD", 2, ["Fushimi Inari", "bamboo grove", "zen gardens"], "international_city"),
    ("New York, USA", 5, 3500, "USD", 2, ["Broadway", "Central Park", "Metropolitan Museum"], "international_city"),
    ("Dubai, UAE", 4, 2400, "USD", 2, ["Burj Khalifa", "desert safari", "shopping"], "international_city"),
    ("Singapore", 4, 2200, "USD", 2, ["Gardens by the Bay", "Marina Bay", "street food"], "international_city"),
    ("Bangkok, Thailand", 4, 1500, "USD", 2, ["Grand Palace", "floating markets", "street food"], "international_city"),
    ("Barcelona, Spain", 4, 2100, "EUR", 2, ["Sagrada Familia", "tapas", "beaches"], "international_city"),
    ("Amsterdam, Netherlands", 4, 2200, "EUR", 2, ["canals", "Rijksmuseum", "bicycles"], "international_city"),
    ("Vienna, Austria", 3, 1600, "EUR", 2, ["classical music", "palaces", "coffee houses"], "international_city"),
    ("Prague, Czech Republic", 3, 1400, "EUR", 2, ["Charles Bridge", "Old Town", "castles"], "international_city"),
    ("Berlin, Germany", 4, 1800, "EUR", 2, ["history", "techno", "museum island"], "international_city"),
    ("Istanbul, Turkey", 4, 1600, "USD", 2, ["Hagia Sophia", "bazaars", "Bosphorus cruise"], "international_city"),
    ("Cairo, Egypt", 4, 1500, "USD", 2, ["Pyramids of Giza", "Nile cruise", "antiquities"], "international_city"),
    ("Sydney, Australia", 5, 3000, "USD", 2, ["Opera House", "Bondi Beach", "harbour cruise"], "international_city"),
    ("Seoul, South Korea", 5, 2400, "USD", 2, ["palaces", "k-pop", "korean bbq", "night markets"], "international_city"),
    ("Hong Kong", 4, 2300, "USD", 2, ["Victoria Peak", "dim sum", "harbour skyline"], "international_city"),
    ("Athens, Greece", 3, 1500, "EUR", 2, ["Acropolis", "ancient history", "greek food"], "international_city"),

    # International Tropical & Resorts (10)
    ("Bali, Indonesia", 5, 1800, "USD", 2, ["Ubud rice terraces", "surfing", "temples"], "international_resort"),
    ("Phuket, Thailand", 4, 1400, "USD", 2, ["Phi Phi islands", "beaches", "snorkeling"], "international_resort"),
    ("Maldives", 4, 4500, "USD", 2, ["overwater villas", "coral reefs", "luxury"], "international_resort"),
    ("Santorini, Greece", 4, 2800, "EUR", 2, ["caldera views", "whitewashed houses", "sunsets"], "international_resort"),
    ("Mauritius", 5, 3200, "USD", 2, ["lagoon beaches", "hiking", "botanical gardens"], "international_resort"),
    ("Seychelles", 5, 4200, "USD", 2, ["granite boulders", "beaches", "giant tortoises"], "international_resort"),
    ("Zanzibar, Tanzania", 4, 2000, "USD", 2, ["Stone Town", "spice tours", "white sands"], "international_resort"),
    ("Fiji", 6, 4000, "USD", 2, ["islands", "snorkeling", "pacific culture"], "international_resort"),
    ("Bora Bora, French Polynesia", 5, 7500, "USD", 2, ["luxury overwater", "lagoon", "diving"], "international_resort"),
    ("Hawaii, USA", 6, 4500, "USD", 2, ["volcanoes", "surfing", "waikiki", "luaus"], "international_resort"),

    # Family & Group Trips (10)
    ("Singapore", 5, 3500, "USD", 4, ["Universal Studios", "Zoo", "Night Safari"], "family_group"),
    ("Orlando, USA", 6, 5000, "USD", 4, ["Disney World", "Universal", "space center"], "family_group"),
    ("Jaipur, India", 4, 45000, "INR", 4, ["elephant sanctuary", "family dining", "forts"], "family_group"),
    ("Goa, India", 5, 55000, "INR", 5, ["family villa", "dudhsagar falls", "dolphin trips"], "family_group"),
    ("Tokyo, Japan", 6, 5200, "USD", 4, ["Disneyland", "Ghibli museum", "robot show"], "family_group"),
    ("London, UK", 5, 4200, "GBP", 4, ["Harry Potter studio", "science museum", "parks"], "family_group"),
    ("Kerala, India", 5, 60000, "INR", 4, ["backwaters", "spice gardens", "elephant training"], "family_group"),
    ("Dubai, UAE", 4, 3800, "USD", 4, ["aquarium", "theme parks", "miracle garden"], "family_group"),
    ("Sydney, Australia", 6, 5500, "USD", 4, ["taronga zoo", "aquarium", "manly beach"], "family_group"),
    ("Paris, France", 5, 4200, "EUR", 4, ["Disneyland Paris", "river cruise", "eiffel"], "family_group"),

    # Solo Backpacker & Budget Exploration (10)
    ("Varanasi, India", 3, 8000, "INR", 1, ["hostels", "walking tours", "spirituality"], "solo_budget"),
    ("Rishikesh, India", 4, 9000, "INR", 1, ["yoga retreats", "hiking", "hostel life"], "solo_budget"),
    ("Pushkar, India", 2, 6000, "INR", 1, ["camel fair", "sacred lake", "rooftop cafes"], "solo_budget"),
    ("Kasol, India", 4, 8500, "INR", 1, ["kheerganga trek", "budget cafes", "nature"], "solo_budget"),
    ("Hampi, India", 3, 7500, "INR", 1, ["bicycles", "guesthouses", "boulders"], "solo_budget"),
    ("Bangkok, Thailand", 4, 600, "USD", 1, ["khao san road", "hostels", "street food"], "solo_budget"),
    ("Hanoi, Vietnam", 5, 550, "USD", 1, ["old quarter", "halong bay", "egg coffee"], "solo_budget"),
    ("Siem Reap, Cambodia", 3, 450, "USD", 1, ["Angkor Wat", "tuk tuks", "budget stays"], "solo_budget"),
    ("Kathmandu, Nepal", 4, 500, "USD", 1, ["Thamel", "boudhanath", "hiking"], "solo_budget"),
    ("Pokhara, Nepal", 4, 500, "USD", 1, ["Phewa lake", "annapurna views", "peace pagoda"], "solo_budget"),

    # Wildlife & Nature Sanctuaries (5)
    ("Ranthambore, India", 3, 28000, "INR", 2, ["tiger safari", "fort", "wildlife"], "wildlife_nature"),
    ("Kaziranga, India", 3, 30000, "INR", 2, ["one-horned rhino", "jeep safari", "tea"], "wildlife_nature"),
    ("Jim Corbett, India", 3, 24000, "INR", 2, ["jungle safari", "dhikala", "bird watching"], "wildlife_nature"),
    ("Serengeti, Tanzania", 5, 3800, "USD", 2, ["great migration", "game drives", "safari"], "wildlife_nature"),
    ("Interlaken, Switzerland", 4, 2800, "EUR", 2, ["jungfraujoch", "alpine trains", "lakes"], "international_mountain"),

    # Edge Cases & Validation Tests (8)
    ("Jaipur", 1, 10000, "INR", 1, ["express tour"], "edge_case_minimal_days"),
    ("Goa", 14, 120000, "INR", 2, ["workation", "relaxation"], "edge_case_long_stay"),
    ("Mumbai", 3, 50000, "INR", 1, ["business travel", "heritage"], "edge_case_high_budget_solo"),
    ("Delhi", 2, 12000, "INR", 10, ["group tour"], "edge_case_large_group"),
    ("Kolkata", 3, 20000, "INR", 2, [], "edge_case_no_interests"),
    ("Jaipur", 0, 10000, "INR", 2, ["tour"], "edge_case_invalid_days_zero"),
    ("Goa", 3, 0.5, "INR", 2, ["beach"], "edge_case_unrealistic_low_budget"),
    ("Kerala", 3, 25000, "INVALID_CURR", 2, ["nature"], "edge_case_invalid_currency"),
]

def generate_benchmark_suite() -> None:
    cases = []
    for idx, item in enumerate(DESTINATIONS_DATA, start=1):
        dest, days, budget, currency, travelers, interests, category = item
        case_id = f"tc_{idx:03d}_{category}"
        expected_status = "validation_error" if ("invalid" in category or "unrealistic" in category) else "success"

        case = {
            "id": case_id,
            "name": f"{category.replace('_', ' ').title()} - {dest}",
            "category": category,
            "request": {
                "destination": dest,
                "days": days,
                "budget": budget,
                "currency": currency,
                "travelers": travelers,
                "interests": interests,
            },
            "expected_status": expected_status,
            "min_attractions": 3 if expected_status == "success" else 0,
            "max_budget_variance_pct": 20.0,
        }
        cases.append(case)

    out_path = Path("benchmark/travel_test_cases.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)

    print(f"Generated {len(cases)} benchmark test cases into {out_path}")

if __name__ == "__main__":
    generate_benchmark_suite()
