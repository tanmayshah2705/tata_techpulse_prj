"""
report_exporter.py
AutoCodeGuard — Export findings to JSON and CSV formats.
"""

import csv
import json
import io
from datetime import datetime
from typing import List, Dict, Any


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def build_report(
    source_code: str,
    language: str,
    static_result: dict,
    gemini_result: dict | None,
    guidelines_map: dict,
) -> dict:
    """
    Assemble a full report dict ready for JSON serialisation.
    guidelines_map: {finding_key: [guideline, ...]}
    """
    return {
        "report_meta": {
            "tool": "AutoCodeGuard",
            "version": "1.0.0",
            "generated_at": _timestamp(),
            "language": language,
            "source_lines": len(source_code.splitlines()),
        },
        "static_analysis": static_result,
        "gemini_review": gemini_result or {},
        "guidelines": guidelines_map,
    }


def to_json_bytes(report: dict) -> bytes:
    """Return the report serialised as pretty-printed UTF-8 JSON bytes."""
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def static_findings_to_csv(static_findings: List[Dict[str, Any]]) -> str:
    """
    Convert static-analysis findings to a CSV string.
    Returns an empty string if no findings.
    """
    if not static_findings:
        return ""

    fieldnames = [
        "rule_id", "severity", "line", "column",
        "title", "evidence", "explanation", "recommendation", "language",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for f in static_findings:
        writer.writerow(f)
    return output.getvalue()


def gemini_findings_to_csv(gemini_findings: List[Dict[str, Any]]) -> str:
    """Convert Gemini findings to CSV string."""
    if not gemini_findings:
        return ""

    fieldnames = [
        "severity", "title", "approximate_line",
        "evidence", "explanation", "recommendation",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for f in gemini_findings:
        writer.writerow(f)
    return output.getvalue()
