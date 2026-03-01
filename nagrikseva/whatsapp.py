"""
NagrikSeva AI — WhatsApp Messaging
====================================
Sends WhatsApp confirmations, status updates, and ticket lookups
via Twilio WhatsApp Sandbox.
"""

import os
import re
import logging

from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Twilio client (lazy init)
_twilio_client = None


def _get_client() -> Client:
    """Get or create the Twilio REST client."""
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
        )
    return _twilio_client


def format_whatsapp_number(phone: str) -> str:
    """
    Normalize an Indian phone number and add whatsapp: prefix.
    
    Handles formats: 9876543210, 09876543210, 919876543210,
    +919876543210, +91 98765 43210, etc.
    """
    # Remove spaces, dashes, brackets
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    
    # Remove whatsapp: prefix if already present
    cleaned = cleaned.replace("whatsapp:", "")
    
    # Remove leading 0
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]
    
    # Add +91 if 10 digits (Indian mobile)
    if len(cleaned) == 10 and cleaned.isdigit():
        cleaned = "+91" + cleaned
    
    # Add + if starts with 91 but no +
    if cleaned.startswith("91") and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    
    # Ensure + prefix exists
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    
    return "whatsapp:" + cleaned


def send_confirmation(phone: str, ticket_id: str, category: str,
                      description: str, ward: str) -> bool:
    """
    Send a bilingual WhatsApp confirmation message after grievance registration.
    
    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        client = _get_client()
        to_number = format_whatsapp_number(phone)
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        message_body = (
            f"✅ NagrikSeva | शिकायत दर्ज हुई\n\n"
            f"Ticket ID: {ticket_id}\n"
            f"Category: {category}\n"
            f"Ward: {ward}\n"
            f"Issue: {description}\n\n"
            f"आपकी शिकायत दर्ज हो गई है। 48 घंटों में अपडेट मिलेगा।\n"
            f"Your grievance is registered. You will receive an update within 48 hours.\n\n"
            f"📲 Status check: Reply with your Ticket ID anytime.\n"
            f"🙏 धन्यवाद | Thank you — NagrikSeva AI"
        )
        
        msg = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number,
        )
        
        logger.info(f"WhatsApp confirmation sent to {to_number}: SID={msg.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp confirmation to {phone}: {e}")
        return False


def send_status_update(phone: str, ticket_id: str, status: str,
                       notes: str = "") -> bool:
    """
    Send a WhatsApp status update message.
    
    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        client = _get_client()
        to_number = format_whatsapp_number(phone)
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        # Status emoji mapping
        emoji_map = {
            "resolved": "✅",
            "in_progress": "🔄",
            "escalated": "⚠️",
            "open": "📋",
            "incomplete": "❌",
        }
        emoji = emoji_map.get(status, "📋")
        
        message_body = (
            f"{emoji} NagrikSeva | Status Update\n\n"
            f"Ticket ID: {ticket_id}\n"
            f"Status: {status.replace('_', ' ').title()}\n"
        )
        
        if notes:
            message_body += f"Notes: {notes}\n"
        
        message_body += (
            f"\n📲 Reply with your Ticket ID for latest status.\n"
            f"🙏 धन्यवाद | Thank you — NagrikSeva AI"
        )
        
        msg = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number,
        )
        
        logger.info(f"WhatsApp status update sent to {to_number}: SID={msg.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp status update to {phone}: {e}")
        return False


def send_ticket_lookup(phone: str, grievance: dict) -> bool:
    """
    Send grievance status in response to a citizen's ticket ID query.
    
    Args:
        phone: Citizen phone number
        grievance: Grievance document dict from MongoDB
    
    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        client = _get_client()
        to_number = format_whatsapp_number(phone)
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        ticket_id = grievance.get("ticket_id", "N/A")
        status = grievance.get("status", "unknown")
        category = grievance.get("category", "N/A")
        ward = grievance.get("ward", "N/A")
        description = grievance.get("description", "N/A")
        created = grievance.get("created_at", "N/A")
        notes = grievance.get("resolution_notes", "")
        
        emoji_map = {
            "resolved": "✅",
            "in_progress": "🔄",
            "escalated": "⚠️",
            "open": "📋",
            "incomplete": "❌",
        }
        emoji = emoji_map.get(status, "📋")
        
        # Format date
        if hasattr(created, "strftime"):
            created = created.strftime("%d %b %Y, %I:%M %p")
        
        message_body = (
            f"{emoji} NagrikSeva | Ticket Status\n\n"
            f"Ticket ID: {ticket_id}\n"
            f"Status: {status.replace('_', ' ').title()}\n"
            f"Category: {category}\n"
            f"Ward: {ward}\n"
            f"Issue: {description}\n"
            f"Registered: {created}\n"
        )
        
        if notes:
            message_body += f"Resolution Notes: {notes}\n"
        
        message_body += f"\n🙏 NagrikSeva AI"
        
        msg = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number,
        )
        
        logger.info(f"WhatsApp ticket lookup sent to {to_number}: SID={msg.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp ticket lookup to {phone}: {e}")
        return False
