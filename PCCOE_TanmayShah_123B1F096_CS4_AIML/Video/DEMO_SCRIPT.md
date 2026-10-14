# AutoCodeGuard — Video Demonstration Script & Recording Guide

**Student:** Tanmay Shah | **PRN:** 123B1F096 | **Branch:** IT  
**Case Study:** CS4 — Secure Code Debugging and Review Assistant  
**Event:** Tata TechPulse 2027  
**Suggested Video Duration:** 5 to 7 Minutes  

---

## 1. Quick Recording Guide (Shortest Practical Method)

Use the built-in screen recorder on Windows 10/11 without installing any third-party tools:

1. **Option A (Windows Game Bar - Recommended & Free):**
   * Press `Windows Key + G` (or `Windows Key + Alt + R` to directly start/stop recording).
   * Ensure your microphone is toggled ON to record your voice commentary.
   * Default output video is saved to `C:\Users\<user>\Videos\Captures\`.
   * Move or copy the resulting `.mp4` file into:
     `PCCOE_TanmayShah_123B1F096_CS4_AIML/Video/demo_video.mp4`

2. **Option B (OBS Studio or Microsoft Clipchamp):**
   * If installed, record the single browser window (`http://localhost:8501`) and your terminal.

---

## 2. Timed Demonstration Walkthrough

### Segment 1: Introduction & Architecture (0:00 – 1:00)
* **What to Show:** Project title slide or Streamlit landing screen (`http://localhost:8501`).
* **What to Say:**
  > *"Hello, I am Tanmay Shah, PRN 123B1F096, Department of IT at PCCOE. This is AutoCodeGuard, a secure code review assistant developed for Tata TechPulse 2027 under Case Study CS4.*
  > *Automotive embedded software requires stringent adherence to safety and security practices. AutoCodeGuard combines deterministic static analysis using Python AST and regex, TF-IDF retrieval of relevant MISRA and ISO guidelines, and advisory AI code review powered by Google Gemini (gemini-flash-lite-latest). All findings are presented in an actionable dashboard with report export capabilities."*

### Segment 2: Reviewing Vulnerable ECU Code (1:00 – 2:30)
* **Action:**
  1. Go to the **Upload File** tab in Streamlit.
  2. Upload `Input_Data/sample_vulnerable_ecu.py`.
  3. Ensure **Enable Gemini AI Review** is toggled **ON**.
  4. Click **🔍 Run Review**.
* **Expected Observations:**
  * **Privacy Notice** appears, explicitly stating code is transmitted securely to Google's Gemini endpoint without persistent cloud storage.
  * **Dashboard Metrics** appear:
    * Static Findings detected (Hardcoded API keys, MD5 broken crypto, shell=True injection, eval() execution, mutable default, bare except).
    * Gemini findings and summary assessment displayed.
  * **Guideline References:** Each finding shows matched guidelines from the local knowledge base (`GEN-001`, `GEN-004`, `SEC-001`, `MIS-001`).
* **What to Say:**
  > *"Notice how the deterministic static analyzer catches the syntax and pattern issues with exact line numbers, while Gemini simultaneously explains the broader architectural impact and potential exploit scenarios. The TF-IDF retrieval engine automatically matches these findings to our local automotive standards knowledge base."*

### Segment 3: Reviewing Safe Telematics Code (2:30 – 3:30)
* **Action:**
  1. Go to the **Upload File** tab.
  2. Upload `Input_Data/sample_safe_telematics.py`.
  3. Click **🔍 Run Review**.
* **Expected Observations:**
  * Static findings count: **0** (`✅ No static analysis findings detected`).
  * Gemini confirms clean, hardened code with **NONE / LOW** overall risk.
* **What to Say:**
  > *"Here we upload our hardened telematics module. AutoCodeGuard demonstrates zero false positives on this compliant implementation, proving that rules do not indiscriminately trigger on safe code."*

### Segment 4: Report Export (3:30 – 4:15)
* **Action:**
  1. Scroll down to the **Export Report** section.
  2. Click **⬇️ Download JSON Report** and **⬇️ Download Static CSV**.
  3. Briefly open the downloaded JSON in an editor or browser.
* **What to Say:**
  > *"Developers and auditors can export full structured JSON reports or CSV tables for automated integration into security ticketing systems or triage pipelines."*

### Segment 5: Automated Evaluation & Test Harness (4:15 – 5:15)
* **Action:**
  1. Switch to the terminal.
  2. Run `python -m pytest test_static_analyzer.py -v`.
  3. Run `python evaluate.py`.
* **Expected Observations:**
  * Pytest passes all 28 unit tests.
  * Evaluation script runs across 12 test cases (10 flawed + 2 clean), displaying 15 True Positives, 0 False Positives, and 0 False Negatives on the benchmark suite.
* **What to Say:**
  > *"All 28 unit tests pass in 0.1 seconds. The automated evaluation harness processes 12 benchmark cases, yielding verified 1.0 precision and recall against our synthetic reference dataset."*

### Segment 6: Conclusion & Limitations (5:15 – 6:00)
* **What to Say:**
  > *"In conclusion, AutoCodeGuard offers a functional, explainable prototype for automotive security triage. As an honest prototype disclosure: static rules cover high-risk heuristic patterns, and LLM suggestions are advisory and must be verified by a safety engineer. Thank you."*
