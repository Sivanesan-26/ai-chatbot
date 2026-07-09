# 🤖 NexBot – AI-Powered Customer Support Chatbot

An intelligent chatbot built with **Python NLP**, **Flask**, and **SQLite** for customer support and FAQs.

---

## 📁 Project Structure

```
ai-chatbot/
├── app.py              # Flask backend — NLP engine + REST API
├── requirements.txt    # Python dependencies
├── chatbot.db          # SQLite DB (auto-created on first run)
└── templates/
    └── index.html      # Frontend UI
```

---

## ⚙️ Setup & Run

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

---

## 🧠 Technologies Used

| Layer       | Technology                          |
|-------------|-------------------------------------|
| **NLP**     | Python regex-based intent classifier (extendable to NLTK/Transformers) |
| **Backend** | Flask + Flask-CORS                  |
| **Database**| SQLite (interaction logs)           |
| **Frontend**| Vanilla JS + CSS (no frameworks)   |

---

## 🔌 API Endpoints

| Method | Endpoint      | Description                     |
|--------|---------------|---------------------------------|
| `GET`  | `/`           | Chat UI                         |
| `POST` | `/api/chat`   | Send message, get response      |
| `GET`  | `/api/logs`   | View interaction logs (JSON)    |
| `GET`  | `/api/stats`  | Analytics: counts, intents, confidence |

### POST `/api/chat`
**Request:**
```json
{
  "message": "What are your pricing plans?",
  "session_id": "optional-uuid"
}
```
**Response:**
```json
{
  "response": "We offer three plans...",
  "intent": "pricing",
  "confidence": 0.85,
  "session_id": "abc-123",
  "timestamp": "2026-06-08T12:34:56"
}
```

---

## 🤖 Supported Intents

| Intent          | Example Queries                          |
|-----------------|------------------------------------------|
| `greeting`      | "Hi", "Hello", "Good morning"           |
| `farewell`      | "Bye", "Goodbye", "See you"             |
| `thanks`        | "Thank you", "Thanks a lot"             |
| `pricing`       | "How much?", "What are the plans?"      |
| `hours`         | "When are you open?", "Working hours"   |
| `refund`        | "I want a refund", "Money back"         |
| `contact`       | "Talk to a human", "Support email"      |
| `faq_account`   | "Forgot password", "Can't login"        |
| `faq_technical` | "Bug", "App not working", "Error"       |
| `about`         | "Who are you?", "What is this bot?"     |
| `help`          | "What can you do?", "Help"              |

---

## 🗄️ Database Schema

```sql
CREATE TABLE interactions (
    id           TEXT PRIMARY KEY,    -- UUID
    session_id   TEXT NOT NULL,       -- Browser session
    user_message TEXT NOT NULL,       -- What user typed
    bot_response TEXT NOT NULL,       -- What bot replied
    intent       TEXT,                -- Classified intent
    confidence   REAL,                -- Confidence score (0–1)
    timestamp    TEXT NOT NULL        -- ISO 8601 UTC
);
```

---

## 🚀 Extending with Transformers

To upgrade to a full transformer-based NLP model, replace `classify_intent()` in `app.py`:

```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_intent(text):
    candidate_labels = list(INTENTS.keys())
    result = classifier(text, candidate_labels)
    intent = result['labels'][0]
    confidence = result['scores'][0]
    return intent, round(confidence, 2)
```

---

## 📊 Outcome

- ✅ Contextual responses via NLP intent classification
- ✅ Full interaction logging in SQLite
- ✅ REST API with confidence scores
- ✅ Real-time analytics dashboard
- ✅ Session tracking per user

---

## 👤 Author
Built as part of an AI/ML internship project.
