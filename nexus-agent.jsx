import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

const TOOL_META = {
  get_weather: { icon: "🌤", label: "Weather" },
  set_alarm: { icon: "⏰", label: "Alarm" },
  send_message: { icon: "💬", label: "Message" },
  create_reminder: { icon: "📌", label: "Reminder" },
  search_contacts: { icon: "👤", label: "Contacts" },
  play_music: { icon: "🎵", label: "Music" },
  set_timer: { icon: "⏱", label: "Timer" },
  create_note: { icon: "📝", label: "Note" },
  add_calendar: { icon: "📅", label: "Calendar" },
  translate: { icon: "🌐", label: "Translate" },
};

async function callHybridAPI(message) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("API unavailable, using local simulation:", err.message);
    return simulateFallback(message);
  }
}

function simulateFallback(text) {
  const lower = text.toLowerCase();
  const calls = [];
  let source = "on-device";
  let confidence = 0.95;
  let latency = Math.floor(Math.random() * 200) + 80;
  const clauses = text.split(/\s*,\s*(?:and\s+)?|\s+\band\b\s+|\s+\bthen\b\s+/).filter(Boolean);
  for (const clause of clauses) {
    const cl = clause.toLowerCase().trim();
    if (/weather|temperature|forecast|umbrella/.test(cl)) {
      const loc = cl.match(/(?:in|for|at)\s+([a-z\s]+)/i);
      calls.push({ name: "get_weather", arguments: { location: loc ? loc[1].trim() : "current location" } });
    } else if (/alarm|wake.*up/.test(cl)) {
      const t = cl.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)/i);
      if (t) { let h = parseInt(t[1]); const m = parseInt(t[2] || "0"); if (t[3].toLowerCase() === "pm" && h !== 12) h += 12; if (t[3].toLowerCase() === "am" && h === 12) h = 0; calls.push({ name: "set_alarm", arguments: { hour: h, minute: m } }); }
    } else if (/timer|countdown/.test(cl)) {
      const m = cl.match(/(\d+)\s*(?:min|minute)/i);
      if (m) calls.push({ name: "set_timer", arguments: { minutes: parseInt(m[1]) } });
    } else if (/(?:send|text|message)\b/.test(cl)) {
      const msg = cl.match(/(?:send|text|message)\s+(?:a\s+message\s+to\s+)?(\w+)\s+(?:saying|that)\s+(.+)/i);
      if (msg) calls.push({ name: "send_message", arguments: { recipient: msg[1], message: msg[2].trim() } });
    } else if (/remind/.test(cl)) {
      const rem = cl.match(/remind\s+me\s+(?:to\s+)?(.+?)\s+(?:at|by)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))/i);
      if (rem) calls.push({ name: "create_reminder", arguments: { title: rem[1], time: rem[2] } });
    } else if (/play\b/.test(cl)) {
      const song = cl.replace(/^.*\bplay\s+/i, "").replace(/^(some|a|the|me)\s+/i, "").trim();
      if (song) calls.push({ name: "play_music", arguments: { song } });
    } else if (/(?:find|look.*up|search).*contact/.test(cl)) {
      const n = cl.match(/(?:find|look.*up|search)\s+(\w+)/i);
      if (n) calls.push({ name: "search_contacts", arguments: { query: n[1] } });
    } else {
      source = "cloud (fallback)";
      confidence = 0.88;
      latency += Math.floor(Math.random() * 800) + 400;
    }
  }
  return {
    function_calls: calls,
    source,
    confidence,
    total_time_ms: latency,
    message: calls.length === 0 ? "I'm not sure how to help with that." : calls.length === 1 ? "Done! Action executed." : `Got it! ${calls.length} actions handled.`,
  };
}

function ToolBadge({ call }) {
  const meta = TOOL_META[call.name] || { icon: "⚙️", label: call.name };
  return (
    <div style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, padding: "10px 14px", marginTop: 6, fontSize: 13 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 16 }}>{meta.icon}</span>
        <span style={{ fontWeight: 600, color: "#a8e6cf", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, letterSpacing: "0.5px" }}>{call.name}()</span>
      </div>
      <div style={{ paddingLeft: 24 }}>
        {Object.entries(call.arguments || {}).map(([k, v]) => (
          <div key={k} style={{ color: "rgba(255,255,255,0.6)", fontSize: 12, lineHeight: 1.6, fontFamily: "'JetBrains Mono', monospace" }}>
            <span style={{ color: "#ffd3a8" }}>{k}</span>
            <span style={{ color: "rgba(255,255,255,0.3)" }}>: </span>
            <span style={{ color: "rgba(255,255,255,0.85)" }}>{JSON.stringify(v)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RoutingIndicator({ source, confidence, latency }) {
  const isOnDevice = source === "on-device";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8, padding: "6px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 5, background: isOnDevice ? "rgba(168,230,207,0.12)" : "rgba(168,200,255,0.12)", border: `1px solid ${isOnDevice ? "rgba(168,230,207,0.3)" : "rgba(168,200,255,0.3)"}`, borderRadius: 20, padding: "3px 10px", fontSize: 11, fontWeight: 500, color: isOnDevice ? "#a8e6cf" : "#a8c8ff" }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: isOnDevice ? "#a8e6cf" : "#a8c8ff", display: "inline-block" }} />
        {isOnDevice ? "On-Device" : "Cloud"}
      </div>
      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", fontFamily: "'JetBrains Mono', monospace" }}>
        {Math.round(latency)}ms · {(confidence * 100).toFixed(0)}% conf
      </span>
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 16, animation: "fadeSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1)" }}>
      <div style={{ maxWidth: "82%", padding: isUser ? "12px 18px" : "14px 18px", borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px", background: isUser ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" : "rgba(255,255,255,0.04)", border: isUser ? "none" : "1px solid rgba(255,255,255,0.08)", color: "#fff", fontSize: 14, lineHeight: 1.6 }}>
        {isUser ? <span>{msg.text}</span> : (
          <div>
            <div style={{ marginBottom: msg.calls?.length ? 8 : 0 }}>{msg.text}</div>
            {msg.calls?.map((call, i) => <ToolBadge key={i} call={call} />)}
            {msg.routing && <RoutingIndicator source={msg.routing.source} confidence={msg.routing.confidence} latency={msg.routing.latency} />}
          </div>
        )}
      </div>
    </div>
  );
}

const SUGGESTIONS = [
  "Set an alarm for 7 AM",
  "What's the weather in Tokyo?",
  "Text Alice saying I'm on my way",
  "Remind me to call the dentist at 3 PM",
  "Play some jazz and check the weather in Paris",
  "Set a 10 min timer, remind me to stretch at 5 PM, and play lo-fi beats",
];

export default function NexusAgent() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hey! I'm Nexus — your personal productivity agent powered by hybrid edge-cloud AI. I route simple commands through an on-device 270M model for instant responses, and use cloud AI for complex tasks. Try me out!" },
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiConnected, setApiConnected] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  // Check API on mount
  useEffect(() => {
    fetch(`${API_BASE}/`)
      .then((r) => r.ok ? setApiConnected(true) : setApiConnected(false))
      .catch(() => setApiConnected(false));
  }, []);

  const handleSend = async (text) => {
    const msg = text || input;
    if (!msg.trim() || isProcessing) return;
    setInput("");
    setIsProcessing(true);
    setMessages((prev) => [...prev, { role: "user", text: msg }]);

    const result = await callHybridAPI(msg);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: result.message,
        calls: result.function_calls,
        routing: { source: result.source, confidence: result.confidence || 0, latency: result.total_time_ms },
      },
    ]);
    setIsProcessing(false);
    inputRef.current?.focus();
  };

  const stats = messages.filter((m) => m.routing);
  const onDevice = stats.filter((m) => m.routing?.source === "on-device").length;
  const cloud = stats.length - onDevice;
  const avgLatency = stats.length > 0 ? Math.round(stats.reduce((a, m) => a + (m.routing?.latency || 0), 0) / stats.length) : 0;

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0f", fontFamily: "'Instrument Sans', 'SF Pro Display', -apple-system, sans-serif", color: "#fff", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes fadeSlideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        input::placeholder { color: rgba(255,255,255,0.3); }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(20px)", background: "rgba(10,10,15,0.8)", position: "sticky", top: 0, zIndex: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #667eea, #764ba2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>⚡</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.3px" }}>Nexus Agent</div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", letterSpacing: "0.5px", textTransform: "uppercase", fontWeight: 500, display: "flex", alignItems: "center", gap: 6 }}>
              Hybrid Edge-Cloud AI
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: apiConnected === true ? "#4ade80" : apiConnected === false ? "#f87171" : "#fbbf24", display: "inline-block" }} />
              <span style={{ fontSize: 10, textTransform: "none" }}>{apiConnected === true ? "API Live" : apiConnected === false ? "Demo Mode" : "Connecting..."}</span>
            </div>
          </div>
        </div>
        {stats.length > 0 && (
          <div style={{ display: "flex", gap: 16, fontSize: 11, color: "rgba(255,255,255,0.4)", fontFamily: "'JetBrains Mono', monospace" }}>
            <span><span style={{ color: "#a8e6cf" }}>●</span> {onDevice} local</span>
            <span><span style={{ color: "#a8c8ff" }}>●</span> {cloud} cloud</span>
            <span>avg {avgLatency}ms</span>
          </div>
        )}
      </div>

      {/* Chat */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 24px 120px", maxWidth: 720, width: "100%", margin: "0 auto" }}>
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {isProcessing && (
          <div style={{ display: "flex", gap: 6, padding: "12px 18px", animation: "fadeSlideUp 0.3s ease" }}>
            {[0, 1, 2].map((i) => (
              <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#667eea", animation: `pulse 1.2s ease infinite ${i * 0.2}s` }} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
        {messages.length <= 1 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 20, animation: "fadeSlideUp 0.5s ease 0.3s both" }}>
            {SUGGESTIONS.map((s, i) => (
              <button key={i} onClick={() => handleSend(s)} style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 20, padding: "8px 16px", color: "rgba(255,255,255,0.7)", fontSize: 13, cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit" }}
                onMouseEnter={(e) => { e.target.style.background = "rgba(255,255,255,0.08)"; e.target.style.borderColor = "rgba(102,126,234,0.4)"; e.target.style.color = "#fff"; }}
                onMouseLeave={(e) => { e.target.style.background = "rgba(255,255,255,0.04)"; e.target.style.borderColor = "rgba(255,255,255,0.1)"; e.target.style.color = "rgba(255,255,255,0.7)"; }}>
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, padding: "16px 24px 24px", background: "linear-gradient(transparent, rgba(10,10,15,0.95) 30%, #0a0a0f)" }}>
        <div style={{ maxWidth: 720, margin: "0 auto", display: "flex", gap: 10, alignItems: "center" }}>
          <input ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Try: Set an alarm for 7 AM and remind me to exercise..."
            disabled={isProcessing}
            style={{ flex: 1, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 14, padding: "14px 18px", color: "#fff", fontSize: 14, outline: "none", fontFamily: "inherit", transition: "border-color 0.2s" }}
            onFocus={(e) => (e.target.style.borderColor = "rgba(102,126,234,0.5)")}
            onBlur={(e) => (e.target.style.borderColor = "rgba(255,255,255,0.1)")} />
          <button onClick={() => handleSend()} disabled={isProcessing || !input.trim()}
            style={{ width: 46, height: 46, borderRadius: 14, border: "none", background: input.trim() && !isProcessing ? "linear-gradient(135deg, #667eea, #764ba2)" : "rgba(255,255,255,0.06)", color: "#fff", fontSize: 18, cursor: input.trim() && !isProcessing ? "pointer" : "not-allowed", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s", flexShrink: 0 }}>
            ↑
          </button>
        </div>
        <div style={{ textAlign: "center", fontSize: 10, color: "rgba(255,255,255,0.2)", marginTop: 8, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.5px" }}>
          Powered by FunctionGemma 270M × Gemini 2.0 Flash · Hybrid Edge-Cloud Routing
        </div>
      </div>
    </div>
  );
}
