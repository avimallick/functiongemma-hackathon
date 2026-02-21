"""
Stress test with diverse phrasings to simulate hidden eval.
Tests generalization beyond standard benchmark patterns.
Add to .gitignore — this is for local testing only.
"""
import sys, os
sys.path.insert(0, "cactus/python/src")
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"

import json
from main import generate_hybrid

# ==================== Tool definitions (same as benchmark) ====================

TOOL_GET_WEATHER = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]},
}
TOOL_SET_ALARM = {
    "name": "set_alarm",
    "description": "Set an alarm for a given time",
    "parameters": {"type": "object", "properties": {"hour": {"type": "integer", "description": "Hour"}, "minute": {"type": "integer", "description": "Minute"}}, "required": ["hour", "minute"]},
}
TOOL_SEND_MESSAGE = {
    "name": "send_message",
    "description": "Send a message to a contact",
    "parameters": {"type": "object", "properties": {"recipient": {"type": "string", "description": "Name of the person to send the message to"}, "message": {"type": "string", "description": "The message content to send"}}, "required": ["recipient", "message"]},
}
TOOL_CREATE_REMINDER = {
    "name": "create_reminder",
    "description": "Create a reminder with a title and time",
    "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Reminder title"}, "time": {"type": "string", "description": "Time for the reminder (e.g. 3:00 PM)"}}, "required": ["title", "time"]},
}
TOOL_SEARCH_CONTACTS = {
    "name": "search_contacts",
    "description": "Search for a contact by name",
    "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Name to search for"}}, "required": ["query"]},
}
TOOL_PLAY_MUSIC = {
    "name": "play_music",
    "description": "Play a song or playlist",
    "parameters": {"type": "object", "properties": {"song": {"type": "string", "description": "Song or playlist name"}}, "required": ["song"]},
}
TOOL_SET_TIMER = {
    "name": "set_timer",
    "description": "Set a countdown timer",
    "parameters": {"type": "object", "properties": {"minutes": {"type": "integer", "description": "Number of minutes"}}, "required": ["minutes"]},
}

# ==================== Test cases ====================

STRESS_TESTS = [
    # === EASY: 1 tool, varied phrasing ===
    {
        "name": "weather_casual_1",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "How's it looking outside in Denver?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_tool": "get_weather",
    },
    {
        "name": "weather_indirect",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Do I need an umbrella in Seattle?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_tool": "get_weather",
    },
    {
        "name": "alarm_casual",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Wake me up at 6:30 AM please."}],
        "tools": [TOOL_SET_ALARM],
        "expected_tool": "set_alarm",
    },
    {
        "name": "message_direct",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Send a message to Rachel saying see you soon."}],
        "tools": [TOOL_SEND_MESSAGE],
        "expected_tool": "send_message",
    },
    {
        "name": "timer_simple",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Set a timer for 8 minutes."}],
        "tools": [TOOL_SET_TIMER],
        "expected_tool": "set_timer",
    },
    {
        "name": "music_specific",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Play Stairway to Heaven."}],
        "tools": [TOOL_PLAY_MUSIC],
        "expected_tool": "play_music",
    },
    {
        "name": "reminder_basic",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Remind me to take out the trash at 8:00 PM."}],
        "tools": [TOOL_CREATE_REMINDER],
        "expected_tool": "create_reminder",
    },
    {
        "name": "search_basic",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "Find Alex in my contacts."}],
        "tools": [TOOL_SEARCH_CONTACTS],
        "expected_tool": "search_contacts",
    },
    {
        "name": "weather_formal",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "What is the current temperature in Tokyo?"}],
        "tools": [TOOL_GET_WEATHER],
        "expected_tool": "get_weather",
    },
    {
        "name": "alarm_natural",
        "difficulty": "easy",
        "messages": [{"role": "user", "content": "I need to get up at 5 AM tomorrow."}],
        "tools": [TOOL_SET_ALARM],
        "expected_tool": "set_alarm",
    },

    # === MEDIUM: 2-4 tools, must pick the right one ===
    {
        "name": "weather_with_distractors",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Is it cold in Moscow right now?"}],
        "tools": [TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_SET_ALARM, TOOL_PLAY_MUSIC],
        "expected_tool": "get_weather",
    },
    {
        "name": "alarm_among_many",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Can you set an alarm for 7:45 AM?"}],
        "tools": [TOOL_SET_ALARM, TOOL_SET_TIMER, TOOL_CREATE_REMINDER],
        "expected_tool": "set_alarm",
    },
    {
        "name": "message_among_many",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Text Mike saying dinner is at 8."}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_PLAY_MUSIC, TOOL_SET_TIMER],
        "expected_tool": "send_message",
    },
    {
        "name": "timer_vs_alarm",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Give me a 25 minute timer."}],
        "tools": [TOOL_SET_TIMER, TOOL_SET_ALARM, TOOL_CREATE_REMINDER],
        "expected_tool": "set_timer",
    },
    {
        "name": "music_among_many",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "I want to listen to Hotel California."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_SEARCH_CONTACTS, TOOL_GET_WEATHER],
        "expected_tool": "play_music",
    },
    {
        "name": "reminder_among_many",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Remind me to water the plants at 4:00 PM."}],
        "tools": [TOOL_CREATE_REMINDER, TOOL_SET_ALARM, TOOL_SEND_MESSAGE, TOOL_SET_TIMER],
        "expected_tool": "create_reminder",
    },
    {
        "name": "search_among_many",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Look up Daniel in my contacts."}],
        "tools": [TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_GET_WEATHER, TOOL_PLAY_MUSIC],
        "expected_tool": "search_contacts",
    },
    {
        "name": "weather_rephrased",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "What's the forecast for Chicago?"}],
        "tools": [TOOL_GET_WEATHER, TOOL_SET_TIMER, TOOL_PLAY_MUSIC],
        "expected_tool": "get_weather",
    },
    {
        "name": "alarm_rephrased",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Make sure I'm up by 8 AM."}],
        "tools": [TOOL_SET_ALARM, TOOL_CREATE_REMINDER, TOOL_SEND_MESSAGE],
        "expected_tool": "set_alarm",
    },
    {
        "name": "music_genre",
        "difficulty": "medium",
        "messages": [{"role": "user", "content": "Play some hip hop."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_SET_ALARM, TOOL_GET_WEATHER],
        "expected_tool": "play_music",
    },

    # === HARD: multi-action, must return multiple correct calls ===
    {
        "name": "weather_and_alarm",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Check the weather in Boston and set an alarm for 6 AM."}],
        "tools": [TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC],
        "expected_tools": ["get_weather", "set_alarm"],
    },
    {
        "name": "message_and_music",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Text Jenny saying I miss you and play Wonderwall."}],
        "tools": [TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC, TOOL_GET_WEATHER, TOOL_SET_TIMER],
        "expected_tools": ["send_message", "play_music"],
    },
    {
        "name": "triple_action",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Find Anna in contacts, message her saying happy anniversary, and set a 30 minute timer."}],
        "tools": [TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_SET_TIMER, TOOL_GET_WEATHER, TOOL_PLAY_MUSIC],
        "expected_tools": ["search_contacts", "send_message", "set_timer"],
    },
    {
        "name": "reminder_and_alarm",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Remind me to pick up dry cleaning at 5:00 PM and set an alarm for 4:30 PM."}],
        "tools": [TOOL_CREATE_REMINDER, TOOL_SET_ALARM, TOOL_PLAY_MUSIC, TOOL_SEND_MESSAGE],
        "expected_tools": ["create_reminder", "set_alarm"],
    },
    {
        "name": "weather_and_message",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Check the weather in Chicago and send Robert a message saying we're still on for lunch."}],
        "tools": [TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_SET_ALARM, TOOL_PLAY_MUSIC],
        "expected_tools": ["get_weather", "send_message"],
    },
    {
        "name": "timer_and_reminder",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Set a 10 minute timer and remind me to check the oven at 6:30 PM."}],
        "tools": [TOOL_SET_TIMER, TOOL_CREATE_REMINDER, TOOL_GET_WEATHER, TOOL_SEND_MESSAGE],
        "expected_tools": ["set_timer", "create_reminder"],
    },
    {
        "name": "music_and_weather",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Play some jazz and tell me the weather in LA."}],
        "tools": [TOOL_PLAY_MUSIC, TOOL_GET_WEATHER, TOOL_SET_ALARM, TOOL_SET_TIMER],
        "expected_tools": ["play_music", "get_weather"],
    },
    {
        "name": "search_and_message_hard",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Look up Chris in my contacts and send him a message saying the project is done."}],
        "tools": [TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_GET_WEATHER, TOOL_PLAY_MUSIC, TOOL_SET_ALARM],
        "expected_tools": ["search_contacts", "send_message"],
    },
    {
        "name": "alarm_weather_message",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Set an alarm for 7 AM, check the weather in Miami, and text Sam saying good morning."}],
        "tools": [TOOL_SET_ALARM, TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC, TOOL_SET_TIMER],
        "expected_tools": ["set_alarm", "get_weather", "send_message"],
    },
    {
        "name": "timer_music_reminder_hard",
        "difficulty": "hard",
        "messages": [{"role": "user", "content": "Set a 20 minute timer, play lo-fi beats, and remind me to stretch at 3:00 PM."}],
        "tools": [TOOL_SET_TIMER, TOOL_PLAY_MUSIC, TOOL_CREATE_REMINDER, TOOL_GET_WEATHER, TOOL_SEND_MESSAGE],
        "expected_tools": ["set_timer", "play_music", "create_reminder"],
    },
]


def _check_result(result, case):
    """Check if result matches expected. Returns (tool_correct, has_args)."""
    calls = result.get("function_calls", [])
    called_names = {c.get("name") for c in calls}

    if case["difficulty"] in ("easy", "medium"):
        expected = case["expected_tool"]
        tool_correct = expected in called_names
        has_args = False
        if tool_correct:
            matching = [c for c in calls if c.get("name") == expected]
            if matching:
                has_args = bool(matching[0].get("arguments"))
        return tool_correct, has_args
    else:
        expected = set(case["expected_tools"])
        tool_correct = expected.issubset(called_names)
        has_args = all(
            any(c.get("name") == t and bool(c.get("arguments")) for c in calls)
            for t in expected
        )
        return tool_correct, has_args


def run_stress_test():
    total = len(STRESS_TESTS)
    results = []

    for i, case in enumerate(STRESS_TESTS, 1):
        print(f"[{i}/{total}] {case['name']} ({case['difficulty']})...", end=" ", flush=True)
        result = generate_hybrid(case["messages"], case["tools"])
        source = result.get("source", "unknown")
        tool_ok, args_ok = _check_result(result, case)
        status = "PASS" if tool_ok else "FAIL"
        print(f"{status} | {result['total_time_ms']:.0f}ms | {source}")

        results.append({
            "name": case["name"],
            "difficulty": case["difficulty"],
            "tool_correct": tool_ok,
            "args_present": args_ok,
            "source": source,
            "total_time_ms": result["total_time_ms"],
            "calls": result["function_calls"],
            "case": case,
        })

    print(f"\n{'='*60}")
    print(f"  STRESS TEST RESULTS")
    print(f"{'='*60}")

    for diff in ["easy", "medium", "hard"]:
        group = [r for r in results if r["difficulty"] == diff]
        if not group:
            continue
        correct = sum(1 for r in group if r["tool_correct"])
        on_device = sum(1 for r in group if r["source"] == "on-device")
        avg_time = sum(r["total_time_ms"] for r in group) / len(group)
        print(f"  {diff:<8} tool_correct={correct}/{len(group)}  on-device={on_device}/{len(group)}  avg_time={avg_time:.0f}ms")

    total_correct = sum(1 for r in results if r["tool_correct"])
    on_device_total = sum(1 for r in results if r["source"] == "on-device")
    cloud_total = total - on_device_total
    avg_time = sum(r["total_time_ms"] for r in results) / total

    print(f"\n  OVERALL: {total_correct}/{total} correct ({100*total_correct/total:.0f}%)")
    print(f"  On-device: {on_device_total}/{total} ({100*on_device_total/total:.0f}%)")
    print(f"  Cloud: {cloud_total}/{total} ({100*cloud_total/total:.0f}%)")
    print(f"  Avg time: {avg_time:.0f}ms")

    failures = [r for r in results if not r["tool_correct"]]
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for r in failures:
            expected = r["case"].get("expected_tool") or r["case"].get("expected_tools")
            got = [c.get("name") for c in r["calls"]]
            print(f"    {r['name']}: expected={expected} got={got} | {r['source']}")
    else:
        print(f"\n  All tests passed!")

    print(f"{'='*60}")


if __name__ == "__main__":
    run_stress_test()