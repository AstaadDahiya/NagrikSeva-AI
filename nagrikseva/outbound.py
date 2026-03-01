"""
NagrikSeva AI — Outbound Call Campaign
========================================
Makes outbound calls to citizens for status updates on their grievances.
Uses Twilio REST API to initiate calls that play TwiML messages.
"""

import os
import time
import logging

from twilio.rest import Client
from dotenv import load_dotenv

import database

load_dotenv()

logger = logging.getLogger(__name__)


def make_outbound_call(
    phone: str,
    ticket_id: str,
    status_message: str,
    account_sid: str = None,
    auth_token: str = None,
    from_number: str = None,
    base_url: str = None,
) -> str | None:
    """
    Initiate a single outbound call to a citizen.
    
    The call plays a TwiML message hosted at /call/outbound-twiml/{ticket_id}.
    
    Args:
        phone: Citizen phone number (E.164 format)
        ticket_id: Grievance ticket ID
        status_message: Status update message to deliver
        account_sid: Twilio Account SID (defaults to env)
        auth_token: Twilio Auth Token (defaults to env)
        from_number: Twilio phone number (defaults to env)
        base_url: Base URL for TwiML endpoint (defaults to env)
    
    Returns:
        Twilio Call SID on success, None on failure.
    """
    try:
        sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        from_num = from_number or os.getenv("TWILIO_PHONE_NUMBER")
        url = base_url or os.getenv("BASE_URL")
        
        client = Client(sid, token)
        
        twiml_url = f"{url}/call/outbound-twiml/{ticket_id}"
        status_url = f"{url}/call/status"
        
        call = client.calls.create(
            to=phone,
            from_=from_num,
            url=twiml_url,
            status_callback=status_url,
            status_callback_event=["completed"],
            method="GET",
        )
        
        logger.info(f"Outbound call initiated: {ticket_id} → {phone}, CallSID={call.sid}")
        return call.sid
        
    except Exception as e:
        logger.error(f"Failed to make outbound call to {phone} for {ticket_id}: {e}")
        return None


def run_campaign(
    grievance_list: list,
    account_sid: str = None,
    auth_token: str = None,
    from_number: str = None,
    base_url: str = None,
) -> dict:
    """
    Run an outbound call campaign for a list of grievances.
    
    Rate-limited to 1 call per second.
    
    Args:
        grievance_list: List of grievance dicts from MongoDB
        account_sid: Twilio Account SID
        auth_token: Twilio Auth Token
        from_number: Twilio phone number
        base_url: Base URL for TwiML endpoint
    
    Returns:
        Summary dict: {triggered: N, failed: N, skipped: N}
    """
    triggered = 0
    failed = 0
    skipped = 0
    
    for grievance in grievance_list:
        ticket_id = grievance.get("ticket_id", "")
        phone = grievance.get("phone", "")
        
        if not phone or not ticket_id:
            skipped += 1
            logger.warning(f"Skipping grievance with missing phone/ticket_id: {ticket_id}")
            continue
        
        status_msg = (
            f"Aapki shikayat {ticket_id} par kaam jaari hai. "
            f"Hum jald se jald iska samaadhaan karenge."
        )
        
        call_sid = make_outbound_call(
            phone=phone,
            ticket_id=ticket_id,
            status_message=status_msg,
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=from_number,
            base_url=base_url,
        )
        
        if call_sid:
            triggered += 1
            # Log to MongoDB
            database.log_outbound_call(
                ticket_id=ticket_id,
                outcome="initiated",
                message=status_msg,
            )
        else:
            failed += 1
            database.log_outbound_call(
                ticket_id=ticket_id,
                outcome="failed",
                message="Call initiation failed",
            )
        
        # Rate limit: 1 call per second
        time.sleep(1)
    
    summary = {"triggered": triggered, "failed": failed, "skipped": skipped}
    logger.info(f"Outbound campaign complete: {summary}")
    return summary
