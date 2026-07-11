from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import datetime
import uuid
import os
import random
import re
import json

app = Flask(__name__)
CORS(app)

# ── Database ──────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id          TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            intent      TEXT,
            confidence  REAL,
            timestamp   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_interaction(session_id, user_msg, bot_resp, intent, confidence):
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO interactions VALUES (?,?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()), session_id, user_msg, bot_resp,
        intent, confidence, datetime.datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

# ── NLP / Intent Engine ───────────────────────────────────────────────────────

INTENTS = {
    "greeting": {
        "patterns": [r"\b(hi|hello|hey|howdy|greetings|good\s*(morning|afternoon|evening))\b"],
        "responses": [
            "Hello! 👋 Welcome! How can I assist you today?",
            "Hi there! Great to see you. What can I help with?",
            "Hey! I'm here and ready to help. What's on your mind?"
        ]
    },
    "farewell": {
        "patterns": [r"\b(bye|goodbye|see\s*you|take\s*care|later|ciao|farewell)\b"],
        "responses": [
            "Goodbye! Have a wonderful day! 😊",
            "See you later! Don't hesitate to come back if you need help.",
            "Take care! It was great chatting with you."
        ]
    },
    "thanks": {
        "patterns": [r"\b(thanks|thank\s*you|thx|ty|appreciate|grateful)\b"],
        "responses": [
            "You're very welcome! 😊 Is there anything else I can help with?",
            "Happy to help! Let me know if you need anything else.",
            "Anytime! That's what I'm here for."
        ]
    },
    "hours": {
        "patterns": [r"\b(hours?|open|close|timing|schedule|available|when\s*(are|is|do))\b"],
        "responses": [
            "Our support team is available **Monday–Friday, 9 AM – 6 PM IST**. Outside those hours, I'm always here to help! 🕘",
            "We're open **weekdays from 9 AM to 6 PM IST**. Our AI assistant (that's me!) is available 24/7."
        ]
    },
    "pricing": {
        "patterns": [r"\b(pric(e|ing|es)|cost|fee|pay|plan|subscription|how\s*much|charge)\b"],
        "responses": [
            "We offer three plans:\n• **Starter** – Free, basic features\n• **Pro** – ₹999/month, all features\n• **Enterprise** – Custom pricing\n\nWould you like more details on any plan?",
            "Our pricing is flexible! The **Free** tier gets you started, **Pro** at ₹999/month unlocks everything. For large teams, we offer custom **Enterprise** deals."
        ]
    },
    "refund": {
        "patterns": [r"\b(refund|money\s*back|return|cancel|reimburse)\b"],
        "responses": [
            "We offer a **30-day money-back guarantee** on all paid plans. To initiate a refund, please contact support@example.com with your order ID.",
            "Refunds are processed within **5–7 business days**. Please reach out to our billing team at billing@example.com."
        ]
    },
    "contact": {
        "patterns": [r"\b(contact|reach|email|phone|support|talk\s*(to|with)\s*(human|agent|person|someone))\b"],
        "responses": [
            "You can reach our support team at:\n📧 support@example.com\n📞 +91-98765-43210\n💬 Live chat: Mon–Fri 9 AM–6 PM IST",
            "Need a human? Our agents are available weekdays! Email **support@example.com** or call **+91-98765-43210**."
        ]
    },
    "faq_account": {
        "patterns": [r"\b(account|login|sign\s*(in|up)|password|register|profile|forgot)\b"],
        "responses": [
            "For account issues:\n• **Forgot password?** Click 'Reset Password' on the login page.\n• **Can't log in?** Clear your browser cache and try again.\n• **New account?** Click 'Sign Up' on our homepage.",
            "Having trouble with your account? Try resetting your password first. If the issue persists, contact support@example.com."
        ]
    },
    "faq_technical": {
        "patterns": [r"\b(bug|error|crash|not\s*work(ing)?|broken|issue|problem|glitch|slow)\b"],
        "responses": [
            "Sorry to hear you're experiencing issues! Please try:\n1. Refreshing the page\n2. Clearing browser cache\n3. Trying a different browser\n\nIf it persists, share your error details with support@example.com.",
            "Technical issues can be tricky! Could you describe what's happening? In the meantime, a quick **page refresh** solves most common glitches."
        ]
    },
    "about": {
        "patterns": [r"\b(about|who\s*(are\s*you|is\s*this)|what\s*(are\s*you|is\s*this)|introduce|yourself|bot|ai|chatbot)\b"],
        "responses": [
            "I'm an **AI-powered customer support chatbot** 🤖 built with Python & NLP. I can answer FAQs, help with account issues, pricing, and more. For complex queries, I'll connect you to a human agent.",
            "I'm your virtual assistant! I use Natural Language Processing to understand your questions and provide helpful responses 24/7. What would you like to know?"
        ]
    },
    "help": {
        "patterns": [r"\b(help|assist|support|what\s*can\s*(you|i)|capabilities|features|options|menu)\b"],
        "responses": [
            "I can help you with:\n• 📋 **FAQs** – Common questions\n• 💰 **Pricing** – Plans & costs\n• 🔧 **Technical issues** – Troubleshooting\n• 👤 **Account** – Login & settings\n• 📞 **Contact** – Reach our team\n• ⏰ **Hours** – Support availability\n\nJust ask anything!",
        ]
    }
}

def classify_intent(text):
    text_lower = text.lower().strip()
    best_intent = "unknown"
    best_score = 0

    for intent, data in INTENTS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Rough confidence based on match length
                match = re.search(pattern, text_lower, re.IGNORECASE)
                score = len(match.group()) / max(len(text_lower), 1)
                score = min(0.95, score + 0.55)
                if score > best_score:
                    best_score = score
                    best_intent = intent

    return best_intent, round(best_score, 2)

def generate_response(text):
    intent, confidence = classify_intent(text)
    if intent == "unknown":
        response = (
            "I'm not sure I understand that completely. Could you rephrase? "
            "You can also type **'help'** to see what I can assist with. "
            "For complex queries, type **'contact'** to reach a human agent. 🙏"
        )
        confidence = 0.20
    else:
        response = random.choice(INTENTS[intent]["responses"])
    return response, intent, confidence

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    response, intent, confidence = generate_response(user_message)
    log_interaction(session_id, user_message, response, intent, confidence)

    return jsonify({
        "response": response,
        "intent": intent,
        "confidence": confidence,
        "session_id": session_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

@app.route("/logs")
def logs_page():
    return render_template("logs.html")

@app.route("/stats")
def stats_page():
    return render_template("stats.html")

@app.route("/api/logs", methods=["GET"])
def get_logs():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM interactions ORDER BY timestamp DESC LIMIT 200")
    rows = c.fetchall()
    conn.close()
    cols = ["id","session_id","user_message","bot_response","intent","confidence","timestamp"]
    return jsonify([dict(zip(cols, r)) for r in rows])

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM interactions")
    total = c.fetchone()[0]
    c.execute("SELECT intent, COUNT(*) as cnt FROM interactions GROUP BY intent ORDER BY cnt DESC")
    intents = [{"intent": r[0], "count": r[1]} for r in c.fetchall()]
    c.execute("SELECT AVG(confidence) FROM interactions")
    avg_conf = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(DISTINCT session_id) FROM interactions")
    sessions = c.fetchone()[0]
    c.execute("SELECT DATE(timestamp) as d, COUNT(*) as cnt FROM interactions GROUP BY d ORDER BY d DESC LIMIT 7")
    daily = [{"date": r[0], "count": r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify({
        "total_interactions": total,
        "total_sessions": sessions,
        "intent_distribution": intents,
        "avg_confidence": round(avg_conf, 3),
        "daily_counts": daily
    })

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
