# 🇮🇳 NagrikSeva AI

**AI-powered citizen grievance redressal system for India.** Citizens call a phone number, an AI agent converses in Hindi/English/Hinglish, collects their complaint, issues a ticket, and sends WhatsApp confirmation. Administrators get a real-time analytics dashboard.

---

## Architecture

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

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Backend | FastAPI (Python) | Free |
| Voice Calls | Twilio Voice | Free trial ($15 credit) |
| Speech-to-Text | Twilio `<Gather>` built-in | Free with Twilio |
| AI Brain | Google Gemini 1.5 Flash | Free API |
| Database | MongoDB Atlas M0 | Free |
| WhatsApp | Twilio WhatsApp Sandbox | Free trial |
| Dashboard | Streamlit + Plotly | Free |
| Tunnel | Ngrok | Free |
| Deployment | Render.com | Free tier |

---

## Setup Instructions

### 1. Clone & Install

```bash
cd nagrikseva
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in all values in .env:
# - Twilio: Account SID, Auth Token, Phone Number
# - Deepgram: API Key (optional, for future production STT)
# - Gemini: API Key (get from https://aistudio.google.com)
# - MongoDB: Connection URI (from Atlas dashboard)
# - BASE_URL: Your ngrok URL
```

### 3. Start Ngrok Tunnel

```bash
ngrok http 8000
# Copy the https://xxx.ngrok-free.app URL to .env as BASE_URL
```

### 4. Configure Twilio Webhooks

In [Twilio Console](https://console.twilio.com):
- **Phone Number → Voice webhook**: `https://xxx.ngrok-free.app/call/incoming` (POST)
- **Phone Number → Status callback**: `https://xxx.ngrok-free.app/call/status` (POST)
- **WhatsApp Sandbox → Webhook**: `https://xxx.ngrok-free.app/whatsapp/incoming` (POST)

### 5. Activate WhatsApp Sandbox

From your demo phone, send `join <keyword>` to **+14155238886** on WhatsApp.

### 6. Verify Demo Phone Number

In Twilio Console → **Verified Caller IDs**, add and verify your demo phone number (required for trial accounts).

### 7. Run the Application

```bash
# Terminal 1: FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Streamlit dashboard
streamlit run dashboard.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/call/incoming` | Twilio inbound call webhook |
| POST | `/call/respond` | Conversation turn webhook |
| POST | `/call/status` | Call end status webhook |
| GET | `/call/outbound-twiml/{ticket_id}` | TwiML for outbound calls |
| POST | `/outbound/trigger?hours=48` | Launch outbound campaign |
| GET | `/grievance/{ticket_id}` | Get grievance by ticket ID |
| POST | `/whatsapp/incoming` | WhatsApp message handler |

---

## Demo Script (7 Steps)

1. **Show the health check**: Open `https://xxx.ngrok-free.app/` in a browser — show JSON response
2. **Make the call**: Dial the Twilio number from your verified phone
3. **Speak in Hindi**: Say your name, ward, city, and describe a grievance
4. **Get ticket ID**: The AI will read back your details and provide a ticket number
5. **Check WhatsApp**: Show the confirmation message with ticket ID
6. **Open Dashboard**: Show the Streamlit dashboard with the new grievance in Live Feed
7. **Trigger Outbound**: Click the outbound campaign button to demo the callback feature

---

## File Structure

```
nagrikseva/
├── main.py          # FastAPI application (core)
├── agent.py         # Gemini AI conversation manager
├── stt.py           # Speech-to-text utilities
├── whatsapp.py      # WhatsApp messaging via Twilio
├── database.py      # MongoDB operations
├── dashboard.py     # Streamlit admin dashboard
├── outbound.py      # Outbound call campaign
├── prompts.py       # Gemini system prompts
├── .env             # Environment variables (not committed)
├── .env.example     # Environment template
├── requirements.txt # Python dependencies
└── README.md        # This file
```

---

## Free Tier Limits

| Service | Limit |
|---------|-------|
| Twilio Trial | $15.50 credit (~100 calls), verified numbers only |
| Gemini Flash | 60 requests/min, 1M tokens/min |
| MongoDB Atlas M0 | 512 MB storage, shared RAM |
| Ngrok Free | 1 tunnel, random URL on restart |
| Render Free | 750 hours/month, sleeps after 15 min inactivity |

---

## Known Limitations

- **Twilio trial**: Can only call/text verified phone numbers
- **WhatsApp sandbox**: Recipients must send `join <keyword>` first
- **Ngrok URL**: Changes on restart — must update Twilio webhook
- **In-memory sessions**: AI chat sessions reset on server restart
- **Twilio STT**: Hindi accuracy is limited; Deepgram Nova-2 recommended for production
- **No authentication**: Dashboard has no login (hackathon scope)

---

## License

MIT — Built for hackathon demonstration purposes.
