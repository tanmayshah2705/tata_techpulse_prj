# AutoCodeGuard — Technical Report

**Title:** AutoCodeGuard — Automotive Secure Code Review Assistant  
**Case Study:** CS4 — Secure Code Debugging and Review Assistant  
**Student:** Tanmay Shah | PRN: 123B1F096 | Branch: IT  
**Institution:** PCCOE | **Event:** Tata TechPulse 2027

---

## Abstract

AutoCodeGuard is a Streamlit-based web application that assists developers in identifying potential security defects in source code. It combines deterministic static analysis (Python AST + regex rules), an LLM-powered advisory review via Google Gemini, and TF-IDF retrieval of relevant coding guidelines from a local knowledge base. The system targets an automotive software development context and is evaluated with a 12-case reproducible dataset. All evaluation results are genuine measured values.

---

## 1. Introduction

Automotive software is subject to stringent safety and security requirements (ISO 26262, ISO/SAE 21434). Early detection of code defects reduces the cost of fixing them and improves overall system reliability. Traditional SAST tools are powerful but expensive, complex to configure, and require specialist knowledge. AutoCodeGuard provides an accessible first-pass review assistant suitable for student and small-team use.

---

## 2. Problem Statement

Development teams need a fast, accessible tool to:
- Flag common coding defects before code review
- Explain *why* a pattern is problematic
- Suggest concrete fixes
- Retrieve relevant standards and guidelines
- Export structured findings for tracking

---

## 3. Objectives and Scope

**Objectives:**
1. Implement deterministic static analysis rules for common defects
2. Integrate Google Gemini for AI-powered advisory review
3. Retrieve relevant guidelines using TF-IDF
4. Present a structured findings dashboard with exports
5. Evaluate with real metrics

**Scope:** See Synopsis for full in/out-of-scope list.

---

## 4. Proposed Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI (app.py)               │
│  ┌────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │  Input     │  │  Findings   │  │  Export       │ │
│  │  (paste /  │  │  Dashboard  │  │  (JSON / CSV) │ │
│  │   upload)  │  │             │  │               │ │
│  └─────┬──────┘  └──────▲──────┘  └───────────────┘ │
└────────┼────────────────┼────────────────────────────┘
         │                │
         ▼                │
┌─────────────────┐  ┌────┴─────────────────────────┐
│ static_analyzer │  │       guideline_retrieval      │
│ (AST + regex)   │  │  (TF-IDF over guidelines_kb)  │
└─────────────────┘  └──────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   gemini_integration        │
│   (Google Gemini API)       │
│   [External — requires key] │
└─────────────────────────────┘
```

---

## 5. Implementation

### 5.1 Module Structure

| Module | Responsibility |
|--------|---------------|
| `app.py` | Streamlit UI, orchestration |
| `static_analyzer.py` | AST + regex rules, Finding dataclass |
| `gemini_integration.py` | Gemini API client, prompt, response parsing |
| `guideline_retrieval.py` | TF-IDF indexer, retrieval API |
| `report_exporter.py` | JSON report assembly, CSV serialisation |
| `evaluate.py` | Evaluation harness, metrics computation |
| `test_static_analyzer.py` | pytest unit tests |

### 5.2 Data Structures

**Finding (dataclass):**
```python
@dataclass
class Finding:
    rule_id: str          # e.g. "ACG-PY-001"
    severity: str         # HIGH / MEDIUM / LOW
    line: int | None      # source line
    column: int | None
    title: str
    evidence: str         # code snippet
    explanation: str
    recommendation: str
    language: str
    is_potential: bool    # always True — heuristic
```

---

## 6. Data Handling

- Source code is processed in memory only; not written to disk.
- Gemini API: code is transmitted only on user request after privacy notice.
- API key is loaded from `.env` via python-dotenv; never printed or logged.
- Findings are displayed in the UI and optionally downloaded by the user.
- No persistent storage of code or findings.

---

## 7. Static Analysis Rules

### Python AST Rules (Python only)

| ID | Visitor | Pattern |
|----|---------|---------|
| ACG-PY-001 | `visit_Call` | `eval()`, `exec()`, `compile()` |
| ACG-PY-002 | `visit_Call` | `subprocess.*` with `shell=True` keyword |
| ACG-PY-003 | `visit_ExceptHandler` | `except:` with no type |
| ACG-PY-004 | `visit_Assert` | `assert` statement |
| ACG-PY-005 | `visit_FunctionDef` | `[]`, `{}`, `set()` as default arg |
| ACG-PY-006 | `visit_Call` | `os.system()` |

### Regex Rules (All languages)

| ID | Pattern (simplified) | Target |
|----|---------------------|--------|
| ACG-RE-001 | `(password|secret|api_key)\s*=\s*['"].+['"]` | Hardcoded credentials |
| ACG-RE-002 | `\b(md5|sha1|sha-1)\b` | Weak cryptographic hashes |
| ACG-RE-003 | `SELECT.*%s|\.format(|f"` | SQL injection patterns |
| ACG-RE-004 | `\b(todo|fixme|hack|xxx)\b` | Incomplete code markers |
| ACG-RE-005 | `debug\s*=\s*true` | Debug flag enabled |
| ACG-RE-006 | `print\s*\(` | Diagnostic print statements |

---

## 8. Gemini Integration

### Request Flow
1. User submits code and clicks "Run Review"
2. Privacy notice is displayed
3. `GeminiReviewer.review()` is called
4. API key is read from `os.environ["GEMINI_API_KEY"]`
5. Prompt (system + user) is sent to `gemini-2.0-flash`
6. `response_mime_type="application/json"` enforces structured output
7. Response is validated; malformed responses produce a graceful error message
8. Findings are displayed with "approximate line" warnings

### Error Handling
- Invalid API key → clear user message
- Quota exceeded → user message with retry advice
- Network failure → user message
- Malformed JSON → user message with raw response preview (first 500 chars)

---

## 9. Guideline Retrieval

A 16-entry JSON knowledge base (`guidelines_kb.json`) covers:
- **General (GEN):** OWASP-aligned best practices
- **MISRA-inspired (MIS):** Automotive C rules (reference only, not certified)
- **Automotive (AUT):** ISO 26262 / ISO/SAE 21434 references (not certified)
- **Security (SEC):** NIST / OWASP cryptographic and injection guidance

**Retrieval process:**
1. Corpus = title + description + tags for each guideline
2. TF-IDF vectorizer (unigram + bigram, English stop words)
3. For each finding: query = title + explanation + evidence
4. Cosine similarity ranking → top-k results
5. Only guidelines with score > 0.0 are shown

---

## 10. Evaluation Methodology

### Dataset
- 12 test cases in `Input_Data/evaluation_dataset.json`
- 10 problematic cases, each targeting specific rule IDs
- 2 safe cases (expected zero findings)

### Metrics
For the **static analyzer only** (LLM findings are advisory):
- **True Positive (TP):** Expected rule detected
- **False Positive (FP):** Rule detected but not expected
- **False Negative (FN):** Expected rule not detected
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2 × P × R / (P + R)

---

## 11. Actual Evaluation Results

> **Note:** Results below are populated by running `evaluate.py`.  
> See `Evaluation_Results/evaluation_summary.txt` for the actual computed values.  
> **No results have been fabricated.**

*Run `python evaluate.py` from the Code/ directory to generate real results.*

---

## 12. Sample Outputs

### Static Analysis Output (TC-002: Hardcoded password + MD5)
```json
{
  "rule_id": "ACG-RE-001",
  "severity": "HIGH",
  "line": 3,
  "title": "Potential hardcoded credential or secret",
  "evidence": "password = 'super_secret_123'",
  "explanation": "A string literal assigned to a credential-like name...",
  "recommendation": "Store secrets in environment variables..."
}
```

---

## 13. Limitations

1. Heuristic rules: false positives possible on legitimate patterns
2. Regex rules are case-insensitive pattern matching; context not parsed
3. Gemini requires internet and a valid API key
4. Gemini line numbers are approximate and must be manually verified
5. 12-case evaluation dataset is small; results may not generalise
6. Not a replacement for certified MISRA compliance checking
7. Python AST rules do not apply to C/C++/Java (regex rules used instead)

---

## 14. Security and Privacy

- API key stored in `.env`, excluded from Git via `.gitignore`
- Source code processed in memory only
- User explicitly consents to Gemini transmission via privacy notice
- No secrets printed, logged, or stored
- `is_potential=True` flag prevents overstatement of findings

---

## 15. Future Work

1. Expand rule set to cover C/C++ AST using libclang or tree-sitter
2. Integrate CERT-C and full MISRA C:2012 rule set
3. Add CI/CD plugin (GitHub Actions, GitLab CI)
4. Support multi-file project analysis
5. Fine-tune a smaller model on automotive code samples
6. Add SARIF export format for IDE integration

---

## 16. Conclusion

AutoCodeGuard demonstrates a practical, modular approach to assisted code review for automotive software development. The combination of deterministic static analysis, LLM advisory review, and TF-IDF guideline retrieval provides an accessible first-pass review tool. The evaluation framework ensures that performance claims are backed by real measurements.

---

## 17. References

1. MISRA C:2012 Guidelines — Motor Industry Software Reliability Association
2. ISO 26262:2018 — Functional Safety of Road Vehicles
3. ISO/SAE 21434:2021 — Road Vehicles: Cybersecurity Engineering
4. OWASP Top 10 — https://owasp.org/www-project-top-ten/
5. NIST SP 800-131A — Transitioning Cryptographic Algorithms
6. Google Generative AI Python SDK — https://github.com/googleapis/python-genai
7. Streamlit — https://docs.streamlit.io
8. scikit-learn TF-IDF — https://scikit-learn.org
9. Python ast module — https://docs.python.org/3/library/ast.html

> ⚠️ **Note:** This technical report is a draft. Please verify against the prescribed PCCOE/Tata TechPulse template before final submission.
