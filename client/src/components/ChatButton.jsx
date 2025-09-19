// simple floating WhatsApp-like chat widget
import React, { useState, useEffect } from "react";

export default function ChatButton({ apiBase = "/api" }) {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userText = input.trim();
    setMsgs(m => [...m, { from: "user", text: userText }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(apiBase + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": "local-dev-key" },
        body: JSON.stringify({ query: userText })
      });
      const j = await res.json();
      const answer = j.answer?.text || (j.answer && j.answer['text']) || JSON.stringify(j);
      setMsgs(m => [...m, { from: "bot", text: answer }]);
    } catch (e) {
      setMsgs(m => [...m, { from: "bot", text: "Error contacting assistant." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ position: "fixed", right: 20, bottom: 20, zIndex: 9999 }}>
      {open && (
        <div style={{ width: 360, height: 480, background: "#fff", boxShadow: "0 8px 32px rgba(0,0,0,0.15)", borderRadius: 8, display: "flex", flexDirection: "column" }}>
          <div style={{ padding: 8, background: "#075E54", color: "#fff", borderTopLeftRadius: 8, borderTopRightRadius: 8 }}>
            TheFool Assistant
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 8 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ textAlign: m.from === "user" ? "right" : "left", margin: "6px 0" }}>
                <div style={{ display: "inline-block", padding: 8, borderRadius: 6, background: m.from === "user" ? "#DCF8C6" : "#F1F0F0", maxWidth: "86%" }}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", padding: 8 }}>
            <input style={{ flex: 1, padding: 8 }} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
            <button onClick={send} style={{ marginLeft: 8 }} disabled={loading}>{loading ? "..." : "Send"}</button>
          </div>
        </div>
      )}
      <button onClick={() => setOpen(o => !o)} style={{ width: 64, height: 64, borderRadius: 32, background: "#25D366", color: "#fff", fontSize: 20, border: "none" }}>
        💬
      </button>
    </div>
  );
}
