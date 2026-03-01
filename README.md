# 🇮🇳 NagrikSeva AI

**AI-powered citizen grievance redressal system for India.**

Citizens call a phone number → an AI agent converses in **Hindi/English/Hinglish** → collects their complaint → issues a ticket → sends **WhatsApp confirmation**. Administrators monitor everything via a real-time **Streamlit dashboard**.

> 💰 **Entire stack is free** — built on free tiers and Twilio trial credit ($15).

---

## ✨ Features

- 📞 **Inbound AI Calls** — Gemini 1.5 Flash picks up, speaks naturally, collects grievance details
- 🗣️ **Trilingual** — Hindi, English, Hinglish — auto-detects and adapts
- 🎫 **Ticket System** — Auto-generates `NS-YYYYMMDD-XXXX` ticket IDs
- 📱 **WhatsApp Confirmations** — Instant ticket confirmation + status lookup
- 📊 **Admin Dashboard** — Real-time analytics, live feed, outbound campaign control
- 📤 **Outbound Campaigns** — Auto-call citizens with status updates on stale grievances

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Citizen    │────▶│   Twilio     │────▶│  FastAPI Server  │
│ (Phone Call) │◀────│   Voice      │◀────│  (main.py)       │
└──────────────┘     └─────────────┘     └────────┬─────────┘
                                                   │
                     ┌─────────────┐     ┌─────────▼────────┐
                     │  WhatsApp   │◀────│   Gemini 1.5     │
                     │  (Twilio)   │     │   Flash AI       │
                     └─────────────┘     └─────────┬────────┘
                                                   │
                     ┌─────────────┐     ┌─────────▼────────┐
                     │  Streamlit  │────▶│  MongoDB Atlas   │
                     │  Dashboard  │◀────│  (Free M0)       │
                     └─────────────┘     └──────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Backend | FastAPI (Python) | Free |
| Voice Calls | Twilio Voice | Free trial ($15) |
| AI Brain | Google Gemini 1.5 Flash | Free API |
| Database | MongoDB Atlas M0 | Free (512 MB) |
| WhatsApp | Twilio WhatsApp Sandbox | Free trial |
| Dashboard | Streamlit + Plotly | Free |
| Tunnel | Ngrok | Free |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/AstaadDahiya/NagrikSeva-AI.git
cd NagrikSeva-AI/nagrikseva
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get API Keys (All Free)

| Service | Where to get it |
|---------|----------------|
| **Gemini API Key** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **MongoDB Atlas** | [cloud.mongodb.com](https://cloud.mongodb.com) → Free M0 cluster |
| **Twilio** | [twilio.com/try-twilio](https://www.twilio.com/try-twilio) → Get SID, Token, Phone Number |
| **Ngrok** | [ngrok.com](https://ngrok.com) → Install & auth |

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Start Ngrok

```bash
ngrok http 8000
# Copy the https URL to .env as BASE_URL
```

### 5. Configure Twilio Webhooks

In [Twilio Console](https://console.twilio.com), set your phone number's webhooks:

| Webhook | URL |
|---------|-----|
| Voice (incoming) | `https://your-ngrok.app/call/incoming` (POST) |
| Status callback | `https://your-ngrok.app/call/status` (POST) |
| WhatsApp sandbox | `https://your-ngrok.app/whatsapp/incoming` (POST) |

### 6. Run

```bash
# Terminal 1: API Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Dashboard
streamlit run dashboard.py
```

### 7. Test

Call your Twilio number → speak in Hindi or English → get a ticket! 🎉

---

## 📁 Project Structure

```
NagrikSeva-AI/
├── nagrikseva/               # Application code
│   ├── main.py               # FastAPI app — 8 endpoints
│   ├── agent.py              # Gemini AI conversation manager
│   ├── prompts.py            # Trilingual system prompts
│   ├── stt.py                # Speech-to-text utilities
│   ├── database.py           # MongoDB CRUD operations
│   ├── whatsapp.py           # WhatsApp messaging
│   ├── outbound.py           # Outbound call campaigns
│   ├── dashboard.py          # Streamlit admin dashboard
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
├── .gsd/                     # Development docs
│   ├── ARCHITECTURE.md       # System architecture
│   ├── STACK.md              # Technology inventory
│   └── phases/               # Execution plans & verification
└── README.md                 # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/call/incoming` | Twilio inbound call webhook |
| POST | `/call/respond` | Conversation turn (speech → AI → TwiML) |
| POST | `/call/status` | Call end status webhook |
| GET | `/call/outbound-twiml/{ticket_id}` | TwiML for outbound calls |
| POST | `/outbound/trigger?hours=48` | Launch outbound campaign |
| GET | `/grievance/{ticket_id}` | Get grievance by ticket ID |
| POST | `/whatsapp/incoming` | WhatsApp message handler |

---

## 🎬 Demo Flow

1. **Health check** → Open `https://your-ngrok.app/` — see JSON status
2. **Inbound call** → Dial your Twilio number from a verified phone
3. **Speak Hindi** → Say name, ward, city, describe your complaint
4. **Get ticket** → AI confirms details and provides `NS-XXXXXXXX-XXXX`
5. **WhatsApp** → Receive confirmation message with ticket ID
6. **Dashboard** → See the grievance appear in Streamlit live feed
7. **Outbound** → Trigger a callback campaign from the dashboard

---

## ⚠️ Known Limitations

- **Twilio trial**: Only verified phone numbers can receive calls
- **WhatsApp sandbox**: Recipients must opt-in first (`join <keyword>`)
- **Ngrok URL**: Changes on restart — update Twilio webhooks accordingly
- **In-memory sessions**: AI chat resets on server restart
- **No auth**: Dashboard has no login (hackathon scope)

---

## 📄 License

MIT — Built for hackathon demonstration purposes.
