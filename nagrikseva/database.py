"""
NagrikSeva AI — MongoDB Database Operations
=============================================
All grievance CRUD operations, statistics aggregation,
and outbound call logging using PyMongo.
"""

import os
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------- Connection ----------

_client: Optional[MongoClient] = None


def get_db():
    """
    Get the MongoDB database instance with connection pooling.
    Uses a single global client, created lazily.
    """
    global _client
    if _client is None:
        _client = MongoClient(
            os.getenv("MONGODB_URI"),
            serverSelectionTimeoutMS=5000,
            maxPoolSize=10,
        )
    return _client[os.getenv("MONGODB_DB", "nagrikseva")]


def get_collection():
    """Get the grievances collection."""
    return get_db()["grievances"]


# ---------- Ticket ID ----------

def generate_ticket_id() -> str:
    """
    Generate a unique ticket ID in format NS-YYYYMMDD-XXXX.
    Checks DB for uniqueness before returning.
    """
    collection = get_collection()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    for _ in range(10):  # Max 10 retries
        random_part = f"{random.randint(0, 9999):04d}"
        ticket_id = f"NS-{today}-{random_part}"
        
        # Check uniqueness
        if collection.count_documents({"ticket_id": ticket_id}) == 0:
            return ticket_id
    
    # Fallback: use microseconds for extra randomness
    micro = datetime.now(timezone.utc).strftime("%f")[:4]
    return f"NS-{today}-{micro}"


# ---------- CRUD Operations ----------

def save_grievance(data: dict) -> str:
    """
    Insert a new grievance document into MongoDB.
    
    Args:
        data: Grievance data dict (ticket_id, citizen_name, phone, etc.)
    
    Returns:
        The ticket_id of the saved grievance.
    """
    try:
        collection = get_collection()
        
        now = datetime.now(timezone.utc)
        document = {
            "ticket_id": data.get("ticket_id", generate_ticket_id()),
            "call_sid": data.get("call_sid", ""),
            "citizen_name": data.get("citizen_name", ""),
            "phone": data.get("phone", ""),
            "ward": data.get("ward", ""),
            "district": data.get("district", ""),
            "category": data.get("category", "other"),
            "description": data.get("description", ""),
            "language": data.get("language", "hinglish"),
            "status": data.get("status", "open"),
            "created_at": now,
            "updated_at": now,
            "resolution_notes": data.get("resolution_notes", ""),
            "call_duration_s": data.get("call_duration_s", 0),
            "outbound_calls": [],
            "chat_history": data.get("chat_history", []),
        }
        
        collection.insert_one(document)
        logger.info(f"Grievance saved: {document['ticket_id']}")
        return document["ticket_id"]
        
    except Exception as e:
        logger.error(f"Failed to save grievance: {e}")
        raise


def get_grievance(ticket_id: str) -> Optional[dict]:
    """
    Retrieve a single grievance by ticket_id.
    
    Returns:
        Grievance dict or None if not found.
    """
    try:
        collection = get_collection()
        doc = collection.find_one({"ticket_id": ticket_id}, {"_id": 0})
        return doc
    except Exception as e:
        logger.error(f"Failed to get grievance {ticket_id}: {e}")
        return None


def update_status(ticket_id: str, status: str, notes: str = "") -> bool:
    """
    Update the status and optional resolution notes for a grievance.
    
    Returns:
        True if updated successfully, False otherwise.
    """
    try:
        collection = get_collection()
        update_data = {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            }
        }
        if notes:
            update_data["$set"]["resolution_notes"] = notes
        
        result = collection.update_one({"ticket_id": ticket_id}, update_data)
        if result.modified_count > 0:
            logger.info(f"Status updated: {ticket_id} → {status}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to update status for {ticket_id}: {e}")
        return False


def update_call_duration(call_sid: str, duration: int) -> bool:
    """
    Update call duration for a grievance identified by call_sid.
    
    Returns:
        True if updated, False otherwise.
    """
    try:
        collection = get_collection()
        result = collection.update_one(
            {"call_sid": call_sid},
            {"$set": {
                "call_duration_s": duration,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Failed to update call duration for {call_sid}: {e}")
        return False


def get_all_grievances(limit: int = 100) -> list:
    """
    Return grievances sorted by created_at descending.
    """
    try:
        collection = get_collection()
        cursor = collection.find({}, {"_id": 0}).sort("created_at", DESCENDING).limit(limit)
        return list(cursor)
    except Exception as e:
        logger.error(f"Failed to get grievances: {e}")
        return []


# ---------- Statistics ----------

def get_stats() -> dict:
    """
    Return aggregated statistics for the dashboard.
    
    Returns dict with:
        total, by_status, by_category, by_language, by_ward,
        today_count, avg_call_duration
    """
    try:
        collection = get_collection()
        
        total = collection.count_documents({})
        
        # By status
        by_status = {}
        for status in ["open", "in_progress", "resolved", "escalated", "incomplete"]:
            by_status[status] = collection.count_documents({"status": status})
        
        # By category
        by_category = {}
        for cat in ["roads", "water", "electricity", "sanitation", "health", "other"]:
            by_category[cat] = collection.count_documents({"category": cat})
        
        # By language
        by_language = {}
        for lang in ["hindi", "english", "hinglish"]:
            by_language[lang] = collection.count_documents({"language": lang})
        
        # By ward (top wards)
        pipeline = [
            {"$group": {"_id": "$ward", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]
        ward_results = list(collection.aggregate(pipeline))
        by_ward = {r["_id"]: r["count"] for r in ward_results if r["_id"]}
        
        # Today count
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = collection.count_documents({"created_at": {"$gte": today_start}})
        
        # Average call duration
        dur_pipeline = [
            {"$match": {"call_duration_s": {"$gt": 0}}},
            {"$group": {"_id": None, "avg": {"$avg": "$call_duration_s"}}},
        ]
        dur_result = list(collection.aggregate(dur_pipeline))
        avg_call_duration = round(dur_result[0]["avg"], 1) if dur_result else 0
        
        return {
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
            "by_language": by_language,
            "by_ward": by_ward,
            "today_count": today_count,
            "avg_call_duration": avg_call_duration,
        }
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "total": 0,
            "by_status": {},
            "by_category": {},
            "by_language": {},
            "by_ward": {},
            "today_count": 0,
            "avg_call_duration": 0,
        }


# ---------- Outbound Campaign ----------

def get_open_old_grievances(hours: int = 48) -> list:
    """
    Get grievances with status='open' older than the specified hours.
    Used for outbound follow-up campaigns.
    """
    try:
        collection = get_collection()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cursor = collection.find(
            {"status": "open", "created_at": {"$lte": cutoff}},
            {"_id": 0},
        ).sort("created_at", DESCENDING)
        return list(cursor)
    except Exception as e:
        logger.error(f"Failed to get old grievances: {e}")
        return []


def log_outbound_call(ticket_id: str, outcome: str, message: str) -> bool:
    """
    Append an outbound call record to a grievance's outbound_calls array.
    
    Returns:
        True if logged successfully.
    """
    try:
        collection = get_collection()
        result = collection.update_one(
            {"ticket_id": ticket_id},
            {
                "$push": {
                    "outbound_calls": {
                        "called_at": datetime.now(timezone.utc),
                        "outcome": outcome,
                        "message": message,
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Failed to log outbound call for {ticket_id}: {e}")
        return False
