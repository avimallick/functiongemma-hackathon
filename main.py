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


# ==================== ENHANCED SYSTEM PROMPTS ====================

SYSTEM_PROMPT_V1 = (
    "You are a function-calling assistant. "
    "Analyze the user request and call the appropriate tool(s). "
    "For each action in the request, make exactly one function call. "
    "Use only the tools provided. Fill all required arguments with values from the user message."
)

SYSTEM_PROMPT_V2 = (
    "You are a precise tool-calling AI. "
    "Read the user message carefully. Identify every distinct action requested. "
    "For each action, select the single best matching tool and extract argument values directly from the message. "
    "Do not invent values. Do not skip any requested action."
)


def _run_cactus(messages, tools, system_prompt=SYSTEM_PROMPT_V1):
    """Run function calling on-device with a custom system prompt."""
    model = _get_cactus_model()

    cactus_tools = [{"type": "function", "function": t} for t in tools]

    raw_str = cactus_complete(
        model,
        [{"role": "system", "content": system_prompt}] + messages,
        tools=cactus_tools,
        force_tools=True,
        max_tokens=256,
        stop_sequences=["<|im_end|>", "<end_of_turn>"],
    )

    try:
        raw = json.loads(raw_str)
    except json.JSONDecodeError:
        return {"function_calls": [], "total_time_ms": 0, "confidence": 0}

    return {
        "function_calls": raw.get("function_calls", []),
        "total_time_ms": raw.get("total_time_ms", 0),
        "confidence": raw.get("confidence", 0),
    }


# Keep original name for backward compatibility with benchmark.py
def generate_cactus(messages, tools):
    """Run function calling on-device via FunctionGemma + Cactus."""
    return _run_cactus(messages, tools, SYSTEM_PROMPT_V1)


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
    system_instruction = (
        "You are a function-calling assistant. "
        "Return all needed function calls for the user request. "
        "Make one call per distinct action."
    )

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


# ==================== VALIDATION HELPERS (tool-agnostic) ====================

def _coerce_args(call, tool_map):
    """Fix type mismatches in arguments based on tool schema."""
    name = call.get("name")
    args = call.get("arguments", {})
    if not isinstance(args, dict):
        args = {}
    out = {"name": name, "arguments": dict(args)}
    tool = tool_map.get(name)
    if not tool:
        return out
    props = tool.get("parameters", {}).get("properties", {})
    for key, val in list(out["arguments"].items()):
        if key not in props:
            continue
        ptype = props[key].get("type", "").lower()
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


def _is_schema_valid(call, tool_map):
    """Check if call has valid name, required params, and correct types."""
    name = call.get("name")
    args = call.get("arguments", {})
    if name not in tool_map or not isinstance(args, dict):
        return False
    tool = tool_map[name]
    required = tool.get("parameters", {}).get("required", [])
    props = tool.get("parameters", {}).get("properties", {})
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


def _is_semantically_valid(call):
    """Domain-agnostic sanity checks on argument values."""
    args = call.get("arguments", {})
    for key, val in args.items():
        if isinstance(val, str) and not val.strip():
            return False
        if isinstance(val, int) and val < 0:
            return False
    return True


def _args_grounded_in_text(call, user_text_l, user_tokens):
    """Check if argument values appear in or relate to the user message."""
    args = call.get("arguments", {})
    if not args:
        return 0.0
    hits = 0.0
    total = 0
    for val in args.values():
        if isinstance(val, str):
            total += 1
            val_l = val.strip().lower()
            if not val_l:
                continue
            if val_l in user_text_l:
                hits += 1.0
                continue
            val_tokens = set(re.findall(r"[a-z0-9]+", val_l))
            if val_tokens:
                overlap = len(val_tokens & user_tokens) / len(val_tokens)
                hits += overlap
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            total += 1
            if str(int(val)) in user_text_l:
                hits += 1.0
    return hits / max(1, total)


def _tool_relevance(tool_name, tool_map, user_tokens):
    """How relevant is this tool to the user's message based on token overlap."""
    tool = tool_map.get(tool_name)
    if not tool:
        return 0.0
    parts = [tool.get("name", ""), tool.get("description", "")]
    for p in tool.get("parameters", {}).get("properties", {}).values():
        if isinstance(p, dict):
            parts.append(p.get("description", ""))
    raw = " ".join(parts).replace("_", " ").lower()
    tool_tokens = {t for t in re.findall(r"[a-z0-9]+", raw) if len(t) > 2}
    if not tool_tokens:
        return 0.0
    return len(tool_tokens & user_tokens) / len(tool_tokens)


def _estimate_action_count(text):
    """Estimate how many distinct actions the user is requesting."""
    separators = re.findall(r"\b(?:and|then|also|plus)\b|,", text.lower())
    return max(1, min(5, len(separators) + 1))


def _score_candidate(calls, tool_map, user_text_l, user_tokens, confidence):
    """Score a set of function calls for overall quality."""
    if not calls:
        return {"valid": False, "score": 0.0, "mean_call_score": 0.0}

    call_scores = []
    for c in calls:
        schema_ok = _is_schema_valid(c, tool_map)
        sem_ok = _is_semantically_valid(c)
        grounding = _args_grounded_in_text(c, user_text_l, user_tokens)
        relevance = _tool_relevance(c.get("name"), tool_map, user_tokens)

        score = 0.0
        if schema_ok and sem_ok:
            score = 0.40 * grounding + 0.30 * relevance + 0.30 * 1.0
        call_scores.append(score)

    all_valid = all(
        _is_schema_valid(c, tool_map) and _is_semantically_valid(c) for c in calls
    )
    mean_score = sum(call_scores) / len(call_scores)
    overall = 0.50 * mean_score + 0.35 * confidence + 0.15 * (1.0 if all_valid else 0.0)

    return {
        "valid": all_valid,
        "score": overall,
        "mean_call_score": mean_score,
    }


def _dedupe_calls(calls):
    """Remove duplicate function calls."""
    seen = set()
    out = []
    for c in calls:
        key = json.dumps({"name": c.get("name"), "arguments": c.get("arguments", {})}, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


# ==================== HYBRID STRATEGY ====================

def generate_hybrid(messages, tools, confidence_threshold=0.99):
    """
    Hybrid strategy: prompt engineering + double-pass + smart cloud routing.
    No regex. Fully tool-agnostic.

    Flow:
      1. Run local model with enhanced prompt V1
      2. Validate output (schema, grounding, relevance)
      3. If uncertain, run local model again with prompt V2 (double-pass)
      4. Pick the better local result
      5. If best local result passes quality bar -> on-device
      6. Otherwise -> cloud fallback
    """
    user_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
    user_text_l = user_text.lower()
    user_tokens = set(re.findall(r"[a-z0-9]+", user_text_l))
    tool_map = {t["name"]: t for t in tools}
    action_count = _estimate_action_count(user_text)
    num_tools = len(tools)

    # --- Pass 1: Run local with prompt V1 ---
    local1 = _run_cactus(messages, tools, SYSTEM_PROMPT_V1)
    calls1 = [_coerce_args(c, tool_map) for c in local1.get("function_calls", [])]
    calls1 = [c for c in calls1 if c.get("name") in tool_map]
    calls1 = _dedupe_calls(calls1)
    conf1 = float(local1.get("confidence", 0.0) or 0.0)
    eval1 = _score_candidate(calls1, tool_map, user_text_l, user_tokens, conf1)

    time_spent = local1.get("total_time_ms", 0)

    # --- Quick accept: single tool, high confidence, valid output ---
    if num_tools == 1 and eval1["valid"] and conf1 >= 0.5 and len(calls1) >= 1:
        local1["function_calls"] = calls1
        local1["source"] = "on-device"
        return local1

    # --- Accept pass 1 if good enough ---
    accept_threshold = 0.40 if action_count == 1 else 0.50
    if eval1["valid"] and eval1["score"] >= accept_threshold and len(calls1) >= action_count:
        local1["function_calls"] = calls1
        local1["source"] = "on-device"
        return local1

    # --- Pass 2: Try with different prompt ---
    local2 = _run_cactus(messages, tools, SYSTEM_PROMPT_V2)
    calls2 = [_coerce_args(c, tool_map) for c in local2.get("function_calls", [])]
    calls2 = [c for c in calls2 if c.get("name") in tool_map]
    calls2 = _dedupe_calls(calls2)
    conf2 = float(local2.get("confidence", 0.0) or 0.0)
    eval2 = _score_candidate(calls2, tool_map, user_text_l, user_tokens, conf2)

    time_spent += local2.get("total_time_ms", 0)

    # Pick the better local result
    if eval2["score"] > eval1["score"]:
        best_calls, best_eval, best_conf = calls2, eval2, conf2
    else:
        best_calls, best_eval, best_conf = calls1, eval1, conf1

    # --- Agreement check: both passes agree on tool names -> higher trust ---
    names1 = {c.get("name") for c in calls1}
    names2 = {c.get("name") for c in calls2}
    passes_agree = names1 == names2 and len(names1) > 0

    if best_eval["valid"] and len(best_calls) >= action_count:
        if passes_agree and best_conf >= 0.30:
            return {
                "function_calls": best_calls,
                "total_time_ms": time_spent,
                "confidence": best_conf,
                "source": "on-device",
            }
        if best_eval["score"] >= accept_threshold and best_conf >= 0.40:
            return {
                "function_calls": best_calls,
                "total_time_ms": time_spent,
                "confidence": best_conf,
                "source": "on-device",
            }

    # --- Last chance: any valid single pass with decent confidence ---
    # Only accept if call count matches expected action count
    for calls, eval_r, conf in [(calls1, eval1, conf1), (calls2, eval2, conf2)]:
        if eval_r["valid"] and conf >= 0.45 and len(calls) >= action_count:
            return {
                "function_calls": calls,
                "total_time_ms": time_spent,
                "confidence": conf,
                "source": "on-device",
            }

    # --- Cloud fallback ---
    try:
        cloud = generate_cloud(messages, tools)
        cloud_calls = [_coerce_args(c, tool_map) for c in cloud.get("function_calls", [])]
        cloud["function_calls"] = [c for c in cloud_calls if c.get("name") in tool_map]
        cloud["source"] = "cloud (fallback)"
        cloud["local_confidence"] = best_conf
        cloud["total_time_ms"] += time_spent
        return cloud
    except Exception:
        return {
            "function_calls": best_calls if best_eval["valid"] else calls1,
            "total_time_ms": time_spent,
            "confidence": best_conf,
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