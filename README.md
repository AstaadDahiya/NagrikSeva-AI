# 🇮🇳 NagrikSeva AI

**AI-powered citizen grievance redressal system for India.**

Citizens call a phone number → an AI agent converses in **Hindi/English/Hinglish** → collects their complaint → issues a ticket → sends **WhatsApp confirmation**. Administrators monitor everything via a real-time **dark-themed admin dashboard**.

> 💰 **Entire stack runs free** — built on free tiers and Twilio trial credit ($15).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📞 **Inbound AI Calls** | Gemini 2.5 Flash picks up, speaks naturally in Hindi, collects grievance details |
| 🗣️ **Trilingual Support** | Hindi, English, Hinglish — auto-detects and adapts mid-conversation |
| 🎫 **Ticket System** | Auto-generates unique `NS-YYYYMMDD-XXXX` ticket IDs with collision checking |
| 📱 **WhatsApp Integration** | Instant ticket confirmation + status lookup via WhatsApp |
| 🖥️ **Admin Dashboard** | Dark-themed Lovable-style UI with 5 tabs — Overview, Live Calls, Grievances, Analytics, Campaign |
| 📤 **Outbound Campaigns** | Auto-call citizens with status updates on stale grievances |
| 🔄 **Live Call Transcripts** | Real-time Agent ↔ Citizen conversation view with stage tracking |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Citizen    │────▶│   Twilio     │────▶│  FastAPI Server  │
│ (Phone Call) │◀────│   Voice      │◀────│  (main.py)       │
└──────────────┘     └─────────────┘     └────────┬─────────┘
                                                   │
                     ┌─────────────┐     ┌─────────▼────────┐
                     │  WhatsApp   │◀────│   Gemini 2.5     │
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
| Backend | FastAPI (Python 3.13) | Free |
| Voice Calls | Twilio Voice + TwiML | Free trial ($15) |
| AI Brain | Google Gemini 2.5 Flash (`google-genai` SDK) | Free API |
| Database | MongoDB Atlas M0 | Free (512 MB) |
| WhatsApp | Twilio WhatsApp Sandbox | Free trial |
| Dashboard | Streamlit + Plotly (dark theme) | Free |
| Tunnel | Localtunnel (or Ngrok) | Free |

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

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Start Tunnel

```bash
# Option A: Localtunnel (recommended — no interstitial page)
npx -y localtunnel --port 8000
# Copy the https URL to .env as BASE_URL

# Option B: Ngrok
ngrok http 8000
```

### 5. Configure Twilio Webhooks

Set your phone number's webhooks in [Twilio Console](https://console.twilio.com):

| Webhook | URL |
|---------|-----|
| Voice (incoming) | `https://your-tunnel-url/call/incoming` (POST) |
| Status callback | `https://your-tunnel-url/call/status` (POST) |
| WhatsApp sandbox | `https://your-tunnel-url/whatsapp/incoming` (POST) |

**Or configure programmatically** — the server auto-sets webhooks via the Twilio API.

### 6. Run

```bash
# Terminal 1: API Server
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Dashboard
source venv/bin/activate
python3 -m streamlit run dashboard.py
```

### 7. Test

Call your Twilio number → speak in Hindi → get a ticket! 🎉

---

## 📁 Project Structure

```
NagrikSeva-AI/
├── nagrikseva/               # Application code
│   ├── main.py               # FastAPI app — 8 endpoints
│   ├── agent.py              # Gemini 2.5 Flash conversation manager
│   ├── prompts.py            # Trilingual system prompts
│   ├── stt.py                # Speech-to-text cleaning utilities
│   ├── database.py           # MongoDB CRUD + aggregations
│   ├── whatsapp.py           # WhatsApp messaging
│   ├── outbound.py           # Outbound call campaigns
│   ├── dashboard.py          # Streamlit admin dashboard (dark UI)
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
├── .gsd/                     # Development methodology docs
│   ├── ARCHITECTURE.md
│   ├── STACK.md
│   └── phases/
└── README.md
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

## 🖥️ Dashboard

The admin dashboard features a **dark Lovable-style UI** with 5 tabs:

| Tab | What It Shows |
|-----|--------------|
| **Overview** | KPI cards, category donut chart, weekly volume, live feed table |
| **Live Calls** | Active call transcript, caller info, conversation stages, call metrics |
| **Grievances** | Searchable table with status pills, category icons, and time tracking |
| **Analytics** | Ward breakdown, resolution trends, language distribution, call heatmap |
| **Campaign** | Configure & launch outbound follow-up campaigns with time threshold slider |

> All data is pulled live from MongoDB. Dashboard auto-refreshes every 30 seconds.

---

## 🎬 Demo Flow

1. **Start server** → `uvicorn main:app --host 0.0.0.0 --port 8000`
2. **Start tunnel** → `npx -y localtunnel --port 8000`
3. **Inbound call** → Dial your Twilio number from a verified phone
4. **Speak Hindi** → *"Mera naam Aryan hai, Ward 17, Chandigarh se, paani ka problem hai"*
5. **AI responds** → Asks clarifying questions, confirms category, generates ticket
6. **WhatsApp** → Receive confirmation message with ticket ID
7. **Dashboard** → See the grievance appear in real-time with chat transcript
8. **Campaign** → Trigger outbound callbacks for stale grievances

---

## ⚠️ Known Limitations

- **Twilio trial**: Only verified phone numbers can make/receive calls; disclaimer plays before every call
- **WhatsApp sandbox**: Recipients must opt-in first (`join <keyword>`)
- **Tunnel URL**: Changes on restart — update Twilio webhooks accordingly (or use the auto-config script)
- **In-memory sessions**: AI chat history resets on server restart
- **No auth**: Dashboard has no login (demo/hackathon scope)
- **Gemini free tier**: Rate limits apply (RPM/RPD) — may need paid tier for heavy usage

---

## 🚀 Deployment

For production deployment, recommended platforms:

| Platform | Cost | Best For |
|----------|------|----------|
| **Railway** | Free → $5/mo | Easiest — one-click GitHub deploy |
| **Google Cloud Run** | Free tier | Auto-scales, pairs with Gemini API |
| **Render** | Free (cold starts) | Simple, but webhook timeouts on free |
| **DigitalOcean** | $4-6/mo | Full control VPS |

---

## 📄 License

MIT — Built for hackathon & demonstration purposes.
