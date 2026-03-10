import { useState, useRef, useEffect } from "react";

// ─── tiny helper to call your Python API ───────────────────────────────────
async function sendMessage(userMessage, chatHistory) {
  const response = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userMessage, history: chatHistory }),
  });
  if (!response.ok) throw new Error("Server error – is the Python API running?");
  const data = await response.json();
  return data.response;
}

// ─── individual chat bubble ─────────────────────────────────────────────────
function ChatBubble({ role, text, animate }) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "18px",
        animation: animate ? "fadeSlideIn 0.35s ease forwards" : "none",
        opacity: animate ? 0 : 1,
      }}
    >
      {!isUser && (
        <div style={styles.avatar}>
          <span style={{ fontSize: "18px" }}>🧵</span>
        </div>
      )}
      <div
        style={{
          ...styles.bubble,
          ...(isUser ? styles.userBubble : styles.botBubble),
        }}
      >
        <p style={{ margin: 0, lineHeight: 1.6, fontSize: "15px" }}>{text}</p>
      </div>
      {isUser && (
        <div style={{ ...styles.avatar, background: "#2d2d2d", marginLeft: "10px", marginRight: 0 }}>
          <span style={{ fontSize: "16px" }}>👤</span>
        </div>
      )}
    </div>
  );
}

// ─── typing indicator ───────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: "18px" }}>
      <div style={styles.avatar}><span style={{ fontSize: "18px" }}>🧵</span></div>
      <div style={{ ...styles.bubble, ...styles.botBubble, padding: "14px 20px" }}>
        <div style={styles.dotRow}>
          <span style={{ ...styles.dot, animationDelay: "0s" }} />
          <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
          <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
        </div>
      </div>
    </div>
  );
}

// ─── main app ───────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! Welcome to StyleThread 👗 I'm your personal fashion assistant. Ask me anything about our collection, sizing, fabrics, or styling tips!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", text, animate: true };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError("");
    setLoading(true);

    // build history for the API (exclude the newest user message, API adds it)
    const history = messages.map((m) => ({ role: m.role, content: m.text }));

    try {
      const reply = await sendMessage(text, history);
      setMessages((prev) => [...prev, { role: "assistant", text: reply, animate: true }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* ── global styles injected once ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'DM Sans', sans-serif;
          background: #f5f0eb;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes blink {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
          40%            { transform: scale(1);   opacity: 1;   }
        }

        textarea:focus { outline: none; }
        textarea { resize: none; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #c9b9a8; border-radius: 10px; }
      `}</style>

      <div style={styles.shell}>
        {/* ── header ── */}
        <div style={styles.header}>
          <div>
            <h1 style={styles.logo}>StyleThread</h1>
            <p style={styles.tagline}>Fashion Assistant</p>
          </div>
          <div style={styles.statusBadge}>
            <span style={styles.statusDot} /> M Rabi
          </div>
        </div>

        {/* ── message area ── */}
        <div style={styles.messageArea}>
          {messages.map((m, i) => (
            <ChatBubble key={i} role={m.role} text={m.text} animate={!!m.animate} />
          ))}
          {loading && <TypingIndicator />}
          {error && (
            <p style={styles.errorMsg}>⚠️ {error}</p>
          )}
          <div ref={bottomRef} />
        </div>

        {/* ── input bar ── */}
        <div style={styles.inputBar}>
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about dresses, sizing, fabrics…"
            style={styles.textarea}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              ...styles.sendBtn,
              ...(loading || !input.trim() ? styles.sendBtnDisabled : {}),
            }}
          >
            {loading ? "…" : "Send ↑"}
          </button>
        </div>

        <p style={styles.hint}>Press Enter to send · Shift+Enter for new line</p>
      </div>
    </>
  );
}

// ─── styles object ──────────────────────────────────────────────────────────
const styles = {
  shell: {
    width: "min(740px, 96vw)",
    height: "min(820px, 95vh)",
    background: "#fff8f3",
    borderRadius: "24px",
    boxShadow: "0 24px 80px rgba(0,0,0,0.12)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    border: "1px solid #e8ddd4",
  },
  header: {
    padding: "22px 28px",
    borderBottom: "1px solid #ede4d8",
    background: "linear-gradient(135deg, #2d2d2d 0%, #4a3728 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  logo: {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: "26px",
    fontWeight: 600,
    color: "#f5e6d3",
    letterSpacing: "1.5px",
  },
  tagline: {
    fontSize: "12px",
    color: "#a08878",
    letterSpacing: "0.5px",
    marginTop: "2px",
  },
  statusBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.15)",
    borderRadius: "20px",
    padding: "5px 12px",
    fontSize: "12px",
    color: "#c8b8a8",
  },
  statusDot: {
    display: "inline-block",
    width: "7px",
    height: "7px",
    background: "#5dce8f",
    borderRadius: "50%",
    boxShadow: "0 0 6px #5dce8f",
  },
  messageArea: {
    flex: 1,
    overflowY: "auto",
    padding: "28px 24px 12px",
  },
  avatar: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    background: "#f0e4d4",
    border: "1px solid #ddd0c4",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginRight: "10px",
    alignSelf: "flex-end",
  },
  bubble: {
    maxWidth: "72%",
    padding: "14px 18px",
    borderRadius: "18px",
    wordBreak: "break-word",
  },
  userBubble: {
    background: "linear-gradient(135deg, #2d2d2d, #4a3728)",
    color: "#f5e6d3",
    borderBottomRightRadius: "4px",
  },
  botBubble: {
    background: "#fff",
    color: "#2d2d2d",
    border: "1px solid #e8ddd4",
    borderBottomLeftRadius: "4px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
  },
  dotRow: {
    display: "flex",
    gap: "5px",
    alignItems: "center",
  },
  dot: {
    display: "inline-block",
    width: "8px",
    height: "8px",
    background: "#a08878",
    borderRadius: "50%",
    animation: "blink 1.2s infinite ease-in-out",
  },
  inputBar: {
    display: "flex",
    gap: "10px",
    padding: "16px 20px",
    borderTop: "1px solid #ede4d8",
    background: "#fff",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    padding: "12px 16px",
    fontFamily: "'DM Sans', sans-serif",
    fontSize: "15px",
    background: "#f5f0eb",
    border: "1px solid #ddd0c4",
    borderRadius: "14px",
    color: "#2d2d2d",
    lineHeight: 1.5,
    maxHeight: "120px",
    overflowY: "auto",
  },
  sendBtn: {
    padding: "12px 22px",
    background: "linear-gradient(135deg, #2d2d2d, #4a3728)",
    color: "#f5e6d3",
    border: "none",
    borderRadius: "14px",
    fontSize: "14px",
    fontFamily: "'DM Sans', sans-serif",
    fontWeight: 500,
    cursor: "pointer",
    letterSpacing: "0.5px",
    transition: "opacity 0.2s",
    whiteSpace: "nowrap",
  },
  sendBtnDisabled: {
    opacity: 0.45,
    cursor: "not-allowed",
  },
  errorMsg: {
    color: "#c0392b",
    fontSize: "13px",
    textAlign: "center",
    margin: "8px 0",
    padding: "8px 16px",
    background: "#fdf0ee",
    borderRadius: "8px",
    border: "1px solid #f5c6c1",
  },
  hint: {
    textAlign: "center",
    fontSize: "11px",
    color: "#b0a090",
    padding: "6px 0 10px",
    background: "#fff",
  },
};