"""
test_static_analyzer.py
AutoCodeGuard — Unit tests for the deterministic static analyzer.

Run with:
    cd PCCOE_TanmayShah_123B1F096_CS4_AIML/Code
    python -m pytest test_static_analyzer.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from static_analyzer import analyze, analyze_python, analyze_generic


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def rule_ids(result: dict) -> set:
    return {f["rule_id"] for f in result.get("findings", [])}


# ---------------------------------------------------------------------------
# Python AST rules
# ---------------------------------------------------------------------------

class TestEvalExec:
    def test_eval_detected(self):
        code = "result = eval(user_input)\n"
        assert "ACG-PY-001" in rule_ids(analyze(code, "python"))

    def test_exec_detected(self):
        code = "exec('import os')\n"
        assert "ACG-PY-001" in rule_ids(analyze(code, "python"))

    def test_no_false_positive_safe_call(self):
        code = "x = print('hello')\n"
        result = analyze(code, "python")
        assert "ACG-PY-001" not in rule_ids(result)


class TestSubprocessShell:
    def test_shell_true_detected(self):
        code = "import subprocess\nsubprocess.run(cmd, shell=True)\n"
        assert "ACG-PY-002" in rule_ids(analyze(code, "python"))

    def test_shell_false_not_detected(self):
        code = "import subprocess\nsubprocess.run(['ls', '-la'], shell=False)\n"
        result = analyze(code, "python")
        assert "ACG-PY-002" not in rule_ids(result)


class TestBareExcept:
    def test_bare_except_detected(self):
        code = "try:\n    x = 1\nexcept:\n    pass\n"
        assert "ACG-PY-003" in rule_ids(analyze(code, "python"))

    def test_specific_except_not_flagged(self):
        code = "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        result = analyze(code, "python")
        assert "ACG-PY-003" not in rule_ids(result)


class TestAssert:
    def test_assert_detected(self):
        code = "def f(x):\n    assert x > 0\n    return x\n"
        assert "ACG-PY-004" in rule_ids(analyze(code, "python"))


class TestMutableDefault:
    def test_mutable_list_default_detected(self):
        code = "def f(items=[]):\n    items.append(1)\n    return items\n"
        assert "ACG-PY-005" in rule_ids(analyze(code, "python"))

    def test_mutable_dict_default_detected(self):
        code = "def f(d={}):\n    return d\n"
        assert "ACG-PY-005" in rule_ids(analyze(code, "python"))

    def test_none_default_safe(self):
        code = "def f(items=None):\n    items = items or []\n    return items\n"
        result = analyze(code, "python")
        assert "ACG-PY-005" not in rule_ids(result)


class TestOsSystem:
    def test_os_system_detected(self):
        code = "import os\nos.system('rm -rf /')\n"
        assert "ACG-PY-006" in rule_ids(analyze(code, "python"))


# ---------------------------------------------------------------------------
# Regex rules
# ---------------------------------------------------------------------------

class TestHardcodedCredentials:
    def test_password_literal_detected(self):
        code = "password = 'hunter2'\n"
        assert "ACG-RE-001" in rule_ids(analyze(code, "python"))

    def test_api_key_detected(self):
        code = "api_key = 'sk-abcdefg'\n"
        assert "ACG-RE-001" in rule_ids(analyze(code, "python"))

    def test_env_var_not_flagged(self):
        code = "import os\npassword = os.environ.get('DB_PASS')\n"
        result = analyze(code, "python")
        assert "ACG-RE-001" not in rule_ids(result)


class TestWeakHash:
    def test_md5_detected(self):
        code = "import hashlib\nh = hashlib.md5(b'data').hexdigest()\n"
        assert "ACG-RE-002" in rule_ids(analyze(code, "python"))

    def test_sha1_detected(self):
        code = "import hashlib\nh = hashlib.sha1(b'data').hexdigest()\n"
        assert "ACG-RE-002" in rule_ids(analyze(code, "python"))

    def test_sha256_not_flagged(self):
        code = "import hashlib\nh = hashlib.sha256(b'data').hexdigest()\n"
        result = analyze(code, "python")
        assert "ACG-RE-002" not in rule_ids(result)


class TestSQLInjection:
    def test_percent_format_detected(self):
        code = 'query = "SELECT * FROM users WHERE name = \'%s\'" % name\n'
        assert "ACG-RE-003" in rule_ids(analyze(code, "python"))


class TestTodo:
    def test_todo_detected(self):
        code = "# TODO: fix this security hole\ndef f(): pass\n"
        assert "ACG-RE-004" in rule_ids(analyze(code, "python"))


class TestDebugTrue:
    def test_debug_true_detected(self):
        code = "DEBUG = True\n"
        assert "ACG-RE-005" in rule_ids(analyze(code, "python"))


class TestPrint:
    def test_print_detected(self):
        code = "print('secret:', value)\n"
        assert "ACG-RE-006" in rule_ids(analyze(code, "python"))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_code_returns_no_findings(self):
        result = analyze("", "python")
        assert result["findings"] == []
        assert result["syntax_error"] is None

    def test_syntax_error_reported(self):
        code = "def broken(\n    pass\n"
        result = analyze(code, "python")
        assert result["syntax_error"] is not None

    def test_safe_code_no_findings(self):
        code = (
            "import logging\n"
            "logger = logging.getLogger(__name__)\n\n"
            "def add(a: int, b: int) -> int:\n"
            "    if not isinstance(a, int) or not isinstance(b, int):\n"
            "        raise TypeError('Both must be int')\n"
            "    return a + b\n"
        )
        result = analyze(code, "python")
        assert result["findings"] == []

    def test_generic_language_uses_regex_only(self):
        code = "password = 'secret'\n"
        result = analyze(code, "c")
        assert "ACG-RE-001" in rule_ids(result)

    def test_line_numbers_present(self):
        code = "eval(x)\n"
        result = analyze(code, "python")
        finding = next(f for f in result["findings"] if f["rule_id"] == "ACG-PY-001")
        assert finding["line"] == 1

    def test_no_duplicate_findings(self):
        code = "eval(x)\neval(y)\n"
        result = analyze(code, "python")
        pairs = [(f["rule_id"], f["line"]) for f in result["findings"]]
        assert len(pairs) == len(set(pairs))
