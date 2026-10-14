AutoCodeGuard — Video Demonstration Plan
=========================================
Student: Tanmay Shah | PRN: 123B1F096 | CS4
Event: Tata TechPulse 2027
Suggested Duration: 5–8 minutes

PREPARATION
-----------
Before recording:
1. Open a terminal in PCCOE_TanmayShah_123B1F096_CS4_AIML/Code/
2. Activate your virtual environment (if used)
3. Confirm .env contains your GEMINI_API_KEY
4. Run: streamlit run app.py
5. Wait for http://localhost:8501 to open in your browser
6. Have the evaluation_dataset.json and a sample file ready to upload


SEGMENT 1 — Introduction (≈ 30 seconds)
----------------------------------------
- State your name, PRN, branch, case study number
- Briefly explain the problem: "Automotive software teams need fast
  first-pass code review for safety and security issues."
- Show the app landing page


SEGMENT 2 — Paste Code Review (≈ 2 minutes)
---------------------------------------------
- Copy TC-002 code from Input_Data/evaluation_dataset.json:
    import hashlib
    password = 'super_secret_123'
    hash_val = hashlib.md5(password.encode()).hexdigest()

- Paste it into the app text area
- Select language: python
- Keep Gemini AI Review ENABLED
- Click "Run Review"
- Walk through:
  a) Privacy notice that appears before API call
  b) Static findings: ACG-RE-001 (hardcoded password), ACG-RE-002 (MD5)
  c) Each finding's evidence, explanation, recommendation
  d) Related guidelines panel (e.g., GEN-001, SEC-001)
  e) Gemini AI summary and findings (wait for API response)


SEGMENT 3 — File Upload (≈ 1 minute)
---------------------------------------
- Upload one of the sample .py files from Input_Data/ (if prepared)
- Show that the analyzer works on uploaded files
- Show the language selector


SEGMENT 4 — Safe Code (No Findings) (≈ 30 seconds)
-----------------------------------------------------
- Paste TC-010 from the dataset (the safe add() function)
- Run review
- Show: "✅ No static analysis findings detected."
- Explain that the tool avoids false positives on clean code


SEGMENT 5 — Export (≈ 30 seconds)
-----------------------------------
- Click "Download JSON Report"
- Open the downloaded file and briefly show its structure
- Mention CSV export is also available


SEGMENT 6 — Evaluation Results (≈ 1 minute)
---------------------------------------------
- Open a terminal
- Run: python evaluate.py
- Show the printed summary table with precision, recall, F1 values
- Emphasise: "These are real measured values from 12 test cases."
- Briefly show Evaluation_Results/evaluation_summary.txt


SEGMENT 7 — Architecture Walkthrough (≈ 1 minute)
---------------------------------------------------
- Open Code/ in editor; show the 5 main modules
- Briefly explain: app.py → static_analyzer.py → guideline_retrieval.py
  → gemini_integration.py → report_exporter.py
- Show model_config.json in Model_Prompts_Config/
- Mention that the API key is loaded from .env (never shown)


SEGMENT 8 — Conclusion (≈ 30 seconds)
---------------------------------------
- Summarise: static rules, Gemini integration, TF-IDF retrieval,
  evaluation with real metrics
- State limitations honestly: student prototype, heuristic findings
- Thank the judges


TIPS
----
- Keep the screen readable: use browser zoom 110-125% for Streamlit
- If Gemini is slow, have a screenshot ready of a previous run
- Do NOT show your .env file or API key on screen
- Speak clearly and slowly; the evaluators may not be familiar with
  every technical detail
