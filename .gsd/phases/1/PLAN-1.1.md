---
phase: 1
plan: 1
wave: 1
depends_on: []
files_modified: [nagrikseva/main.py]
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Grievance data extraction happens silently without extra Gemini prompt heard by citizen"
    - "Twilio Client is instantiated once and reused across all endpoints"
    - "Ticket ID input is validated with regex before DB lookup"
  artifacts:
    - "nagrikseva/main.py contains a single shared Twilio client"
    - "_extract_grievance_data() uses regex parsing, not a Gemini call"
---

# Plan 1.1: Fix Call Flow & Consolidate Twilio Client

<objective>
Fix the critical call-flow bug where `_extract_grievance_data()` sends an extra Gemini prompt mid-call that the citizen hears as TTS, consolidate duplicated Twilio Client instantiation, and add input validation on the grievance lookup endpoint.

Purpose: The extra Gemini prompt is the highest-priority bug — it breaks the live demo by saying extraction instructions to the citizen.
Output: A clean `main.py` with silent data extraction, shared Twilio client, and validated inputs.
</objective>

<context>
Load for context:
- .gsd/ARCHITECTURE.md
- nagrikseva/main.py
- nagrikseva/agent.py (for session access pattern)
</context>

<tasks>

<task type="auto">
  <name>Fix silent grievance data extraction</name>
  <files>nagrikseva/main.py</files>
  <action>
    Rewrite `_extract_grievance_data()` to extract citizen details from the Gemini chat history
    using regex/string parsing INSTEAD of sending another prompt to Gemini.
    
    Approach:
    1. Access `agent.sessions[call_sid]["chat"].history` to get all messages
    2. Parse the final AI confirmation message (which contains name, ward, district, category, description)
    3. Use regex to extract each field from the confirmation text
    4. Fallback: if regex fails, set fields to empty strings — never call Gemini again
    
    AVOID: Calling `agent.get_response()` for extraction — this sends a user message to Gemini
    which Twilio will speak aloud to the citizen. This is the bug we're fixing.
  </action>
  <verify>
    Grep main.py for `agent.get_response` calls — should appear exactly once (in `call_respond`),
    NOT in `_extract_grievance_data`.
  </verify>
  <done>
    `_extract_grievance_data()` parses data from chat history without any Gemini API call.
    `agent.get_response` is called exactly once per request in `call_respond`.
  </done>
</task>

<task type="auto">
  <name>Consolidate Twilio Client and add input validation</name>
  <files>nagrikseva/main.py</files>
  <action>
    1. Create a module-level lazy Twilio client at the top of main.py:
       ```python
       _twilio_client = None
       def get_twilio_client():
           global _twilio_client
           if _twilio_client is None:
               _twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
           return _twilio_client
       ```
    2. Replace the two inline `Client(...)` instantiations in `whatsapp_incoming` (lines ~428, ~447)
       with calls to `get_twilio_client()`
    3. Add ticket ID validation on `GET /grievance/{ticket_id}`:
       - Regex check: `^NS-\d{8}-\d{4}$`
       - Return 400 if invalid format
    4. Add the same validation in `whatsapp_incoming` before DB lookup
    
    AVOID: Importing Client from twilio.rest at function scope — move to top-level import.
  </action>
  <verify>
    Grep for `from twilio.rest import Client` — should appear once at top level, not inside functions.
    Grep for `Client(` — should appear once in `get_twilio_client()`, not inline in endpoints.
  </verify>
  <done>
    Single shared Twilio client. No inline Client() calls in endpoints.
    Invalid ticket IDs return 400 instead of hitting the database.
  </done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] `python3 -c "import py_compile; py_compile.compile('main.py', doraise=True)"`
- [ ] `grep -c "agent.get_response" main.py` returns `1`
- [ ] `grep -c "Client(" main.py` returns `1` (the one in `get_twilio_client`)
- [ ] No `from twilio.rest import Client` inside function bodies
</verification>

<success_criteria>
- [ ] `_extract_grievance_data` does zero Gemini API calls
- [ ] Twilio Client is a lazy singleton, not instantiated per-request
- [ ] Invalid ticket ID format returns 400
- [ ] main.py compiles without errors
</success_criteria>
