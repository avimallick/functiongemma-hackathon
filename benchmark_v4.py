import sys, os
sys.path.insert(0, "cactus/python/src")
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"

import json
from main import generate_hybrid


############## Tool definitions ##############

TOOL_TRANSLATE_TEXT = {
    "name": "translate_text",
    "description": "Translate text into a target language",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to translate"},
            "target_language": {"type": "string", "description": "The language to translate into (e.g. French, Spanish)"},
        },
        "required": ["text", "target_language"],
    },
}

TOOL_ADD_CALENDAR_EVENT = {
    "name": "add_calendar_event",
    "description": "Add an event to the user's calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the event"},
            "date": {"type": "string", "description": "Date of the event (e.g. Monday, tomorrow, 2024-06-15)"},
            "time": {"type": "string", "description": "Time of the event (e.g. 2:00 PM)"},
        },
        "required": ["title", "date", "time"],
    },
}

TOOL_WEB_SEARCH = {
    "name": "web_search",
    "description": "Search the web for information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
        },
        "required": ["query"],
    },
}

TOOL_GET_DIRECTIONS = {
    "name": "get_directions",
    "description": "Get directions from one place to another",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Starting location"},
            "destination": {"type": "string", "description": "Destination location"},
        },
        "required": ["origin", "destination"],
    },
}

TOOL_SET_VOLUME = {
    "name": "set_volume",
    "description": "Set the device volume level",
    "parameters": {
        "type": "object",
        "properties": {
            "level": {"type": "integer", "description": "Volume level from 0 to 100"},
        },
        "required": ["level"],
    },
}

TOOL_TAKE_NOTE = {
    "name": "take_note",
    "description": "Save a note with a title and body",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the note"},
            "body": {"type": "string", "description": "Content of the note"},
        },
        "required": ["title", "body"],
    },
}

TOOL_CONVERT_UNITS = {
    "name": "convert_units",
    "description": "Convert a value from one unit to another",
    "parameters": {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "The numeric value to convert"},
            "from_unit": {"type": "string", "description": "The unit to convert from"},
            "to_unit": {"type": "string", "description": "The unit to convert to"},
        },
        "required": ["value", "from_unit", "to_unit"],
    },
}


############## Benchmark cases (v4 set — new tools) ##############

BENCHMARKS_V4 = [
    # ===== Easy: 1 tool, direct request =====
    {
        "name": "translate_hello_spanish",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Translate 'hello' into Spanish."}],
        "tools": [TOOL_TRANSLATE_TEXT],
        "expected_calls": [{"name": "translate_text", "arguments": {"text": "hello", "target_language": "Spanish"}}],
    },
    {
        "name": "calendar_dentist_friday",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Add a dentist appointment to my calendar on Friday at 10:00 AM."}],
        "tools": [TOOL_ADD_CALENDAR_EVENT],
        "expected_calls": [{"name": "add_calendar_event", "arguments": {"title": "dentist appointment", "date": "Friday", "time": "10:00 AM"}}],
    },
    {
        "name": "search_best_pizza",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Search for the best pizza places near me."}],
        "tools": [TOOL_WEB_SEARCH],
        "expected_calls": [{"name": "web_search", "arguments": {"query": "best pizza places near me"}}],
    },
    {
        "name": "directions_home_to_airport",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Get me directions from home to the airport."}],
        "tools": [TOOL_GET_DIRECTIONS],
        "expected_calls": [{"name": "get_directions", "arguments": {"origin": "home", "destination": "airport"}}],
    },
    {
        "name": "volume_50",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Set the volume to 50."}],
        "tools": [TOOL_SET_VOLUME],
        "expected_calls": [{"name": "set_volume", "arguments": {"level": 50}}],
    },
    {
        "name": "note_grocery_list",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Take a note titled grocery list with the body eggs, milk, bread."}],
        "tools": [TOOL_TAKE_NOTE],
        "expected_calls": [{"name": "take_note", "arguments": {"title": "grocery list", "body": "eggs, milk, bread"}}],
    },
    {
        "name": "convert_miles_to_km",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Convert 5 miles to kilometers."}],
        "tools": [TOOL_CONVERT_UNITS],
        "expected_calls": [{"name": "convert_units", "arguments": {"value": 5, "from_unit": "miles", "to_unit": "kilometers"}}],
    },
    {
        "name": "translate_goodbye_french",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "How do you say goodbye in French? Translate it for me."}],
        "tools": [TOOL_TRANSLATE_TEXT],
        "expected_calls": [{"name": "translate_text", "arguments": {"text": "goodbye", "target_language": "French"}}],
    },
    {
        "name": "volume_mute",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Mute the device."}],
        "tools": [TOOL_SET_VOLUME],
        "expected_calls": [{"name": "set_volume", "arguments": {"level": 0}}],
    },
    {
        "name": "convert_celsius_to_fahrenheit",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Convert 100 degrees Celsius to Fahrenheit."}],
        "tools": [TOOL_CONVERT_UNITS],
        "expected_calls": [{"name": "convert_units", "arguments": {"value": 100, "from_unit": "Celsius", "to_unit": "Fahrenheit"}}],
    },

    # ===== Medium: 2-4 tools, must pick the right one =====
    {
        "name": "translate_among_three",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Translate 'thank you' into Japanese."}],
        "tools": [TOOL_WEB_SEARCH, TOOL_TRANSLATE_TEXT, TOOL_TAKE_NOTE],
        "expected_calls": [{"name": "translate_text", "arguments": {"text": "thank you", "target_language": "Japanese"}}],
    },
    {
        "name": "directions_among_two",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "How do I get from the train station to the museum?"}],
        "tools": [TOOL_WEB_SEARCH, TOOL_GET_DIRECTIONS],
        "expected_calls": [{"name": "get_directions", "arguments": {"origin": "train station", "destination": "museum"}}],
    },
    {
        "name": "calendar_among_three",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Schedule a team standup on Monday at 9:00 AM."}],
        "tools": [TOOL_TAKE_NOTE, TOOL_ADD_CALENDAR_EVENT, TOOL_WEB_SEARCH],
        "expected_calls": [{"name": "add_calendar_event", "arguments": {"title": "team standup", "date": "Monday", "time": "9:00 AM"}}],
    },
    {
        "name": "volume_among_four",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Turn the volume all the way up."}],
        "tools": [TOOL_ADD_CALENDAR_EVENT, TOOL_WEB_SEARCH, TOOL_CONVERT_UNITS, TOOL_SET_VOLUME],
        "expected_calls": [{"name": "set_volume", "arguments": {"level": 100}}],
    },
    {
        "name": "note_among_three",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Save a note called meeting notes with the content discuss Q3 roadmap."}],
        "tools": [TOOL_ADD_CALENDAR_EVENT, TOOL_TAKE_NOTE, TOOL_GET_DIRECTIONS],
        "expected_calls": [{"name": "take_note", "arguments": {"title": "meeting notes", "body": "discuss Q3 roadmap"}}],
    },
    {
        "name": "search_among_four",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Look up the latest news on electric vehicles."}],
        "tools": [TOOL_TRANSLATE_TEXT, TOOL_SET_VOLUME, TOOL_WEB_SEARCH, TOOL_GET_DIRECTIONS],
        "expected_calls": [{"name": "web_search", "arguments": {"query": "latest news on electric vehicles"}}],
    },
    {
        "name": "convert_among_three",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "How many pounds is 10 kilograms?"}],
        "tools": [TOOL_WEB_SEARCH, TOOL_GET_DIRECTIONS, TOOL_CONVERT_UNITS],
        "expected_calls": [{"name": "convert_units", "arguments": {"value": 10, "from_unit": "kilograms", "to_unit": "pounds"}}],
    },
    {
        "name": "directions_among_four",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Navigate from downtown to the nearest hospital."}],
        "tools": [TOOL_TRANSLATE_TEXT, TOOL_ADD_CALENDAR_EVENT, TOOL_TAKE_NOTE, TOOL_GET_DIRECTIONS],
        "expected_calls": [{"name": "get_directions", "arguments": {"origin": "downtown", "destination": "nearest hospital"}}],
    },
    {
        "name": "translate_among_five",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Say 'good night' in Italian."}],
        "tools": [TOOL_SET_VOLUME, TOOL_GET_DIRECTIONS, TOOL_WEB_SEARCH, TOOL_ADD_CALENDAR_EVENT, TOOL_TRANSLATE_TEXT],
        "expected_calls": [{"name": "translate_text", "arguments": {"text": "good night", "target_language": "Italian"}}],
    },
    {
        "name": "calendar_among_five",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Put a lunch with Sarah on my calendar for tomorrow at 12:30 PM."}],
        "tools": [TOOL_WEB_SEARCH, TOOL_CONVERT_UNITS, TOOL_GET_DIRECTIONS, TOOL_SET_VOLUME, TOOL_ADD_CALENDAR_EVENT],
        "expected_calls": [{"name": "add_calendar_event", "arguments": {"title": "lunch with Sarah", "date": "tomorrow", "time": "12:30 PM"}}],
    },

    # ===== Hard: multiple tools needed, multi-call =====
    {
        "name": "translate_and_note",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Translate 'welcome' into German and save a note called phrases with the body welcome in German."}],
        "tools": [TOOL_TRANSLATE_TEXT, TOOL_TAKE_NOTE, TOOL_WEB_SEARCH, TOOL_ADD_CALENDAR_EVENT],
        "expected_calls": [
            {"name": "translate_text", "arguments": {"text": "welcome", "target_language": "German"}},
            {"name": "take_note", "arguments": {"title": "phrases", "body": "welcome in German"}},
        ],
    },
    {
        "name": "calendar_and_directions",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Add a job interview to my calendar on Wednesday at 2:00 PM and get directions from my office to the interview location."}],
        "tools": [TOOL_ADD_CALENDAR_EVENT, TOOL_GET_DIRECTIONS, TOOL_WEB_SEARCH, TOOL_TAKE_NOTE],
        "expected_calls": [
            {"name": "add_calendar_event", "arguments": {"title": "job interview", "date": "Wednesday", "time": "2:00 PM"}},
            {"name": "get_directions", "arguments": {"origin": "my office", "destination": "interview location"}},
        ],
    },
    {
        "name": "search_and_volume",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Search for relaxing music playlists and set the volume to 30."}],
        "tools": [TOOL_WEB_SEARCH, TOOL_SET_VOLUME, TOOL_TRANSLATE_TEXT, TOOL_GET_DIRECTIONS],
        "expected_calls": [
            {"name": "web_search", "arguments": {"query": "relaxing music playlists"}},
            {"name": "set_volume", "arguments": {"level": 30}},
        ],
    },
    {
        "name": "convert_and_note",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Convert 72 Fahrenheit to Celsius and save a note called temperature with the result."}],
        "tools": [TOOL_CONVERT_UNITS, TOOL_TAKE_NOTE, TOOL_WEB_SEARCH, TOOL_SET_VOLUME],
        "expected_calls": [
            {"name": "convert_units", "arguments": {"value": 72, "from_unit": "Fahrenheit", "to_unit": "Celsius"}},
            {"name": "take_note", "arguments": {"title": "temperature", "body": "72 Fahrenheit to Celsius"}},
        ],
    },
    {
        "name": "directions_and_calendar",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Get directions from home to the stadium and add game night to my calendar on Saturday at 7:00 PM."}],
        "tools": [TOOL_GET_DIRECTIONS, TOOL_ADD_CALENDAR_EVENT, TOOL_SET_VOLUME, TOOL_TRANSLATE_TEXT],
        "expected_calls": [
            {"name": "get_directions", "arguments": {"origin": "home", "destination": "stadium"}},
            {"name": "add_calendar_event", "arguments": {"title": "game night", "date": "Saturday", "time": "7:00 PM"}},
        ],
    },
    {
        "name": "search_and_translate",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Search for top tourist spots in Rome and translate 'where is the Colosseum' into Italian."}],
        "tools": [TOOL_WEB_SEARCH, TOOL_TRANSLATE_TEXT, TOOL_TAKE_NOTE, TOOL_GET_DIRECTIONS],
        "expected_calls": [
            {"name": "web_search", "arguments": {"query": "top tourist spots in Rome"}},
            {"name": "translate_text", "arguments": {"text": "where is the Colosseum", "target_language": "Italian"}},
        ],
    },
    {
        "name": "note_search_volume",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Save a note called recipe ideas with the body sourdough bread, set the volume to 20, and search for sourdough bread recipes."}],
        "tools": [TOOL_TAKE_NOTE, TOOL_SET_VOLUME, TOOL_WEB_SEARCH, TOOL_ADD_CALENDAR_EVENT, TOOL_TRANSLATE_TEXT],
        "expected_calls": [
            {"name": "take_note", "arguments": {"title": "recipe ideas", "body": "sourdough bread"}},
            {"name": "set_volume", "arguments": {"level": 20}},
            {"name": "web_search", "arguments": {"query": "sourdough bread recipes"}},
        ],
    },
    {
        "name": "calendar_translate_directions",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Add a flight to Paris to my calendar on Thursday at 6:00 AM, translate 'my flight is on time' into French, and get directions from my house to the airport."}],
        "tools": [TOOL_ADD_CALENDAR_EVENT, TOOL_TRANSLATE_TEXT, TOOL_GET_DIRECTIONS, TOOL_WEB_SEARCH, TOOL_SET_VOLUME],
        "expected_calls": [
            {"name": "add_calendar_event", "arguments": {"title": "flight to Paris", "date": "Thursday", "time": "6:00 AM"}},
            {"name": "translate_text", "arguments": {"text": "my flight is on time", "target_language": "French"}},
            {"name": "get_directions", "arguments": {"origin": "my house", "destination": "airport"}},
        ],
    },
    {
        "name": "convert_search_calendar",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Convert 26.2 miles to kilometers, search for marathon training plans, and add a long run to my calendar on Sunday at 7:00 AM."}],
        "tools": [TOOL_CONVERT_UNITS, TOOL_WEB_SEARCH, TOOL_ADD_CALENDAR_EVENT, TOOL_TAKE_NOTE, TOOL_GET_DIRECTIONS],
        "expected_calls": [
            {"name": "convert_units", "arguments": {"value": 26.2, "from_unit": "miles", "to_unit": "kilometers"}},
            {"name": "web_search", "arguments": {"query": "marathon training plans"}},
            {"name": "add_calendar_event", "arguments": {"title": "long run", "date": "Sunday", "time": "7:00 AM"}},
        ],
    },
    {
        "name": "translate_note_search",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Translate 'do you speak English' into Mandarin, save a note called travel phrases with that phrase, and search for Mandarin pronunciation guides."}],
        "tools": [TOOL_TRANSLATE_TEXT, TOOL_TAKE_NOTE, TOOL_WEB_SEARCH, TOOL_SET_VOLUME, TOOL_GET_DIRECTIONS],
        "expected_calls": [
            {"name": "translate_text", "arguments": {"text": "do you speak English", "target_language": "Mandarin"}},
            {"name": "take_note", "arguments": {"title": "travel phrases", "body": "do you speak English in Mandarin"}},
            {"name": "web_search", "arguments": {"query": "Mandarin pronunciation guides"}},
        ],
    },
]


def _normalize(v):
    """Normalize a value for comparison."""
    if isinstance(v, str):
        return v.strip().lower()
    return v


def _call_matches(predicted, expected):
    """Check if a predicted call matches an expected call (name + argument values)."""
    if predicted["name"] != expected["name"]:
        return False
    pred_args = predicted.get("arguments", {})
    exp_args = expected.get("arguments", {})
    for key, exp_val in exp_args.items():
        if key not in pred_args:
            return False
        if _normalize(pred_args[key]) != _normalize(exp_val):
            return False
    return True


def compute_f1(predicted_calls, expected_calls):
    """Compute F1 score between predicted and expected function calls."""
    if not predicted_calls and not expected_calls:
        return 1.0
    if not predicted_calls or not expected_calls:
        return 0.0

    matched = 0
    used = set()
    for exp in expected_calls:
        for i, pred in enumerate(predicted_calls):
            if i not in used and _call_matches(pred, exp):
                matched += 1
                used.add(i)
                break

    precision = matched / len(predicted_calls)
    recall = matched / len(expected_calls)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def run_benchmark(benchmarks=None):
    """Run all benchmark cases and print results."""
    if benchmarks is None:
        benchmarks = BENCHMARKS_V4

    total = len(benchmarks)
    results = []
    for i, case in enumerate(benchmarks, 1):
        print(f"[{i}/{total}] Running: {case['name']} ({case['difficulty']})...", end=" ", flush=True)
        result = generate_hybrid(case["messages"], case["tools"])
        f1 = compute_f1(result["function_calls"], case["expected_calls"])
        source = result.get("source", "unknown")
        print(f"F1={f1:.2f} | {result['total_time_ms']:.0f}ms | {source}")
        results.append({
            "name": case["name"],
            "difficulty": case["difficulty"],
            "total_time_ms": result["total_time_ms"],
            "f1": f1,
            "source": source,
            "predicted": result["function_calls"],
            "expected": case["expected_calls"],
        })

    print("\n=== Benchmark Results (v4 set) ===\n")
    print(f"  {'#':>2} | {'Difficulty':<10} | {'Name':<34} | {'Time (ms)':>10} | {'F1':>5} | Source")
    print(f"  {'--':>2}-+-{'-'*10}-+-{'-'*34}-+-{'-'*10}-+-{'-'*5}-+-{'-'*20}")
    for i, r in enumerate(results, 1):
        print(f"  {i:>2} | {r['difficulty']:<10} | {r['name']:<34} | {r['total_time_ms']:>10.2f} | {r['f1']:>5.2f} | {r['source']}")

    print(f"\n--- Summary ---")
    for difficulty in ["easy", "medium", "hard"]:
        group = [r for r in results if r["difficulty"] == difficulty]
        if not group:
            continue
        avg_f1 = sum(r["f1"] for r in group) / len(group)
        avg_time = sum(r["total_time_ms"] for r in group) / len(group)
        on_device = sum(1 for r in group if r["source"] == "on-device")
        cloud = len(group) - on_device
        print(f"  {difficulty:<8} avg F1={avg_f1:.2f}  avg time={avg_time:.2f}ms  on-device={on_device}/{len(group)} cloud={cloud}/{len(group)}")

    avg_f1 = sum(r["f1"] for r in results) / len(results)
    avg_time = sum(r["total_time_ms"] for r in results) / len(results)
    total_time = sum(r["total_time_ms"] for r in results)
    on_device_total = sum(1 for r in results if r["source"] == "on-device")
    cloud_total = len(results) - on_device_total
    print(f"  {'overall':<8} avg F1={avg_f1:.2f}  avg time={avg_time:.2f}ms  total time={total_time:.2f}ms")
    print(f"           on-device={on_device_total}/{len(results)} ({100*on_device_total/len(results):.0f}%)  cloud={cloud_total}/{len(results)} ({100*cloud_total/len(results):.0f}%)")

    score = compute_total_score(results)
    print(f"\n{'='*50}")
    print(f"  TOTAL SCORE: {score:.1f}%")
    print(f"{'='*50}")

    return results


def compute_total_score(results):
    """
    Compute a total score from 0-100% as a weighted sum across difficulty levels.

    Components (per difficulty level):
      - F1 score (60%): accuracy of tool calls
      - Time score (15%): faster is better, capped at 500ms baseline
      - On-device ratio (25%): higher on-device usage is better

    Difficulty weights:
      - easy: 20%
      - medium: 30%
      - hard: 50%
    """
    difficulty_weights = {"easy": 0.20, "medium": 0.30, "hard": 0.50}
    time_baseline_ms = 500

    total_score = 0
    for difficulty, weight in difficulty_weights.items():
        group = [r for r in results if r["difficulty"] == difficulty]
        if not group:
            continue

        avg_f1 = sum(r["f1"] for r in group) / len(group)
        avg_time = sum(r["total_time_ms"] for r in group) / len(group)
        on_device_ratio = sum(1 for r in group if r["source"] == "on-device") / len(group)

        time_score = max(0, 1 - avg_time / time_baseline_ms)

        level_score = (0.60 * avg_f1) + (0.15 * time_score) + (0.25 * on_device_ratio)
        total_score += weight * level_score

    return total_score * 100


if __name__ == "__main__":
    run_benchmark()
