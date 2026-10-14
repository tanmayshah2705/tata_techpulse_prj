"""
static_analyzer.py
AutoCodeGuard — Deterministic static analysis rules.

Rules detect potentially unsafe patterns and return structured findings.
Findings are labelled as POTENTIAL issues (not confirmed vulnerabilities).
Execution of user code never occurs.
"""

import ast
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Finding:
    rule_id: str
    severity: str            # HIGH / MEDIUM / LOW
    line: Optional[int]
    column: Optional[int]
    title: str
    evidence: str            # code snippet / pattern matched
    explanation: str
    recommendation: str
    language: str = "python"
    is_potential: bool = True  # always True — findings are heuristic

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Python AST-based rules
# ---------------------------------------------------------------------------

class _PythonASTVisitor(ast.NodeVisitor):
    """Walks Python AST and collects findings."""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.findings: List[Finding] = []

    def _snippet(self, lineno: int) -> str:
        if lineno and 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    # ACG-PY-001: eval() / exec() usage
    def visit_Call(self, node: ast.Call):
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in ("eval", "exec", "compile"):
            self.findings.append(Finding(
                rule_id="ACG-PY-001",
                severity="HIGH",
                line=node.lineno,
                column=node.col_offset,
                title=f"Potential use of dynamic code execution: {func_name}()",
                evidence=self._snippet(node.lineno),
                explanation=(
                    f"`{func_name}()` can execute arbitrary code. "
                    "If user-controlled data is passed, this is a code-injection risk."
                ),
                recommendation=(
                    f"Avoid `{func_name}()`. Replace with explicit logic, "
                    "safe parsers (e.g., ast.literal_eval for data), or dedicated APIs."
                ),
            ))

        # ACG-PY-002: subprocess with shell=True
        if func_name in ("run", "call", "Popen", "check_output", "check_call", "system"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(Finding(
                        rule_id="ACG-PY-002",
                        severity="HIGH",
                        line=node.lineno,
                        column=node.col_offset,
                        title="Potential shell injection: subprocess called with shell=True",
                        evidence=self._snippet(node.lineno),
                        explanation=(
                            "shell=True passes the command string to the OS shell, "
                            "enabling command injection if any part is user-controlled."
                        ),
                        recommendation=(
                            "Pass a list of arguments instead: "
                            "subprocess.run(['cmd', 'arg1'], shell=False). "
                            "Validate any user-supplied values before use."
                        ),
                    ))

        # ACG-PY-006: os.system()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "system":
                self.findings.append(Finding(
                    rule_id="ACG-PY-006",
                    severity="HIGH",
                    line=node.lineno,
                    column=node.col_offset,
                    title="Potential use of os.system() — command injection risk",
                    evidence=self._snippet(node.lineno),
                    explanation=(
                        "os.system() passes the string directly to the OS shell. "
                        "User-controlled content enables command injection."
                    ),
                    recommendation=(
                        "Prefer subprocess.run() with a list of arguments and shell=False."
                    ),
                ))

        self.generic_visit(node)

    # ACG-PY-003: Bare except clause
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.findings.append(Finding(
                rule_id="ACG-PY-003",
                severity="MEDIUM",
                line=node.lineno,
                column=node.col_offset,
                title="Potential issue: bare except clause hides all exceptions",
                evidence=self._snippet(node.lineno),
                explanation=(
                    "A bare `except:` catches every exception, including "
                    "SystemExit and KeyboardInterrupt, masking real errors."
                ),
                recommendation=(
                    "Catch specific exception types: `except ValueError as e:`. "
                    "Log or re-raise exceptions appropriately."
                ),
            ))
        self.generic_visit(node)

    # ACG-PY-004: assert statements in non-test code
    def visit_Assert(self, node: ast.Assert):
        self.findings.append(Finding(
            rule_id="ACG-PY-004",
            severity="LOW",
            line=node.lineno,
            column=node.col_offset,
            title="Potential issue: assert statement (disabled with -O flag)",
            evidence=self._snippet(node.lineno),
            explanation=(
                "assert statements are removed when Python runs with -O or -OO. "
                "Do not use assert for security or input-validation checks."
            ),
            recommendation=(
                "Replace with explicit `if` checks and raise appropriate exceptions "
                "for input validation and security-critical conditions."
            ),
        ))
        self.generic_visit(node)

    # ACG-PY-005: Mutable default arguments
    def visit_FunctionDef(self, node: ast.FunctionDef):
        for default in node.args.defaults + node.args.kw_defaults:
            if default is None:
                continue
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(Finding(
                    rule_id="ACG-PY-005",
                    severity="LOW",
                    line=node.lineno,
                    column=node.col_offset,
                    title=f"Potential issue: mutable default argument in `{node.name}()`",
                    evidence=self._snippet(node.lineno),
                    explanation=(
                        "Mutable defaults (list, dict, set) are shared across all calls. "
                        "This causes unexpected state persistence between calls."
                    ),
                    recommendation=(
                        "Use `None` as the default and initialise inside the function: "
                        "`def f(x=None): x = x or []`"
                    ),
                ))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


# ---------------------------------------------------------------------------
# Regex-based rules (language-agnostic heuristics)
# ---------------------------------------------------------------------------

_REGEX_RULES = [
    {
        "rule_id": "ACG-RE-001",
        "severity": "HIGH",
        "title": "Potential hardcoded credential or secret",
        "pattern": re.compile(
            r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']{3,}["\']'
        ),
        "explanation": (
            "A string literal assigned to a credential-like name was detected. "
            "Hardcoded secrets can be extracted from source code, binaries, or version history."
        ),
        "recommendation": (
            "Store secrets in environment variables or a secrets manager. "
            "Never commit secrets to version control."
        ),
    },
    {
        "rule_id": "ACG-RE-002",
        "severity": "HIGH",
        "title": "Potential use of weak cryptographic hash: MD5 or SHA-1",
        "pattern": re.compile(r'(?i)\b(md5|sha1|sha-1)\b'),
        "explanation": (
            "MD5 and SHA-1 are cryptographically broken and must not be used for "
            "security-sensitive purposes such as password hashing or digital signatures."
        ),
        "recommendation": (
            "Use SHA-256 or SHA-3 (hashlib.sha256 / hashlib.sha3_256). "
            "For password storage, use bcrypt, scrypt, or argon2."
        ),
    },
    {
        "rule_id": "ACG-RE-003",
        "severity": "HIGH",
        "title": "Potential SQL injection: string formatting in SQL query",
        "pattern": re.compile(
            r'(?i)(select|insert|update|delete|drop)\s.+(%s|%d|\.format\(|f["\'])',
        ),
        "explanation": (
            "Building SQL queries using string formatting or f-strings with "
            "external data enables SQL injection attacks."
        ),
        "recommendation": (
            "Use parameterised queries: cursor.execute('SELECT * FROM t WHERE id=?', (val,)). "
            "Never concatenate or format user data directly into SQL strings."
        ),
    },
    {
        "rule_id": "ACG-RE-004",
        "severity": "MEDIUM",
        "title": "Potential TODO / FIXME left in production code",
        "pattern": re.compile(r'(?i)\b(todo|fixme|hack|xxx)\b'),
        "explanation": (
            "TODO/FIXME comments often mark incomplete or insecure code paths "
            "that should be resolved before production deployment."
        ),
        "recommendation": (
            "Resolve the marked issue or create a tracked issue. "
            "Remove placeholders before release."
        ),
    },
    {
        "rule_id": "ACG-RE-005",
        "severity": "HIGH",
        "title": "Potential debug mode enabled in production",
        "pattern": re.compile(r'(?i)\bdebug\s*=\s*true\b'),
        "explanation": (
            "Debug mode exposes detailed error messages, stack traces, and "
            "sometimes interactive consoles to potential attackers."
        ),
        "recommendation": (
            "Set DEBUG=False in production. Control via an environment variable, "
            "never hardcode True for production builds."
        ),
    },
    {
        "rule_id": "ACG-RE-006",
        "severity": "MEDIUM",
        "title": "Potential use of print() for diagnostic output",
        "pattern": re.compile(r'\bprint\s*\('),
        "explanation": (
            "print() statements left in production code may inadvertently leak "
            "sensitive information (credentials, internal state) to stdout/logs."
        ),
        "recommendation": (
            "Replace print() with a structured logging framework "
            "(Python logging module). Control log levels per environment."
        ),
    },
]


def _apply_regex_rules(source_lines: List[str]) -> List[Finding]:
    findings = []
    for lineno, line in enumerate(source_lines, start=1):
        for rule in _REGEX_RULES:
            if rule["pattern"].search(line):
                findings.append(Finding(
                    rule_id=rule["rule_id"],
                    severity=rule["severity"],
                    line=lineno,
                    column=None,
                    title=rule["title"],
                    evidence=line.rstrip(),
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                ))
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_python(source_code: str) -> List[Finding]:
    """
    Run Python AST-based and regex rules on *source_code*.
    Returns a list of Finding objects (may be empty).
    Raises ValueError with a user-friendly message on parse failure.
    """
    source_lines = source_code.splitlines()
    findings: List[Finding] = []

    # AST analysis
    try:
        tree = ast.parse(source_code)
        visitor = _PythonASTVisitor(source_lines)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError as exc:
        raise ValueError(f"Python syntax error at line {exc.lineno}: {exc.msg}") from exc

    # Regex analysis
    findings.extend(_apply_regex_rules(source_lines))

    # Deduplicate by (rule_id, line)
    seen = set()
    unique = []
    for f in findings:
        key = (f.rule_id, f.line)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def analyze_generic(source_code: str, language: str = "unknown") -> List[Finding]:
    """
    Run only regex-based rules (for non-Python languages).
    """
    source_lines = source_code.splitlines()
    findings = _apply_regex_rules(source_lines)

    seen = set()
    unique = []
    for f in findings:
        key = (f.rule_id, f.line)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    for f in unique:
        f.language = language
    return unique


def analyze(source_code: str, language: str = "python") -> dict:
    """
    Entry point.  Returns a dict ready for JSON serialisation:
    {
        "language": str,
        "findings": [Finding.to_dict(), ...],
        "syntax_error": str | None
    }
    """
    if not source_code or not source_code.strip():
        return {"language": language, "findings": [], "syntax_error": None}

    syntax_error = None
    findings: List[Finding] = []

    if language == "python":
        try:
            findings = analyze_python(source_code)
        except ValueError as exc:
            syntax_error = str(exc)
            # still run regex rules even on parse failure
            findings = _apply_regex_rules(source_code.splitlines())
    else:
        findings = analyze_generic(source_code, language)

    return {
        "language": language,
        "findings": [f.to_dict() for f in findings],
        "syntax_error": syntax_error,
    }
