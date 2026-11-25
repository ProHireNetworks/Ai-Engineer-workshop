# TripMate AI – Multi-Agent Travel Planning Assistant
## Comprehensive Agent Swarm Evaluation Report

**Evaluation Date:** 2026-11-20 18:20:43 UTC
**Total Benchmark Test Cases:** 105
**Pass Rate:** 100.0% (105/105 passed)

### Executive Summary Performance Metrics

| Metric | Result | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Pass Rate** | 100.0% | >= 90.0% | PASS |
| **Avg Plan Completeness** | 100.0% | >= 85.0% | PASS |
| **Avg Budget Accuracy** | 100.0% | >= 85.0% | PASS |
| **Avg Turn Latency** | 9.3 ms | < 500 ms (Mock/Local) | PASS |
| **p95 Turn Latency** | 10.5 ms | < 1000 ms (Mock/Local) | PASS |
| **Total Tokens Consumed** | 105,882 | N/A | OK |
| **Total Est. LLM Cost** | $0.0318 USD | N/A | OK |

### Category Breakdown

| Case ID | Name | Category | Status | Completeness | Budget Acc | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tc_001_domestic_heritage` | Domestic Heritage - Jaipur, India | domestic_heritage | **PASSED** | 100% | 100% | 14.4 |
| `tc_002_domestic_heritage` | Domestic Heritage - Udaipur, India | domestic_heritage | **PASSED** | 100% | 100% | 11.2 |
| `tc_003_domestic_heritage` | Domestic Heritage - Agra, India | domestic_heritage | **PASSED** | 100% | 100% | 8.3 |
| `tc_004_domestic_heritage` | Domestic Heritage - Varanasi, India | domestic_heritage | **PASSED** | 100% | 100% | 9.4 |
| `tc_005_domestic_heritage` | Domestic Heritage - Hampi, India | domestic_heritage | **PASSED** | 100% | 100% | 9.7 |
| `tc_006_domestic_heritage` | Domestic Heritage - Mysore, India | domestic_heritage | **PASSED** | 100% | 100% | 8.8 |
| `tc_007_domestic_heritage` | Domestic Heritage - Khajuraho, India | domestic_heritage | **PASSED** | 100% | 100% | 9.0 |
| `tc_008_domestic_heritage` | Domestic Heritage - Amritsar, India | domestic_heritage | **PASSED** | 100% | 100% | 9.2 |
| `tc_009_domestic_heritage` | Domestic Heritage - Jodhpur, India | domestic_heritage | **PASSED** | 100% | 100% | 9.2 |
| `tc_010_domestic_heritage` | Domestic Heritage - Jaisalmer, India | domestic_heritage | **PASSED** | 100% | 100% | 11.3 |
| `tc_011_domestic_heritage` | Domestic Heritage - Madurai, India | domestic_heritage | **PASSED** | 100% | 100% | 9.8 |
| `tc_012_domestic_heritage` | Domestic Heritage - Tanjore, India | domestic_heritage | **PASSED** | 100% | 100% | 8.9 |
| `tc_013_domestic_heritage` | Domestic Heritage - Bhubaneswar, India | domestic_heritage | **PASSED** | 100% | 100% | 35.3 |
| `tc_014_domestic_heritage` | Domestic Heritage - Puri, India | domestic_heritage | **PASSED** | 100% | 100% | 8.5 |
| `tc_015_domestic_heritage` | Domestic Heritage - Lucknow, India | domestic_heritage | **PASSED** | 100% | 100% | 8.9 |
| `tc_016_domestic_coastal` | Domestic Coastal - Goa, India | domestic_coastal | **PASSED** | 100% | 100% | 8.5 |
| `tc_017_domestic_coastal` | Domestic Coastal - South Goa, India | domestic_coastal | **PASSED** | 100% | 100% | 9.1 |
| `tc_018_domestic_coastal` | Domestic Coastal - Alleppey, India | domestic_coastal | **PASSED** | 100% | 100% | 8.5 |
| `tc_019_domestic_coastal` | Domestic Coastal - Kovalam, India | domestic_coastal | **PASSED** | 100% | 100% | 9.0 |
| `tc_020_domestic_coastal` | Domestic Coastal - Pondicherry, India | domestic_coastal | **PASSED** | 100% | 100% | 8.7 |
| `tc_021_domestic_coastal` | Domestic Coastal - Gokarna, India | domestic_coastal | **PASSED** | 100% | 100% | 9.5 |
| `tc_022_domestic_coastal` | Domestic Coastal - Varkala, India | domestic_coastal | **PASSED** | 100% | 100% | 9.8 |
| `tc_023_domestic_coastal` | Domestic Coastal - Andaman, India | domestic_coastal | **PASSED** | 100% | 100% | 9.7 |
| `tc_024_domestic_coastal` | Domestic Coastal - Diu, India | domestic_coastal | **PASSED** | 100% | 100% | 9.0 |
| `tc_025_domestic_coastal` | Domestic Coastal - Mangalore, India | domestic_coastal | **PASSED** | 100% | 100% | 9.0 |
| `tc_026_domestic_coastal` | Domestic Coastal - Kochi, India | domestic_coastal | **PASSED** | 100% | 100% | 9.1 |
| `tc_027_domestic_coastal` | Domestic Coastal - Alibaug, India | domestic_coastal | **PASSED** | 100% | 100% | 8.7 |
| `tc_028_domestic_mountain` | Domestic Mountain - Manali, India | domestic_mountain | **PASSED** | 100% | 100% | 9.0 |
| `tc_029_domestic_mountain` | Domestic Mountain - Shimla, India | domestic_mountain | **PASSED** | 100% | 100% | 8.8 |
| `tc_030_domestic_mountain` | Domestic Mountain - Munnar, India | domestic_mountain | **PASSED** | 100% | 100% | 9.0 |
| `tc_031_domestic_mountain` | Domestic Mountain - Ooty, India | domestic_mountain | **PASSED** | 100% | 100% | 8.3 |
| `tc_032_domestic_mountain` | Domestic Mountain - Darjeeling, India | domestic_mountain | **PASSED** | 100% | 100% | 9.5 |
| `tc_033_domestic_mountain` | Domestic Mountain - Gangtok, India | domestic_mountain | **PASSED** | 100% | 100% | 9.2 |
| `tc_034_domestic_mountain` | Domestic Mountain - Leh Ladakh, India | domestic_mountain | **PASSED** | 100% | 100% | 10.5 |
| `tc_035_domestic_mountain` | Domestic Mountain - Rishikesh, India | domestic_mountain | **PASSED** | 100% | 100% | 10.1 |
| `tc_036_domestic_mountain` | Domestic Mountain - Kodaikanal, India | domestic_mountain | **PASSED** | 100% | 100% | 8.8 |
| `tc_037_domestic_mountain` | Domestic Mountain - Coorg, India | domestic_mountain | **PASSED** | 100% | 100% | 9.3 |
| `tc_038_domestic_mountain` | Domestic Mountain - Wayanad, India | domestic_mountain | **PASSED** | 100% | 100% | 8.5 |
| `tc_039_domestic_mountain` | Domestic Mountain - Nainital, India | domestic_mountain | **PASSED** | 100% | 100% | 10.1 |
| `tc_040_domestic_mountain` | Domestic Mountain - Mussoorie, India | domestic_mountain | **PASSED** | 100% | 100% | 8.9 |
| `tc_041_domestic_mountain` | Domestic Mountain - Shillong, India | domestic_mountain | **PASSED** | 100% | 100% | 9.1 |
| `tc_042_domestic_mountain` | Domestic Mountain - Kasol, India | domestic_mountain | **PASSED** | 100% | 100% | 9.3 |
| `tc_043_international_city` | International City - Paris, France | international_city | **PASSED** | 100% | 100% | 8.6 |
| `tc_044_international_city` | International City - Rome, Italy | international_city | **PASSED** | 100% | 100% | 9.1 |
| `tc_045_international_city` | International City - London, UK | international_city | **PASSED** | 100% | 100% | 9.5 |
| `tc_046_international_city` | International City - Tokyo, Japan | international_city | **PASSED** | 100% | 100% | 9.2 |
| `tc_047_international_city` | International City - Kyoto, Japan | international_city | **PASSED** | 100% | 100% | 8.7 |
| `tc_048_international_city` | International City - New York, USA | international_city | **PASSED** | 100% | 100% | 10.3 |
| `tc_049_international_city` | International City - Dubai, UAE | international_city | **PASSED** | 100% | 100% | 9.1 |
| `tc_050_international_city` | International City - Singapore | international_city | **PASSED** | 100% | 100% | 9.1 |
| `tc_051_international_city` | International City - Bangkok, Thailand | international_city | **PASSED** | 100% | 100% | 9.3 |
| `tc_052_international_city` | International City - Barcelona, Spain | international_city | **PASSED** | 100% | 100% | 9.1 |
| `tc_053_international_city` | International City - Amsterdam, Netherlands | international_city | **PASSED** | 100% | 100% | 9.1 |
| `tc_054_international_city` | International City - Vienna, Austria | international_city | **PASSED** | 100% | 100% | 9.3 |
| `tc_055_international_city` | International City - Prague, Czech Republic | international_city | **PASSED** | 100% | 100% | 9.8 |
| `tc_056_international_city` | International City - Berlin, Germany | international_city | **PASSED** | 100% | 100% | 8.7 |
| `tc_057_international_city` | International City - Istanbul, Turkey | international_city | **PASSED** | 100% | 100% | 9.4 |
| `tc_058_international_city` | International City - Cairo, Egypt | international_city | **PASSED** | 100% | 100% | 8.9 |
| `tc_059_international_city` | International City - Sydney, Australia | international_city | **PASSED** | 100% | 100% | 9.5 |
| `tc_060_international_city` | International City - Seoul, South Korea | international_city | **PASSED** | 100% | 100% | 9.6 |
| `tc_061_international_city` | International City - Hong Kong | international_city | **PASSED** | 100% | 100% | 9.4 |
| `tc_062_international_city` | International City - Athens, Greece | international_city | **PASSED** | 100% | 100% | 10.0 |
| `tc_063_international_resort` | International Resort - Bali, Indonesia | international_resort | **PASSED** | 100% | 100% | 9.3 |
| `tc_064_international_resort` | International Resort - Phuket, Thailand | international_resort | **PASSED** | 100% | 100% | 10.0 |
| `tc_065_international_resort` | International Resort - Maldives | international_resort | **PASSED** | 100% | 100% | 9.7 |
| `tc_066_international_resort` | International Resort - Santorini, Greece | international_resort | **PASSED** | 100% | 100% | 9.6 |
| `tc_067_international_resort` | International Resort - Mauritius | international_resort | **PASSED** | 100% | 100% | 9.5 |
| `tc_068_international_resort` | International Resort - Seychelles | international_resort | **PASSED** | 100% | 100% | 8.8 |
| `tc_069_international_resort` | International Resort - Zanzibar, Tanzania | international_resort | **PASSED** | 100% | 100% | 9.2 |
| `tc_070_international_resort` | International Resort - Fiji | international_resort | **PASSED** | 100% | 100% | 9.1 |
| `tc_071_international_resort` | International Resort - Bora Bora, French Polynesia | international_resort | **PASSED** | 100% | 100% | 8.9 |
| `tc_072_international_resort` | International Resort - Hawaii, USA | international_resort | **PASSED** | 100% | 100% | 8.4 |
| `tc_073_family_group` | Family Group - Singapore | family_group | **PASSED** | 100% | 100% | 9.5 |
| `tc_074_family_group` | Family Group - Orlando, USA | family_group | **PASSED** | 100% | 100% | 9.0 |
| `tc_075_family_group` | Family Group - Jaipur, India | family_group | **PASSED** | 100% | 100% | 8.9 |
| `tc_076_family_group` | Family Group - Goa, India | family_group | **PASSED** | 100% | 100% | 8.8 |
| `tc_077_family_group` | Family Group - Tokyo, Japan | family_group | **PASSED** | 100% | 100% | 8.7 |
| `tc_078_family_group` | Family Group - London, UK | family_group | **PASSED** | 100% | 100% | 8.9 |
| `tc_079_family_group` | Family Group - Kerala, India | family_group | **PASSED** | 100% | 100% | 8.7 |
| `tc_080_family_group` | Family Group - Dubai, UAE | family_group | **PASSED** | 100% | 100% | 8.8 |
| `tc_081_family_group` | Family Group - Sydney, Australia | family_group | **PASSED** | 100% | 100% | 8.4 |
| `tc_082_family_group` | Family Group - Paris, France | family_group | **PASSED** | 100% | 100% | 8.8 |
| `tc_083_solo_budget` | Solo Budget - Varanasi, India | solo_budget | **PASSED** | 100% | 100% | 9.5 |
| `tc_084_solo_budget` | Solo Budget - Rishikesh, India | solo_budget | **PASSED** | 100% | 100% | 10.3 |
| `tc_085_solo_budget` | Solo Budget - Pushkar, India | solo_budget | **PASSED** | 100% | 100% | 10.5 |
| `tc_086_solo_budget` | Solo Budget - Kasol, India | solo_budget | **PASSED** | 100% | 100% | 9.9 |
| `tc_087_solo_budget` | Solo Budget - Hampi, India | solo_budget | **PASSED** | 100% | 100% | 9.9 |
| `tc_088_solo_budget` | Solo Budget - Bangkok, Thailand | solo_budget | **PASSED** | 100% | 100% | 8.9 |
| `tc_089_solo_budget` | Solo Budget - Hanoi, Vietnam | solo_budget | **PASSED** | 100% | 100% | 9.5 |
| `tc_090_solo_budget` | Solo Budget - Siem Reap, Cambodia | solo_budget | **PASSED** | 100% | 100% | 8.9 |
| `tc_091_solo_budget` | Solo Budget - Kathmandu, Nepal | solo_budget | **PASSED** | 100% | 100% | 9.3 |
| `tc_092_solo_budget` | Solo Budget - Pokhara, Nepal | solo_budget | **PASSED** | 100% | 100% | 9.1 |
| `tc_093_wildlife_nature` | Wildlife Nature - Ranthambore, India | wildlife_nature | **PASSED** | 100% | 100% | 9.6 |
| `tc_094_wildlife_nature` | Wildlife Nature - Kaziranga, India | wildlife_nature | **PASSED** | 100% | 100% | 9.2 |
| `tc_095_wildlife_nature` | Wildlife Nature - Jim Corbett, India | wildlife_nature | **PASSED** | 100% | 100% | 9.1 |
| `tc_096_wildlife_nature` | Wildlife Nature - Serengeti, Tanzania | wildlife_nature | **PASSED** | 100% | 100% | 9.7 |
| `tc_097_international_mountain` | International Mountain - Interlaken, Switzerland | international_mountain | **PASSED** | 100% | 100% | 8.9 |
| `tc_098_edge_case_minimal_days` | Edge Case Minimal Days - Jaipur | edge_case_minimal_days | **PASSED** | 100% | 100% | 9.9 |
| `tc_099_edge_case_long_stay` | Edge Case Long Stay - Goa | edge_case_long_stay | **PASSED** | 100% | 100% | 9.9 |
| `tc_100_edge_case_high_budget_solo` | Edge Case High Budget Solo - Mumbai | edge_case_high_budget_solo | **PASSED** | 100% | 100% | 9.2 |
| `tc_101_edge_case_large_group` | Edge Case Large Group - Delhi | edge_case_large_group | **PASSED** | 100% | 100% | 8.8 |
| `tc_102_edge_case_no_interests` | Edge Case No Interests - Kolkata | edge_case_no_interests | **PASSED** | 100% | 100% | 9.3 |
| `tc_103_edge_case_invalid_days_zero` | Edge Case Invalid Days Zero - Jaipur | edge_case_invalid_days_zero | **PASSED** | 100% | 100% | 0.0 |
| `tc_104_edge_case_unrealistic_low_budget` | Edge Case Unrealistic Low Budget - Goa | edge_case_unrealistic_low_budget | **PASSED** | 100% | 100% | 0.0 |
| `tc_105_edge_case_invalid_currency` | Edge Case Invalid Currency - Kerala | edge_case_invalid_currency | **PASSED** | 100% | 100% | 0.0 |