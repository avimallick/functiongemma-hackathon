import sys, os
sys.path.insert(0, "cactus/python/src")
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"

import json
from main import generate_hybrid


############## Tool definitions ##############

TOOL_GET_WEATHER = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"],
    },
}

TOOL_SET_ALARM = {
    "name": "set_alarm",
    "description": "Set an alarm for a given time",
    "parameters": {
        "type": "object",
        "properties": {
            "hour": {"type": "integer", "description": "Hour to set the alarm for"},
            "minute": {"type": "integer", "description": "Minute to set the alarm for"},
        },
        "required": ["hour", "minute"],
    },
}

TOOL_SEND_MESSAGE = {
    "name": "send_message",
    "description": "Send a message to a contact",
    "parameters": {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Name of the person to send the message to"},
            "message": {"type": "string", "description": "The message content to send"},
        },
        "required": ["recipient", "message"],
    },
}

TOOL_CREATE_REMINDER = {
    "name": "create_reminder",
    "description": "Create a reminder with a title and time",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Reminder title"},
            "time": {"type": "string", "description": "Time for the reminder (e.g. 3:00 PM)"},
        },
        "required": ["title", "time"],
    },
}

TOOL_SEARCH_CONTACTS = {
    "name": "search_contacts",
    "description": "Search for a contact by name",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Name to search for"},
        },
        "required": ["query"],
    },
}

TOOL_PLAY_MUSIC = {
    "name": "play_music",
    "description": "Play a song or playlist",
    "parameters": {
        "type": "object",
        "properties": {
            "song": {"type": "string", "description": "Song or playlist name"},
        },
        "required": ["song"],
    },
}

TOOL_SET_TIMER = {
    "name": "set_timer",
    "description": "Set a countdown timer",
    "parameters": {
        "type": "object",
        "properties": {
            "minutes": {"type": "integer", "description": "Number of minutes"},
        },
        "required": ["minutes"],
    },
}


############## Benchmark cases (v3 test set) ##############

BENCHMARKS_V3 = [
    # ===== Easy: 1 tool, direct request =====
    {
        "name": "weather_seoul",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "What is the weather in Seoul?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_calls": [{"name": "get_weather", "arguments": {"location": "Seoul"}}],
    },
    {
        "name": "alarm_330pm",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Set an alarm for 3:30 PM."}],
        "tools": [TOOL_SET_ALARM],
        "expected_calls": [{"name": "set_alarm", "arguments": {"hour": 15, "minute": 30}}],
    },
    {
        "name": "message_diana",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Send a message to Diana saying I'm on my way."}],
        "tools": [TOOL_SEND_MESSAGE],
        "expected_calls": [{"name": "send_message", "arguments": {"recipient": "Diana", "message": "I'm on my way"}}],
    },
    {
        "name": "weather_bangkok",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "How's the weather in Bangkok?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_calls": [{"name": "get_weather", "arguments": {"location": "Bangkok"}}],
    },
    {
        "name": "alarm_midnight",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Wake me up at midnight."}],
        "tools": [TOOL_SET_ALARM],
        "expected_calls": [{"name": "set_alarm", "arguments": {"hour": 0, "minute": 0}}],
    },
    {
        "name": "play_jazz_playlist",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Play my jazz playlist."}],
        "tools": [TOOL_PLAY_MUSIC],
        "expected_calls": [{"name": "play_music", "arguments": {"song": "jazz playlist"}}],
    },
    {
        "name": "timer_45min",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Set a timer for 45 minutes."}],
        "tools": [TOOL_SET_TIMER],
        "expected_calls": [{"name": "set_timer", "arguments": {"minutes": 45}}],
    },
    {
        "name": "reminder_yoga",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Remind me about yoga at 7:30 AM."}],
        "tools": [TOOL_CREATE_REMINDER],
        "expected_calls": [{"name": "create_reminder", "arguments": {"title": "yoga", "time": "7:30 AM"}}],
    },
    {
        "name": "search_grace",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Look up Grace in my contacts."}],
        "tools": [TOOL_SEARCH_CONTACTS],
        "expected_calls": [{"name": "search_contacts", "arguments": {"query": "Grace"}}],
    },
    {
        "name": "weather_nairobi",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "What's the weather like in Nairobi?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_calls": [{"name": "get_weather", "arguments": {"location": "Nairobi"}}],
    },

    # ===== Medium: 2-3 tools, must pick the right one =====
    {
        "name": "timer_among_three_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Set a timer for 8 minutes."}],
        "tools": [TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_SET_TIMER],
        "expected_calls": [{"name": "set_timer", "arguments": {"minutes": 8}}],
    },
    {
        "name": "weather_among_two_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "What's the weather in Cairo?"}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_GET_WEATHER],
        "expected_calls": [{"name": "get_weather", "arguments": {"location": "Cairo"}}],
    },
    {
        "name": "reminder_among_three_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Remind me to pick up the kids at 3:15 PM."}],
        "tools": [TOOL_SET_ALARM, TOOL_CREATE_REMINDER, TOOL_PLAY_MUSIC],
        "expected_calls": [{"name": "create_reminder", "arguments": {"title": "pick up the kids", "time": "3:15 PM"}}],
    },
    {
        "name": "music_among_four_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Play some ambient music."}],
        "tools": [TOOL_SET_TIMER, TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC],
        "expected_calls": [{"name": "play_music", "arguments": {"song": "ambient music"}}],
    },
    {
        "name": "search_among_three_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Find Ethan in my contacts."}],
        "tools": [TOOL_GET_WEATHER, TOOL_SEARCH_CONTACTS, TOOL_SET_ALARM],
        "expected_calls": [{"name": "search_contacts", "arguments": {"query": "Ethan"}}],
    },
    {
        "name": "alarm_among_four_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Set an alarm for 10:45 PM."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_CREATE_REMINDER, TOOL_GET_WEATHER, TOOL_SET_ALARM],
        "expected_calls": [{"name": "set_alarm", "arguments": {"hour": 22, "minute": 45}}],
    },
    {
        "name": "message_among_five_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Text Olivia saying happy new year."}],
        "tools": [TOOL_SET_ALARM, TOOL_GET_WEATHER, TOOL_SET_TIMER, TOOL_PLAY_MUSIC, TOOL_SEND_MESSAGE],
        "expected_calls": [{"name": "send_message", "arguments": {"recipient": "Olivia", "message": "happy new year"}}],
    },
    {
        "name": "weather_among_five_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "What's the weather in Buenos Aires?"}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_SET_TIMER, TOOL_CREATE_REMINDER, TOOL_PLAY_MUSIC, TOOL_GET_WEATHER],
        "expected_calls": [{"name": "get_weather", "arguments": {"location": "Buenos Aires"}}],
    },
    {
        "name": "timer_among_four_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Start a 2 minute countdown."}],
        "tools": [TOOL_SET_ALARM, TOOL_SEND_MESSAGE, TOOL_SET_TIMER, TOOL_GET_WEATHER],
        "expected_calls": [{"name": "set_timer", "arguments": {"minutes": 2}}],
    },
    {
        "name": "reminder_among_five_v3",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Remind me to call mom at 6:30 PM."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_SEARCH_CONTACTS, TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_CREATE_REMINDER],
        "expected_calls": [{"name": "create_reminder", "arguments": {"title": "call mom", "time": "6:30 PM"}}],
    },

    # ===== Hard: multiple tools needed, multi-call =====
    {
        "name": "weather_and_alarm_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Check the weather in Oslo and set an alarm for 6:00 AM."}],
        "tools": [TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC],
        "expected_calls": [
            {"name": "get_weather", "arguments": {"location": "Oslo"}},
            {"name": "set_alarm", "arguments": {"hour": 6, "minute": 0}},
        ],
    },
    {
        "name": "music_and_timer_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Play hip hop music and set a timer for 60 minutes."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_SET_TIMER, TOOL_CREATE_REMINDER, TOOL_GET_WEATHER],
        "expected_calls": [
            {"name": "play_music", "arguments": {"song": "hip hop music"}},
            {"name": "set_timer", "arguments": {"minutes": 60}},
        ],
    },
    {
        "name": "message_and_reminder_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Send a message to Felix saying thanks for dinner and remind me to reply to emails at 9:00 AM."}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_CREATE_REMINDER, TOOL_GET_WEATHER, TOOL_SET_ALARM],
        "expected_calls": [
            {"name": "send_message", "arguments": {"recipient": "Felix", "message": "thanks for dinner"}},
            {"name": "create_reminder", "arguments": {"title": "reply to emails", "time": "9:00 AM"}},
        ],
    },
    {
        "name": "search_and_weather_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Find Priya in my contacts and check the weather in Mumbai."}],
        "tools": [TOOL_SEARCH_CONTACTS, TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_PLAY_MUSIC],
        "expected_calls": [
            {"name": "search_contacts", "arguments": {"query": "Priya"}},
            {"name": "get_weather", "arguments": {"location": "Mumbai"}},
        ],
    },
    {
        "name": "alarm_and_music_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Set an alarm for 8:30 AM and play chill vibes."}],
        "tools": [TOOL_SET_ALARM, TOOL_PLAY_MUSIC, TOOL_SET_TIMER, TOOL_SEND_MESSAGE],
        "expected_calls": [
            {"name": "set_alarm", "arguments": {"hour": 8, "minute": 30}},
            {"name": "play_music", "arguments": {"song": "chill vibes"}},
        ],
    },
    {
        "name": "reminder_and_search_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Remind me about the book club at 5:30 PM and find Lucas in my contacts."}],
        "tools": [TOOL_CREATE_REMINDER, TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_GET_WEATHER],
        "expected_calls": [
            {"name": "create_reminder", "arguments": {"title": "book club", "time": "5:30 PM"}},
            {"name": "search_contacts", "arguments": {"query": "Lucas"}},
        ],
    },
    {
        "name": "message_timer_weather_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Text Sophie saying we're out of coffee, set a timer for 10 minutes, and check the weather in Vienna."}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_SET_TIMER, TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_PLAY_MUSIC],
        "expected_calls": [
            {"name": "send_message", "arguments": {"recipient": "Sophie", "message": "we're out of coffee"}},
            {"name": "set_timer", "arguments": {"minutes": 10}},
            {"name": "get_weather", "arguments": {"location": "Vienna"}},
        ],
    },
    {
        "name": "alarm_reminder_music_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Set an alarm for 7:00 AM, remind me to take vitamins at 8:00 AM, and play morning beats."}],
        "tools": [TOOL_SET_ALARM, TOOL_CREATE_REMINDER, TOOL_PLAY_MUSIC, TOOL_GET_WEATHER, TOOL_SEND_MESSAGE],
        "expected_calls": [
            {"name": "set_alarm", "arguments": {"hour": 7, "minute": 0}},
            {"name": "create_reminder", "arguments": {"title": "take vitamins", "time": "8:00 AM"}},
            {"name": "play_music", "arguments": {"song": "morning beats"}},
        ],
    },
    {
        "name": "search_message_alarm_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Look up Marcus in my contacts, send him a message saying project is done, and set an alarm for 4:00 PM."}],
        "tools": [TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_SET_ALARM, TOOL_GET_WEATHER, TOOL_SET_TIMER],
        "expected_calls": [
            {"name": "search_contacts", "arguments": {"query": "Marcus"}},
            {"name": "send_message", "arguments": {"recipient": "Marcus", "message": "project is done"}},
            {"name": "set_alarm", "arguments": {"hour": 16, "minute": 0}},
        ],
    },
    {
        "name": "weather_music_reminder_v3",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Check the weather in Cape Town, play ocean sounds, and remind me to pack sunscreen at 10:00 AM."}],
        "tools": [TOOL_GET_WEATHER, TOOL_PLAY_MUSIC, TOOL_CREATE_REMINDER, TOOL_SET_ALARM, TOOL_SEND_MESSAGE],
        "expected_calls": [
            {"name": "get_weather", "arguments": {"location": "Cape Town"}},
            {"name": "play_music", "arguments": {"song": "ocean sounds"}},
            {"name": "create_reminder", "arguments": {"title": "pack sunscreen", "time": "10:00 AM"}},
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
        benchmarks = BENCHMARKS_V3

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

    print("\n=== Benchmark Results (v3 set) ===\n")
    print(f"  {'#':>2} | {'Difficulty':<10} | {'Name':<32} | {'Time (ms)':>10} | {'F1':>5} | Source")
    print(f"  {'--':>2}-+-{'-'*10}-+-{'-'*32}-+-{'-'*10}-+-{'-'*5}-+-{'-'*20}")
    for i, r in enumerate(results, 1):
        print(f"  {i:>2} | {r['difficulty']:<10} | {r['name']:<32} | {r['total_time_ms']:>10.2f} | {r['f1']:>5.2f} | {r['source']}")

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
