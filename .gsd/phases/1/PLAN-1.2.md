---
phase: 1
plan: 2
wave: 1
depends_on: []
files_modified: [nagrikseva/agent.py, nagrikseva/requirements.txt]
autonomous: true
user_setup: []

must_haves:
  truths:
    - "agent.py uses google.genai SDK instead of deprecated google.generativeai"
    - "Unused packages removed from requirements.txt"
    - "All existing agent functions still work with same signatures"
  artifacts:
    - "nagrikseva/agent.py imports from google.genai"
    - "nagrikseva/requirements.txt has google-genai, not google-generativeai"
---

# Plan 1.2: Migrate Gemini SDK & Cleanup Dependencies

<objective>
Migrate from the deprecated `google.generativeai` package to `google.genai`, and remove unused
dependencies (`deepgram-sdk`, `httpx`) from requirements.txt.

Purpose: `google.generativeai` shows a FutureWarning and will stop receiving updates. Cleaning
unused deps reduces install time and attack surface.
Output: Updated `agent.py` using new SDK, clean `requirements.txt`.
</objective>

<context>
Load for context:
- .gsd/ARCHITECTURE.md
- nagrikseva/agent.py
- nagrikseva/requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Migrate agent.py to google.genai SDK</name>
  <files>nagrikseva/agent.py</files>
  <action>
    Migrate from `google.generativeai` to `google.genai`:
    
    1. Replace import:
       - OLD: `import google.generativeai as genai`
       - NEW: `from google import genai`
    
    2. Replace configuration:
       - OLD: `genai.configure(api_key=os.getenv("GEMINI_API_KEY"))`
       - NEW: `client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))`
    
    3. Replace model creation in `initialize_session()`:
       - OLD: `genai.GenerativeModel(model_name=..., system_instruction=...)`
              `model.start_chat(history=[])`
       - NEW: Use `client.chats.create(model="gemini-1.5-flash", config={"system_instruction": ...})`
              or use `client.models.generate_content` with chat-style history management
    
    4. Replace send_message in `get_response()`:
       - OLD: `session["chat"].send_message(user_message)` → `response.text`
       - NEW: `client.chats.send_message(...)` or equivalent
    
    5. Update `end_session()` to extract history from new chat object
    
    IMPORTANT: Keep the same function signatures — `initialize_session(call_sid, language)`,
    `get_response(call_sid, user_message)`, `end_session(call_sid)`, `detect_language(text)`,
    `get_session_language(call_sid)`. These are called by main.py.
    
    AVOID: Changing the sessions dict structure or function return types. main.py depends on these.
    
    NOTE: Check the google.genai docs for exact API — the chat interface may differ.
    If the new SDK doesn't have a direct chat equivalent, manage history manually by 
    storing messages in the sessions dict and sending full history each time.
  </action>
  <verify>
    `python3 -c "import py_compile; py_compile.compile('agent.py', doraise=True)"` passes.
    `grep "google.generativeai" agent.py` returns nothing.
    `grep "google.genai\|from google import genai" agent.py` returns a match.
  </verify>
  <done>
    agent.py uses google.genai SDK. No deprecation warnings on import.
    All 5 public functions maintain the same signatures.
  </done>
</task>

<task type="auto">
  <name>Cleanup requirements.txt</name>
  <files>nagrikseva/requirements.txt</files>
  <action>
    1. Replace `google-generativeai` with `google-genai`
    2. Remove `deepgram-sdk` (unused — placeholder for future)
    3. Remove `httpx` (unused)
    4. Keep a comment noting Deepgram as a future option:
       `# deepgram-sdk  # Uncomment for production Hindi STT`
  </action>
  <verify>
    `cat requirements.txt` shows `google-genai` not `google-generativeai`.
    No `deepgram-sdk` or `httpx` as active dependencies.
  </verify>
  <done>
    requirements.txt has 10 active dependencies (down from 12).
    google-genai replaces google-generativeai.
  </done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] `python3 -c "import py_compile; py_compile.compile('agent.py', doraise=True)"`
- [ ] `pip install -r requirements.txt` completes without error
- [ ] `grep "google.generativeai" agent.py` returns nothing
- [ ] Server starts without FutureWarning
</verification>

<success_criteria>
- [ ] agent.py imports from google.genai, not google.generativeai
- [ ] All 5 agent functions maintain same signatures
- [ ] requirements.txt has no unused packages
- [ ] Server starts clean (no deprecation warnings)
</success_criteria>
