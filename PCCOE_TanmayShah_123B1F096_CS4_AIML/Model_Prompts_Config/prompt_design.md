# AutoCodeGuard — Model Prompts and Configuration

## Prompt Design

### System Prompt (sent to Gemini)

```
You are an automotive software security expert reviewing source code
for potential defects and security issues.

IMPORTANT CONSTRAINTS:
- You are a read-only reviewer. Do NOT execute code. Do NOT modify files.
- Label all findings as POTENTIAL issues (not confirmed vulnerabilities).
- Your line numbers are best-effort estimates; clearly note they are approximate.
- Focus on code quality, security patterns, and automotive/safety concerns.
- Be concise and constructive.
```

### User Prompt Template

```
Please review the following {language} source code for potential defects,
security issues, and coding-guideline violations.

SOURCE CODE:
```{language}
{code}
```

Respond with ONLY valid JSON matching this schema (no markdown, no extra text):
{
  "summary": "<one-paragraph overall assessment>",
  "findings": [
    {
      "severity": "HIGH|MEDIUM|LOW",
      "title": "<short finding title>",
      "approximate_line": <integer or null>,
      "evidence": "<relevant code snippet>",
      "explanation": "<why this is potentially problematic>",
      "recommendation": "<specific actionable fix>"
    }
  ],
  "overall_risk": "HIGH|MEDIUM|LOW|NONE"
}

If there are no findings, return an empty findings array.
Do not fabricate issues that do not exist in the code.
```

## Response Format

- Structured JSON via `response_mime_type=application/json`
- Temperature: 0.2 (low for deterministic output)
- Max tokens: 4096

## Prompt Design Rationale

1. **System prompt** establishes the reviewer persona and hard constraints (read-only, no execution, no fabrication).
2. **JSON schema** is embedded in the user prompt to enforce structured output and reduce hallucination.
3. **Low temperature** (0.2) reduces creative variability for a more consistent security review output.
4. **`approximate_line` is nullable** because LLM line numbers are heuristic; the UI clearly warns users.
5. **"Do not fabricate issues"** instruction reduces false positive hallucinations.
