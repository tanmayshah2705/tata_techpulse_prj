# AutoCodeGuard — Project Synopsis

**Title:** AutoCodeGuard — Automotive Secure Code Review Assistant  
**Case Study:** CS4 — Secure Code Debugging and Review Assistant  
**Student:** Tanmay Shah | PRN: 123B1F096 | Branch: IT  
**Institution:** Pimpri Chinchwad College of Engineering (PCCOE)  
**Event:** Tata TechPulse 2027  

---

## Problem Statement

Modern automotive software systems — from ADAS to infotainment ECUs — are increasingly developed in high-level languages such as C, C++, and Python. Security vulnerabilities and coding defects in these systems can lead to safety failures, data breaches, and regulatory non-compliance. Development teams often lack immediate, accessible tooling that combines static analysis, AI-assisted explanation, and coding-guideline retrieval in a single review workflow. AutoCodeGuard addresses this gap with a lightweight, explainable prototype.

---

## Objectives

1. Detect selected potentially unsafe code patterns using deterministic static analysis.
2. Provide AI-powered advisory findings and explanations using Google Gemini.
3. Retrieve relevant coding guidelines (MISRA-inspired, ISO 26262, ISO/SAE 21434 references) from a local knowledge base.
4. Present findings in a structured, actionable dashboard.
5. Export reproducible reports in JSON and CSV formats.
6. Evaluate the deterministic analyzer with measurable precision, recall, and F1 metrics.

---

## Scope

**In scope:**
- Python AST-based analysis rules (6 rules)
- Regex-based heuristic rules for all languages (6 rules)
- Gemini LLM-powered advisory review
- TF-IDF guideline retrieval from a 16-entry local knowledge base
- JSON/CSV report export
- Reproducible evaluation with 12 test cases
- Streamlit web UI with file upload and paste input

**Out of scope:**
- Certified automotive SAST (MISRA C:2012 full compliance)
- Real-time CI/CD pipeline integration
- Multi-file project analysis
- Custom model training or fine-tuning

---

## Methodology

1. **Static Analysis:** Python AST visitor pattern detects syntactic anti-patterns (eval/exec, shell injection, bare except, mutable defaults, assert misuse, os.system). Regex rules detect credential leakage, weak hashes, SQL injection patterns, debug flags, TODO markers, and print statements.

2. **LLM Integration:** Source code is transmitted to Google Gemini only on user request, after displaying a privacy notice. A structured JSON prompt with a read-only reviewer persona elicits findings with severity, evidence, explanation, and recommendations. Responses are validated before display.

3. **Guideline Retrieval:** A local JSON knowledge base of 16 guidelines (General, MISRA-inspired, Automotive, Security) is indexed with TF-IDF. Each finding triggers a cosine-similarity retrieval of the top-k most relevant guidelines.

4. **Evaluation:** A 12-case dataset (10 problematic + 2 safe) is used to evaluate the deterministic analyzer. Expected rule IDs per case allow computation of precision, recall, and F1.

---

## Architecture

```
User (Browser)
    │
    ▼
Streamlit UI (app.py)
    ├──► static_analyzer.py  ─── Python AST + Regex rules
    ├──► gemini_integration.py ── Google Gemini API (external)
    ├──► guideline_retrieval.py ─ TF-IDF over guidelines_kb.json
    └──► report_exporter.py  ─── JSON / CSV output
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| UI | Streamlit |
| LLM | Google Gemini (gemini-2.0-flash) |
| Static Analysis | Python `ast` module + `re` |
| Guideline Retrieval | scikit-learn TF-IDF |
| Knowledge Base | Local JSON |
| Export | json, csv (stdlib) |
| Testing | pytest |

---

## Dataset

- **Evaluation dataset:** 12 hand-crafted test cases in `Input_Data/evaluation_dataset.json`
- **Knowledge base:** 16 guidelines in `Code/guidelines_kb.json` covering General, MISRA-inspired, Automotive, and Security categories

---

## Evaluation Methodology

The deterministic static analyzer is evaluated by:
1. Running it on each test case
2. Comparing detected rule IDs to expected rule IDs
3. Computing per-rule and aggregate precision, recall, and F1

LLM (Gemini) findings are advisory and cannot be evaluated with standard precision/recall.

---

## Expected Outcomes

- Functional Streamlit application with full review workflow
- Static analyzer achieving high recall on designed test cases
- Gemini review providing human-readable advisory explanations
- Downloadable structured reports
- Measured evaluation results (not fabricated)

---

## Limitations

- Heuristic rules produce potential findings, not confirmed vulnerabilities
- Gemini requires an API key and internet connection
- Gemini line numbers are approximate
- Static rules cover a limited subset of possible defects
- Not suitable for automotive certification

---

## References

1. MISRA C:2012 — Motor Industry Software Reliability Association (reference only)
2. ISO 26262:2018 — Road vehicles: Functional Safety (reference only)
3. ISO/SAE 21434:2021 — Road vehicles: Cybersecurity Engineering (reference only)
4. OWASP Top 10 — https://owasp.org/www-project-top-ten/
5. NIST SP 800-131A — Transitioning Cryptographic Algorithms
6. Google Generative AI Python SDK — https://github.com/googleapis/python-genai
7. Streamlit Documentation — https://docs.streamlit.io

---

## Faculty Approval

**Faculty Mentor Name:** ______________________________

**Signature:** ______________________________

**Date:** ______________________________

> ⚠️ **Note:** This synopsis is a draft. Please verify against the prescribed PCCOE/Tata TechPulse template before final submission.
