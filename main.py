import sys

sys.path.insert(0, "cactus/python/src")
functiongemma_path = "cactus/weights/functiongemma-270m-it"

import atexit
import json
import os
import re
import time

from google import genai
from google.genai import types

from cactus import cactus_complete, cactus_destroy, cactus_init

_CACTUS_MODEL = None


def _get_cactus_model():
    """Lazily initialize and reuse the local model across calls."""
    global _CACTUS_MODEL
    if _CACTUS_MODEL is None:
        _CACTUS_MODEL = cactus_init(functiongemma_path)
    return _CACTUS_MODEL


@atexit.register
def _cleanup_cactus_model():
    global _CACTUS_MODEL
    if _CACTUS_MODEL is not None:
        cactus_destroy(_CACTUS_MODEL)
        _CACTUS_MODEL = None


def generate_cactus(messages, tools):
    """Run function calling on-device via FunctionGemma + Cactus."""
    model = _get_cactus_model()

    cactus_tools = [
        {
            "type": "function",
            "function": t,
        }
        for t in tools
    ]

    raw_str = cactus_complete(
        model,
        [
            {
                "role": "system",
                "content": "You are a helpful assistant that can use tools.",
            }
        ]
        + messages,
        tools=cactus_tools,
        force_tools=True,
        max_tokens=256,
        stop_sequences=["<|im_end|>", "<end_of_turn>"],
    )

    try:
        raw = json.loads(raw_str)
    except json.JSONDecodeError:
        return {
            "function_calls": [],
            "total_time_ms": 0,
            "confidence": 0,
        }

    return {
        "function_calls": raw.get("function_calls", []),
        "total_time_ms": raw.get("total_time_ms", 0),
        "confidence": raw.get("confidence", 0),
    }


def generate_cloud(messages, tools):
    """Run function calling via Gemini Cloud API."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    gemini_tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            k: types.Schema(
                                type=v["type"].upper(),
                                description=v.get("description", ""),
                            )
                            for k, v in t["parameters"]["properties"].items()
                        },
                        required=t["parameters"].get("required", []),
                    ),
                )
                for t in tools
            ]
        )
    ]

    contents = [m["content"] for m in messages if m["role"] == "user"]
    system_instruction = "You are a function-calling assistant. Return all needed function calls for the user request."

    start_time = time.time()

    gemini_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            tools=gemini_tools,
            system_instruction=system_instruction,
            temperature=0,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.ANY,
                    allowed_function_names=[t["name"] for t in tools],
                )
            ),
        ),
    )

    total_time_ms = (time.time() - start_time) * 1000

    function_calls = []
    for candidate in gemini_response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append(
                    {
                        "name": part.function_call.name,
                        "arguments": dict(part.function_call.args),
                    }
                )

    return {
        "function_calls": function_calls,
        "total_time_ms": total_time_ms,
    }


def generate_hybrid(messages, tools, confidence_threshold=0.99):
    """
    Hybrid strategy: local-first with regex repair.
    Always runs local model (preserves on-device credit).
    Uses regex to validate/repair arguments.
    Cloud fallback only when both fail.
    """
    user_text = " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    )
    user_text_l = user_text.lower()
    tool_map = {t["name"]: t for t in tools}
    available = set(tool_map.keys())

    # ==================== HELPERS ====================

    def _coerce_call_types(call):
        """Fix type mismatches (e.g., string "5" -> int 5)."""
        name = call.get("name")
        args = call.get("arguments", {})
        if not isinstance(args, dict):
            args = {}
        out = {"name": name, "arguments": dict(args)}
        if name not in tool_map:
            return out
        props = tool_map[name].get("parameters", {}).get("properties", {})
        for key, val in list(out["arguments"].items()):
            ptype = props.get(key, {}).get("type", "").lower()
            if ptype == "integer":
                if isinstance(val, str) and re.fullmatch(r"[+-]?\d+", val.strip()):
                    out["arguments"][key] = int(val.strip())
                elif isinstance(val, float) and val.is_integer():
                    out["arguments"][key] = int(val)
            elif ptype == "string":
                if isinstance(val, str):
                    out["arguments"][key] = val.strip()
                else:
                    out["arguments"][key] = str(val)
        return out

    def _schema_valid(call):
        """Check if call has valid tool name, required params, and correct types."""
        name = call.get("name")
        args = call.get("arguments", {})
        if name not in tool_map or not isinstance(args, dict):
            return False
        required = tool_map[name].get("parameters", {}).get("required", [])
        props = tool_map[name].get("parameters", {}).get("properties", {})
        for key in required:
            if key not in args:
                return False
        for key, val in args.items():
            if key not in props:
                continue
            ptype = props[key].get("type", "").lower()
            if ptype == "integer" and not isinstance(val, int):
                return False
            if ptype == "string" and not isinstance(val, str):
                return False
        return True

    def _semantic_valid(calls):
        """Domain-specific sanity checks on argument values."""
        for c in calls:
            name = c.get("name")
            args = c.get("arguments", {})
            if name == "set_alarm":
                h, m = args.get("hour"), args.get("minute")
                if not (isinstance(h, int) and isinstance(m, int) and 0 <= h <= 23 and 0 <= m <= 59):
                    return False
            elif name == "set_timer":
                mins = args.get("minutes")
                if not (isinstance(mins, int) and mins > 0):
                    return False
            elif name == "get_weather":
                loc = args.get("location")
                if not (isinstance(loc, str) and loc.strip()):
                    return False
            elif name == "search_contacts":
                q = args.get("query")
                if not (isinstance(q, str) and q.strip()):
                    return False
            elif name == "send_message":
                r, msg = args.get("recipient"), args.get("message")
                if not (isinstance(r, str) and r.strip() and isinstance(msg, str) and msg.strip()):
                    return False
            elif name == "create_reminder":
                t, tm = args.get("title"), args.get("time")
                if not (isinstance(t, str) and t.strip() and isinstance(tm, str) and tm.strip()):
                    return False
            elif name == "play_music":
                s = args.get("song")
                if not (isinstance(s, str) and s.strip()):
                    return False
        return True

    # ==================== INTENT DETECTION ====================

    def _detect_intents(text_l):
        """Broad intent detection."""
        intent_patterns = {
            "get_weather": [r"\bweather\b", r"\bforecast\b", r"\btemperature\b", r"\bhow.?s it (?:looking |going )?(?:outside|out)\b"],
            "set_alarm": [r"\balarm\b", r"\bwake.{0,5}up\b"],
            "send_message": [r"\bsend\b.*\b(?:message|msg)\b", r"\btext\b", r"\btell\s+\w+\s+(?:that|to say)\b", r"\bmessage\s+\w+\b", r"\bsaying\b"],
            "create_reminder": [r"\bremind\b", r"\breminder\b"],
            "search_contacts": [r"\bcontacts?\b", r"\blook\s*up\b", r"\bsearch\s+for\b", r"\bfind\b.*\b(?:contact|number|phone)\b"],
            "play_music": [r"\bplay\b", r"\blisten\b", r"\bmusic\b", r"\bsong\b", r"\bplaylist\b"],
            "set_timer": [r"\btimer\b", r"\bcountdown\b"],
        }
        intents = set()
        for tool_name, patterns in intent_patterns.items():
            if tool_name not in available:
                continue
            if any(re.search(p, text_l) for p in patterns):
                intents.add(tool_name)
        return intents

    def _count_actions(text_l):
        splitters = re.split(r"\s*,\s*(?:and\s+)?|\s+\band\b\s+|\s+\bthen\b\s+|\s+\balso\b\s+|\s+\bplus\b\s+", text_l)
        parts = [p.strip() for p in splitters if p and p.strip()]
        return max(len(parts), 1)

    # ==================== REGEX EXTRACTION ====================

    def _clean(s):
        s = re.sub(r"\s+", " ", str(s)).strip()
        s = s.rstrip(".,!?")
        s = s.strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
            s = s[1:-1].strip()
        return s

    def _parse_alarm_24h(hour_s, minute_s, mer_s):
        hour = int(hour_s)
        minute = int(minute_s or 0)
        mer = mer_s.lower()
        if mer == "pm" and hour != 12:
            hour += 12
        if mer == "am" and hour == 12:
            hour = 0
        return {"hour": hour, "minute": minute}

    def _extract_rule_calls(text):
        """Regex-based extraction with broadened patterns."""
        clauses = [
            c.strip()
            for c in re.split(r"\s*,\s*(?:and\s+)?|\s+\band\b\s+|\s+\bthen\b\s+", text, flags=re.I)
            if c and c.strip()
        ]
        calls = []
        last_contact = None

        for raw_clause in clauses:
            clause = raw_clause.strip().strip(".!? ")
            clause_l = clause.lower()
            if not clause:
                continue

            # --- search_contacts ---
            if "search_contacts" in available:
                m = re.search(
                    r"(?:find|look\s*up|search\s+for|search)\s+([A-Za-z][A-Za-z\s\-']+?)\s+(?:in|from|on)\s+(?:my\s+)?contacts?\b",
                    clause, re.I,
                )
                if m:
                    query = _clean(m.group(1))
                    if query:
                        calls.append({"name": "search_contacts", "arguments": {"query": query}})
                        last_contact = query
                        continue

            # --- send_message ---
            if "send_message" in available:
                m = re.search(
                    r"(?:send|text)\s+(?:a\s+message\s+to\s+)?((?!him\b|her\b|them\b)[A-Za-z][A-Za-z\s\-']*?)\s+(?:saying|that says|with)\s+(.+)$",
                    clause, re.I,
                )
                if m:
                    recipient = _clean(m.group(1))
                    message = _clean(m.group(2))
                    if recipient and message:
                        calls.append({"name": "send_message", "arguments": {"recipient": recipient, "message": message}})
                        last_contact = recipient
                        continue

                m = re.search(
                    r"(?:send|text)\s+(?:him|her|them)\s+(?:a\s+)?message\s+(?:saying|that says|with)\s+(.+)$",
                    clause, re.I,
                )
                if m and last_contact:
                    message = _clean(m.group(1))
                    if message:
                        calls.append({"name": "send_message", "arguments": {"recipient": last_contact, "message": message}})
                        continue

                m = re.search(
                    r"\bmessage\s+([A-Za-z][A-Za-z\s\-']*?)\s+(?:saying|that says|with)\s+(.+)$",
                    clause, re.I,
                )
                if m:
                    recipient = _clean(m.group(1))
                    message = _clean(m.group(2))
                    if recipient and message:
                        calls.append({"name": "send_message", "arguments": {"recipient": recipient, "message": message}})
                        last_contact = recipient
                        continue

                # "tell X that Y" / "tell X to say Y"
                m = re.search(
                    r"\btell\s+([A-Za-z][A-Za-z\s\-']*?)\s+(?:that|to say)\s+(.+)$",
                    clause, re.I,
                )
                if m:
                    recipient = _clean(m.group(1))
                    message = _clean(m.group(2))
                    if recipient and message:
                        calls.append({"name": "send_message", "arguments": {"recipient": recipient, "message": message}})
                        last_contact = recipient
                        continue

            # --- get_weather ---
            if "get_weather" in available:
                m = re.search(
                    r"(?:weather|forecast|temperature)(?:\s+like)?\s+(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-']+)",
                    clause, re.I,
                )
                if not m:
                    m = re.search(
                        r"(?:check|get|look\s*up|what'?s?)\s+(?:the\s+)?(?:weather|forecast)\s+(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-']+)",
                        clause, re.I,
                    )
                if not m:
                    m = re.search(
                        r"(?:how.?s|what.?s)\s+(?:it|the weather|things).*?\b(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-']+)",
                        clause, re.I,
                    )
                if not m:
                    m = re.search(
                        r"(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-']+?)[\s,]+(?:what(?:'?s| is)\s+the\s+)?(?:weather|forecast|temperature)",
                        clause, re.I,
                    )
                if not m:
                    m = re.search(
                        r"(?:weather|forecast|temperature)\s+(?:of|for)\s+([A-Za-z][A-Za-z\s\-']+)",
                        clause, re.I,
                    )
                if m:
                    location = _clean(m.group(1))
                    if location:
                        calls.append({"name": "get_weather", "arguments": {"location": location}})
                        continue

            # --- set_alarm ---
            if "set_alarm" in available:
                m = re.search(
                    r"(?:set\s+(?:an?\s+)?alarm|wake\s+me\s+up)\s+(?:for|at)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
                    clause, re.I,
                )
                if not m:
                    m = re.search(
                        r"\balarm\b.*?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
                        clause, re.I,
                    )
                if not m:
                    m = re.search(
                        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s+alarm\b",
                        clause, re.I,
                    )
                if m:
                    alarm = _parse_alarm_24h(m.group(1), m.group(2), m.group(3))
                    calls.append({"name": "set_alarm", "arguments": alarm})
                    continue

            # --- set_timer ---
            if "set_timer" in available:
                m = re.search(
                    r"(?:set\s+(?:a\s+)?)?(?:timer\s+(?:for\s+)?|(\d+)\s*(?:minute|min)\s+timer)(\d+)?\s*(?:minutes?|mins?)?\b",
                    clause, re.I,
                )
                if not m:
                    m = re.search(r"(\d+)\s*(?:minutes?|mins?)\s*timer\b", clause, re.I)
                if not m:
                    m = re.search(r"\btimer\b.*?(\d+)\s*(?:minutes?|mins?)\b", clause, re.I)
                if not m:
                    m = re.search(r"set\s+(?:a\s+)?(\d+)\s*(?:minute|min)\s+timer\b", clause, re.I)
                if not m:
                    m = re.search(r"\bcountdown\b.*?(\d+)\s*(?:minutes?|mins?)\b", clause, re.I)
                if m:
                    digit_match = re.search(r"(\d+)", m.group(0))
                    if digit_match:
                        minutes = int(digit_match.group(1))
                        if minutes > 0:
                            calls.append({"name": "set_timer", "arguments": {"minutes": minutes}})
                            continue

            # --- create_reminder ---
            if "create_reminder" in available:
                m = re.search(
                    r"remind\s+me\s+(?:to\s+|about\s+)?(.+?)\s+(?:at|by|around)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b",
                    clause, re.I,
                )
                if m:
                    title = _clean(m.group(1))
                    title = re.sub(r"^(?:the|a|an)\s+", "", title, flags=re.I).strip()
                    time_raw = m.group(2).strip()
                    tm = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", time_raw, re.I)
                    if tm:
                        h, mn, mer = int(tm.group(1)), int(tm.group(2) or 0), tm.group(3).upper()
                        time_s = f"{h}:{mn:02d} {mer}"
                    else:
                        time_s = time_raw
                    if title:
                        calls.append({"name": "create_reminder", "arguments": {"title": title, "time": time_s}})
                        continue

            # --- play_music ---
            if "play_music" in available:
                m = re.search(r"\bplay\s+(.+)$", clause, re.I)
                if not m:
                    m = re.search(r"(?:listen\s+to|put\s+on)\s+(.+)$", clause, re.I)
                if m:
                    song = _clean(m.group(1))
                    had_some = bool(re.match(r"^some\s+", song, re.I))
                    song = re.sub(r"^(?:some|a|the|me)\s+", "", song, flags=re.I).strip()
                    if had_some:
                        stripped = re.sub(r"\s+music\s*$", "", song, flags=re.I).strip()
                        if stripped:
                            song = stripped
                    if song:
                        calls.append({"name": "play_music", "arguments": {"song": song}})
                        continue

        return calls

    # ==================== MAIN ROUTING LOGIC ====================

    intents = _detect_intents(user_text_l)
    num_intents = len(intents)
    action_count = _count_actions(user_text_l)
    is_multi_action = action_count >= 2 or num_intents >= 2

    # --- Step 1: ALWAYS run local first (preserves on-device credit) ---
    local = generate_cactus(messages, tools)
    local_calls = [_coerce_call_types(c) for c in local.get("function_calls", [])]
    local["function_calls"] = local_calls
    local_conf = float(local.get("confidence", 0.0) or 0.0)
    local_time = local.get("total_time_ms", 0)

    schema_ok = bool(local_calls) and all(_schema_valid(c) for c in local_calls)
    sem_ok = schema_ok and _semantic_valid(local_calls)

    local_tool_names = {c["name"] for c in local_calls} if local_calls else set()
    covers_intents = intents.issubset(local_tool_names) if intents else True

    # --- Step 2: Prepare regex repair ---
    rule_calls = [_coerce_call_types(c) for c in _extract_rule_calls(user_text)]
    rule_valid = bool(rule_calls) and all(_schema_valid(c) for c in rule_calls) and _semantic_valid(rule_calls)
    rule_tool_names = {c["name"] for c in rule_calls} if rule_calls else set()
    rule_covers = intents.issubset(rule_tool_names) if intents else True

    # --- Step 3: Decide what to return ---

    intent_match = True
    if intents and local_calls:
        if not covers_intents:
            intent_match = False

    # If regex found valid calls that cover intents, use regex args with local timing
    if rule_valid and rule_calls and rule_covers:
        count_ok = len(rule_calls) >= num_intents if is_multi_action else len(rule_calls) >= 1
        if count_ok:
            return {
                "function_calls": rule_calls,
                "total_time_ms": local_time,
                "confidence": max(local_conf, 0.85),
                "source": "on-device",
            }

    # Local model valid, correct intents — accept with low threshold
    if not is_multi_action:
        if sem_ok and intent_match and local_conf >= 0.40:
            local["source"] = "on-device"
            return local
    else:
        if sem_ok and intent_match and covers_intents and len(local_calls) >= num_intents and local_conf >= 0.45:
            local["source"] = "on-device"
            return local

    # Regex partial match — still better than nothing
    if rule_valid and rule_calls:
        return {
            "function_calls": rule_calls,
            "total_time_ms": local_time,
            "confidence": max(local_conf, 0.6),
            "source": "on-device",
        }

    # Local has valid schema even if confidence is low — accept
    if schema_ok and sem_ok and local_calls:
        local["source"] = "on-device"
        return local

    # --- Step 4: Cloud fallback ---
    try:
        cloud = generate_cloud(messages, tools)
        cloud["function_calls"] = [_coerce_call_types(c) for c in cloud.get("function_calls", [])]
        cloud["source"] = "cloud (fallback)"
        cloud["local_confidence"] = local_conf
        cloud["total_time_ms"] += local_time
        return cloud
    except Exception:
        best_calls = rule_calls if rule_valid else local_calls if schema_ok else []
        return {
            "function_calls": best_calls,
            "total_time_ms": local_time,
            "confidence": local_conf,
            "source": "on-device",
        }


def print_result(label, result):
    """Pretty-print a generation result."""
    print(f"\n=== {label} ===\n")
    if "source" in result:
        print(f"Source: {result['source']}")
    if "confidence" in result:
        print(f"Confidence: {result['confidence']:.4f}")
    if "local_confidence" in result:
        print(f"Local confidence (below threshold): {result['local_confidence']:.4f}")
    print(f"Total time: {result['total_time_ms']:.2f}ms")
    for call in result["function_calls"]:
        print(f"Function: {call['name']}")
        print(f"Arguments: {json.dumps(call['arguments'], indent=2)}")


############## Example usage ##############

if __name__ == "__main__":
    tools = [
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name",
                    }
                },
                "required": ["location"],
            },
        }
    ]

    messages = [{"role": "user", "content": "What is the weather in San Francisco?"}]

    on_device = generate_cactus(messages, tools)
    print_result("FunctionGemma (On-Device Cactus)", on_device)

    cloud = generate_cloud(messages, tools)
    print_result("Gemini (Cloud)", cloud)

    hybrid = generate_hybrid(messages, tools)
    print_result("Hybrid (On-Device + Cloud Fallback)", hybrid)