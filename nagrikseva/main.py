"""
NagrikSeva AI — FastAPI Application
=====================================
The heart of the system. Handles Twilio voice webhooks, WhatsApp messages,
outbound campaigns, and grievance API endpoints.
"""

import os
import re
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv

import agent
import stt
import database
import whatsapp
import outbound

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------- Shared Twilio Client ----------

_twilio_client = None


def get_twilio_client() -> TwilioClient:
    """Get or create a shared Twilio REST client."""
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = TwilioClient(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
        )
    return _twilio_client


# Ticket ID regex pattern
TICKET_ID_PATTERN = re.compile(r"^NS-\d{8}-\d{4}$")
TICKET_ID_SEARCH = re.compile(r"NS-\d{8}-\d{4}")


# ---------- App Setup ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🇮🇳 NagrikSeva AI server starting...")
    yield
    logger.info("NagrikSeva AI server shutting down.")


app = FastAPI(
    title="NagrikSeva AI",
    description="AI-powered citizen grievance redressal system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health Check ----------

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "NagrikSeva AI is running", "version": "1.0.0"}


# ---------- Inbound Call ----------

@app.post("/call/incoming")
async def call_incoming(request: Request):
    """
    Twilio webhook: fires when someone calls the Twilio number.
    Initializes AI session and delivers the greeting.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    caller = form.get("From", "unknown")
    
    logger.info(f"📞 Incoming call: CallSid={call_sid}, From={caller}")
    
    # Initialize Gemini session
    try:
        agent.initialize_session(call_sid)
    except Exception as e:
        logger.error(f"Failed to init session: {e}")
    
    # Build TwiML greeting
    response = VoiceResponse()
    
    greeting = (
        "Namaste! NagrikSeva AI mein aapka swagat hai. "
        "Aap Hindi ya English mein bol sakte hain. "
        "Welcome to NagrikSeva AI. You can speak in Hindi or English. "
        "Kripya apni shikayat batayein. Please tell us your grievance."
    )
    
    gather = Gather(
        input="speech",
        language="hi-IN",
        speech_timeout="3",
        action="/call/respond",
        method="POST",
    )
    gather.say(greeting, voice="Polly.Aditi", language="hi-IN")
    response.append(gather)
    
    # Fallback if no speech detected
    response.say(
        "Koi awaaz nahi mili. Kripya dobara bolein.",
        voice="Polly.Aditi",
        language="hi-IN",
    )
    response.redirect("/call/incoming")
    
    return Response(content=str(response), media_type="application/xml")


# ---------- Conversation Turn ----------

@app.post("/call/respond")
async def call_respond(request: Request):
    """
    Twilio webhook: fires after each citizen utterance.
    Routes speech through STT cleaning → Gemini AI → TwiML response.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    speech_result = form.get("SpeechResult", "")
    confidence = form.get("Confidence", "0")
    caller = form.get("From", "unknown")
    
    logger.info(
        f"🎤 Speech: CallSid={call_sid}, "
        f"Confidence={confidence}, Text='{speech_result[:80]}'"
    )
    
    # Clean transcript
    cleaned = stt.clean_transcript(speech_result)
    
    # Check intelligibility
    if not stt.is_intelligible(cleaned):
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            language="hi-IN",
            speech_timeout="3",
            action="/call/respond",
            method="POST",
        )
        gather.say(
            "Maaf kijiye, aapki awaaz saaf nahi aayi. Kripya dobara bolein. "
            "Sorry, I couldn't hear you clearly. Please repeat.",
            voice="Polly.Aditi",
            language="hi-IN",
        )
        response.append(gather)
        response.say(
            "Koi awaaz nahi mili. Call samaapt ho rahi hai. Dhanyawad.",
            voice="Polly.Aditi",
            language="hi-IN",
        )
        return Response(content=str(response), media_type="application/xml")
    
    # Get AI response
    ai_response = agent.get_response(call_sid, cleaned)
    
    # Check if response contains a ticket ID (NS-YYYYMMDD-XXXX pattern)
    ticket_match = re.search(r"NS-\d{8}-\d{4}", ai_response)
    if ticket_match:
        ticket_id = ticket_match.group(0)
        logger.info(f"🎫 Ticket generated: {ticket_id} for call {call_sid}")
        
        # Extract data and save to MongoDB
        try:
            # Parse grievance data from chat history
            grievance_data = _extract_grievance_data(call_sid, ticket_id, caller)
            grievance_data["ticket_id"] = ticket_id
            database.save_grievance(grievance_data)
            
            # Send WhatsApp confirmation (non-blocking, don't fail the call)
            try:
                whatsapp.send_confirmation(
                    phone=caller,
                    ticket_id=ticket_id,
                    category=grievance_data.get("category", "other"),
                    description=grievance_data.get("description", ""),
                    ward=grievance_data.get("ward", ""),
                )
            except Exception as wa_err:
                logger.error(f"WhatsApp send failed: {wa_err}")
                
        except Exception as db_err:
            logger.error(f"Failed to save grievance: {db_err}")
    
    # Build TwiML response
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        language="hi-IN",
        speech_timeout="3",
        action="/call/respond",
        method="POST",
    )
    gather.say(ai_response, voice="Polly.Aditi", language="hi-IN")
    response.append(gather)
    
    # Fallback
    response.say(
        "Koi awaaz nahi mili. Kripya dobara bolein.",
        voice="Polly.Aditi",
        language="hi-IN",
    )
    response.redirect("/call/incoming")
    
    return Response(content=str(response), media_type="application/xml")


def _extract_grievance_data(call_sid: str, ticket_id: str, phone: str) -> dict:
    """
    Extract structured grievance data from the AI conversation for this call.
    Parses the Gemini chat history using regex — does NOT call Gemini again
    (that would cause the extraction prompt to be spoken aloud to the citizen).
    """
    data = {
        "ticket_id": ticket_id,
        "call_sid": call_sid,
        "phone": phone,
        "citizen_name": "",
        "ward": "",
        "district": "",
        "category": "other",
        "description": "",
        "language": agent.get_session_language(call_sid),
        "status": "open",
    }

    try:
        # Access the in-memory chat history directly — no API call
        if call_sid not in agent.sessions:
            logger.warning(f"No session found for {call_sid}, cannot extract data")
            return data

        chat = agent.sessions[call_sid]["chat"]
        # Combine all model responses into one text block for parsing
        model_texts = []
        user_texts = []
        for msg in chat.history:
            text = msg.parts[0].text if msg.parts else ""
            if msg.role == "model":
                model_texts.append(text)
            else:
                user_texts.append(text)

        all_model = "\n".join(model_texts)
        all_user = "\n".join(user_texts)

        # --- Parse category (look for known keywords) ---
        categories = ["roads", "water", "electricity", "sanitation", "health", "other"]
        cat_pattern = re.compile(
            r"(?:category|shreni|shikayat)\s*[:—-]?\s*(" + "|".join(categories) + ")",
            re.IGNORECASE,
        )
        cat_match = cat_pattern.search(all_model)
        if cat_match:
            data["category"] = cat_match.group(1).lower()
        else:
            # Fallback: look in user messages
            for cat in categories:
                if cat in all_user.lower() or cat in all_model.lower():
                    data["category"] = cat
                    break

        # --- Parse name (usually first user response) ---
        name_pattern = re.compile(
            r"(?:naam|name)\s*[:—-]?\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        name_match = name_pattern.search(all_model)  # from confirmation message
        if name_match:
            data["citizen_name"] = name_match.group(1).strip().strip("*")
        elif user_texts:
            # First user message is often their name
            data["citizen_name"] = user_texts[0].strip()[:100]

        # --- Parse ward ---
        ward_pattern = re.compile(
            r"(?:ward|area|ilaka)\s*[:—-]?\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        ward_match = ward_pattern.search(all_model)
        if ward_match:
            data["ward"] = ward_match.group(1).strip().strip("*")

        # --- Parse district ---
        district_pattern = re.compile(
            r"(?:district|sheher|city|jila)\s*[:—-]?\s*(.+?)(?:\n|$)", re.IGNORECASE
        )
        district_match = district_pattern.search(all_model)
        if district_match:
            data["district"] = district_match.group(1).strip().strip("*")

        # --- Parse description (from confirmation or last user messages) ---
        desc_pattern = re.compile(
            r"(?:shikayat|grievance|complaint|issue|description|vivaran)\s*[:—-]?\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        desc_match = desc_pattern.search(all_model)
        if desc_match:
            data["description"] = desc_match.group(1).strip().strip("*")[:500]
        elif len(user_texts) >= 2:
            # Use later user messages as description
            data["description"] = " ".join(user_texts[1:])[:500]

        logger.info(f"Extracted grievance data for {call_sid}: {data}")

    except Exception as e:
        logger.error(f"Failed to extract grievance data: {e}")

    return data


# ---------- Call Status ----------

@app.post("/call/status")
async def call_status(request: Request):
    """
    Twilio webhook: fires when a call ends.
    Updates call duration in MongoDB and ends the AI session.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    call_duration = form.get("CallDuration", "0")
    call_status_val = form.get("CallStatus", "unknown")
    
    logger.info(
        f"📴 Call ended: CallSid={call_sid}, "
        f"Duration={call_duration}s, Status={call_status_val}"
    )
    
    # Update call duration in MongoDB
    try:
        duration = int(call_duration)
        database.update_call_duration(call_sid, duration)
    except (ValueError, Exception) as e:
        logger.error(f"Failed to update call duration: {e}")
    
    # End AI session
    history = agent.end_session(call_sid)
    
    return JSONResponse({"status": "ok"})


# ---------- Outbound Campaign ----------

@app.post("/outbound/trigger")
async def trigger_outbound(hours: int = Query(default=48)):
    """
    Trigger an outbound call campaign for open grievances older than X hours.
    """
    logger.info(f"🚀 Outbound campaign triggered: hours={hours}")
    
    try:
        grievances = database.get_open_old_grievances(hours=hours)
        
        if not grievances:
            return JSONResponse({
                "status": "no_grievances",
                "message": f"No open grievances older than {hours} hours",
                "count": 0,
            })
        
        result = outbound.run_campaign(grievances)
        
        return JSONResponse({
            "status": "campaign_complete",
            "triggered": result["triggered"],
            "failed": result["failed"],
            "skipped": result["skipped"],
        })
        
    except Exception as e:
        logger.error(f"Outbound campaign error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )


# ---------- Outbound TwiML ----------

@app.get("/call/outbound-twiml/{ticket_id}")
async def outbound_twiml(ticket_id: str):
    """
    Returns TwiML for outbound status update calls.
    Called by Twilio when the outbound call connects.
    """
    grievance = database.get_grievance(ticket_id)
    
    phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    if grievance:
        status = grievance.get("status", "open")
        message = (
            f"Namaste, NagrikSeva AI ki taraf se call aa rahi hai. "
            f"Aapki shikayat {ticket_id} ka status update hai: "
            f"Aapki shikayat par kaam jaari hai aur jald samaadhaan hoga. "
            f"Agar koi sawaal ho toh {phone_number} par call karein. "
            f"Dhanyawad."
        )
    else:
        message = (
            f"Namaste, NagrikSeva AI ki taraf se call aa rahi hai. "
            f"Kripya {phone_number} par call karke apni shikayat ki jaankari prapt karein. "
            f"Dhanyawad."
        )
    
    response = VoiceResponse()
    response.say(message, voice="Polly.Aditi", language="hi-IN")
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")


# ---------- Grievance API ----------

@app.get("/grievance/{ticket_id}")
async def get_grievance(ticket_id: str):
    """Return grievance JSON for a given ticket ID."""
    # Validate ticket ID format
    if not TICKET_ID_PATTERN.match(ticket_id.upper()):
        return JSONResponse(
            {"error": "Invalid ticket ID format. Expected: NS-YYYYMMDD-XXXX"},
            status_code=400,
        )

    grievance = database.get_grievance(ticket_id.upper())
    if grievance:
        # Convert datetime objects for JSON serialization
        for key in ["created_at", "updated_at"]:
            if grievance.get(key) and hasattr(grievance[key], "isoformat"):
                grievance[key] = grievance[key].isoformat()
        
        # Convert outbound call dates too
        for call_log in grievance.get("outbound_calls", []):
            if call_log.get("called_at") and hasattr(call_log["called_at"], "isoformat"):
                call_log["called_at"] = call_log["called_at"].isoformat()
        
        return JSONResponse(grievance)
    return JSONResponse({"error": "Grievance not found"}, status_code=404)


# ---------- WhatsApp Incoming ----------

@app.post("/whatsapp/incoming")
async def whatsapp_incoming(request: Request):
    """
    Handle incoming WhatsApp messages.
    Citizens can reply with their ticket ID to check status.
    """
    form = await request.form()
    message_body = form.get("Body", "").strip()
    from_number = form.get("From", "")
    
    logger.info(f"📱 WhatsApp message from {from_number}: '{message_body}'")
    
    # Check if message looks like a ticket ID
    ticket_match = re.search(r"NS-\d{8}-\d{4}", message_body.upper())
    
    if ticket_match:
        ticket_id = ticket_match.group(0)
        grievance = database.get_grievance(ticket_id)
        
        if grievance:
            whatsapp.send_ticket_lookup(
                phone=from_number.replace("whatsapp:", ""),
                grievance=grievance,
            )
        else:
            # Ticket not found — send message via shared Twilio client
            try:
                get_twilio_client().messages.create(
                    body=(
                        f"❌ Ticket ID '{ticket_id}' not found.\n"
                        f"Kripya sahi Ticket ID bhejein.\n"
                        f"Please send the correct Ticket ID."
                    ),
                    from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
                    to=from_number,
                )
            except Exception as e:
                logger.error(f"Failed to send ticket-not-found reply: {e}")
    else:
        # Not a ticket ID — send help message
        try:
            get_twilio_client().messages.create(
                body=(
                    "🙏 NagrikSeva AI\n\n"
                    "Apni shikayat ka status jaanne ke liye, "
                    "apna Ticket ID bhejein (e.g., NS-20260301-1234).\n\n"
                    "To check your grievance status, "
                    "please reply with your Ticket ID."
                ),
                from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
                to=from_number,
            )
        except Exception as e:
            logger.error(f"Failed to send help reply: {e}")
    
    return Response(content="<Response/>", media_type="application/xml")


# ---------- Main ----------

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
