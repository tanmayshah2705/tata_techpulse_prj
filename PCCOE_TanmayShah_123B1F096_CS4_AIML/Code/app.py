"""
app.py
AutoCodeGuard — Automotive Secure Code Review Assistant
Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import sys
import os

# Ensure sibling modules are importable when run from any directory
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import json

from static_analyzer import analyze
from guideline_retrieval import get_retriever
from gemini_integration import get_reviewer, MODEL_NAME
from report_exporter import (
    build_report,
    to_json_bytes,
    static_findings_to_csv,
    gemini_findings_to_csv,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AutoCodeGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🛡️ AutoCodeGuard")
    st.caption("Automotive Secure Code Review Assistant")
    st.divider()

    st.subheader("📋 Project Info")
    st.markdown("""
    **Student:** Tanmay Shah  
    **PRN:** 123B1F096  
    **Branch:** IT  
    **Case Study:** CS4  
    **Event:** Tata TechPulse 2027
    """)
    st.divider()

    st.subheader("⚙️ Configuration")
    language = st.selectbox(
        "Source language",
        options=["python", "c", "cpp", "java", "javascript", "other"],
        index=0,
    )
    run_gemini = st.toggle("Enable Gemini AI Review", value=True)
    top_k_guidelines = st.slider("Guidelines per finding", 1, 4, 2)

    st.divider()
    st.subheader("🤖 Model")
    st.code(MODEL_NAME, language=None)

    reviewer = get_reviewer()
    key_status = "✅ API key set" if reviewer.is_api_key_set() else "❌ API key missing"
    st.caption(key_status)

    st.divider()
    st.caption(
        "⚠️ **Static analysis findings are heuristic (potential issues only)**. "
        "This tool is a student prototype, not a certified SAST tool."
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("🛡️ AutoCodeGuard — Secure Code Review")
st.markdown(
    "Paste or upload source code below, then click **Run Review** "
    "to get static analysis findings and (optionally) an AI-powered review."
)

# --- Input tabs ---
tab_paste, tab_upload = st.tabs(["📝 Paste Code", "📂 Upload File"])

source_code = ""

with tab_paste:
    pasted = st.text_area(
        "Source code",
        height=300,
        placeholder="# Paste your source code here…",
        label_visibility="collapsed",
    )
    if pasted.strip():
        source_code = pasted

with tab_upload:
    uploaded = st.file_uploader(
        "Upload a source file",
        type=["py", "c", "cpp", "cc", "h", "java", "js", "ts", "txt"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        try:
            file_content = uploaded.read().decode("utf-8", errors="replace")
            source_code = file_content
            st.code(file_content[:2000], language=language)
            if len(file_content) > 2000:
                st.caption(f"(showing first 2000 of {len(file_content)} characters)")
        except Exception as exc:
            st.error(f"Could not read file: {exc}")

# --- Run button ---
st.divider()

run_btn = st.button("🔍 Run Review", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Privacy notice (shown before any Gemini call)
# ---------------------------------------------------------------------------

if run_gemini and run_btn:
    st.info(
        "🔒 **Privacy Notice:** When Gemini AI Review is enabled, the submitted "
        "source code is transmitted to **Google's Gemini API** for processing. "
        "Do not submit code containing passwords, personal data, or proprietary "
        "secrets you are not authorised to share with a third-party service. "
        "Google's data-handling policies apply. This tool does not store your code."
    )

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

if run_btn:
    if not source_code or not source_code.strip():
        st.error("⚠️ Please paste or upload source code before running a review.")
        st.stop()

    retriever = get_retriever()

    # ---- Static analysis ----
    with st.spinner("Running static analysis…"):
        static_result = analyze(source_code, language)

    static_findings = static_result.get("findings", [])
    syntax_error = static_result.get("syntax_error")

    if syntax_error:
        st.warning(f"⚠️ Syntax issue detected: {syntax_error}")

    # ---- Gemini review ----
    gemini_result = None
    if run_gemini:
        if not reviewer.is_api_key_set():
            st.error(
                "❌ GEMINI_API_KEY is not set. "
                "Add it to your `.env` file and restart the app."
            )
        else:
            with st.spinner(f"Requesting Gemini ({MODEL_NAME}) review…"):
                gemini_result = reviewer.review(source_code, language)

            if gemini_result.get("error"):
                st.error(f"❌ Gemini error: {gemini_result['error']}")

    # ---- Guideline retrieval ----
    guidelines_map: dict = {}
    for f in static_findings:
        key = f"{f['rule_id']}:{f['line']}"
        guidelines_map[key] = retriever.retrieve_for_finding(f, top_k=top_k_guidelines)

    if gemini_result:
        for gf in gemini_result.get("findings", []):
            key = f"gemini:{gf['title'][:40]}"
            guidelines_map[key] = retriever.retrieve(
                gf["title"] + " " + gf["explanation"],
                top_k=top_k_guidelines,
            )

    # ---- Report assembly ----
    report = build_report(source_code, language, static_result, gemini_result, guidelines_map)

    # ===========================================================
    # DASHBOARD
    # ===========================================================

    st.divider()
    st.header("📊 Findings Dashboard")

    # Summary metrics
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    n_static = len(static_findings)
    n_high = sum(1 for f in static_findings if f["severity"] == "HIGH")
    n_med  = sum(1 for f in static_findings if f["severity"] == "MEDIUM")
    n_low  = sum(1 for f in static_findings if f["severity"] == "LOW")

    gemini_findings = gemini_result.get("findings", []) if gemini_result else []
    n_gemini = len(gemini_findings)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Static Findings", n_static)
    col2.metric("🔴 HIGH", n_high)
    col3.metric("🟡 MEDIUM", n_med)
    col4.metric("🟢 LOW", n_low)
    col5.metric("🤖 Gemini Findings", n_gemini)

    if gemini_result and not gemini_result.get("error"):
        risk_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "NONE": "✅"}.get(
            gemini_result.get("overall_risk", ""), "❓"
        )
        st.markdown(
            f"**Gemini Overall Risk:** {risk_color} {gemini_result.get('overall_risk', 'N/A')}"
        )
        if gemini_result.get("summary"):
            st.info(f"**Gemini Summary:** {gemini_result['summary']}")

    # ---- Static Analysis Findings ----
    st.subheader("🔬 Static Analysis Findings (Deterministic)")
    st.caption(
        "⚠️ These are **potential issues** detected by heuristic rules. "
        "They are not confirmed vulnerabilities. Manual review is required."
    )

    if not static_findings:
        st.success("✅ No static analysis findings detected.")
    else:
        sorted_findings = sorted(
            static_findings, key=lambda f: severity_order.get(f["severity"], 9)
        )
        for idx, f in enumerate(sorted_findings):
            sev = f["severity"]
            icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
            with st.expander(
                f"{icon} [{f['rule_id']}] {f['title']} — Line {f['line'] or 'N/A'}",
                expanded=(sev == "HIGH"),
            ):
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.markdown(f"**Severity:** `{sev}`")
                    st.markdown(f"**Rule ID:** `{f['rule_id']}`")
                    if f.get("line"):
                        st.markdown(f"**Line:** {f['line']}")
                    if f.get("evidence"):
                        st.code(f["evidence"], language=language)
                with col_r:
                    st.markdown("**Explanation:**")
                    st.write(f["explanation"])
                    st.markdown("**Recommendation:**")
                    st.write(f["recommendation"])

                # Guidelines
                g_key = f"{f['rule_id']}:{f['line']}"
                related = guidelines_map.get(g_key, [])
                if related:
                    st.markdown("**📚 Related Guidelines:**")
                    for g in related:
                        badge = f"`{g['id']}` [{g['category']}]"
                        st.markdown(
                            f"- {badge} **{g['title']}** *(Score: {g['score']:.2f})*  \n"
                            f"  {g['description']}  \n"
                            f"  *Source: {g['source']}*"
                        )

    # ---- Gemini Findings ----
    if gemini_result and not gemini_result.get("error"):
        st.subheader("🤖 Gemini AI Review Findings")
        st.caption(
            "⚠️ LLM-generated findings are **advisory only**. Line numbers are approximate. "
            "They are not confirmed vulnerabilities."
        )

        if not gemini_findings:
            st.success("✅ Gemini found no issues.")
        else:
            for gf in sorted(
                gemini_findings, key=lambda f: severity_order.get(f["severity"], 9)
            ):
                sev = gf["severity"]
                icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
                with st.expander(
                    f"{icon} {gf['title']} — ~Line {gf.get('approximate_line', 'N/A')}",
                    expanded=(sev == "HIGH"),
                ):
                    col_l, col_r = st.columns([1, 1])
                    with col_l:
                        st.markdown(f"**Severity:** `{sev}`")
                        st.markdown(
                            f"**Approx. Line:** {gf.get('approximate_line', 'N/A')} "
                            "*(heuristic — verify manually)*"
                        )
                        if gf.get("evidence"):
                            st.code(gf["evidence"], language=language)
                    with col_r:
                        st.markdown("**Explanation:**")
                        st.write(gf["explanation"])
                        st.markdown("**Recommendation:**")
                        st.write(gf["recommendation"])

                    g_key = f"gemini:{gf['title'][:40]}"
                    related = guidelines_map.get(g_key, [])
                    if related:
                        st.markdown("**📚 Related Guidelines:**")
                        for g in related:
                            badge = f"`{g['id']}` [{g['category']}]"
                            st.markdown(
                                f"- {badge} **{g['title']}** *(Score: {g['score']:.2f})*  \n"
                                f"  {g['description']}  \n"
                                f"  *Source: {g['source']}*"
                            )

    # ---- Export ----
    st.divider()
    st.subheader("💾 Export Report")

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        json_bytes = to_json_bytes(report)
        st.download_button(
            label="⬇️ Download JSON Report",
            data=json_bytes,
            file_name="autocodeguard_report.json",
            mime="application/json",
            use_container_width=True,
        )

    with exp_col2:
        csv_data = static_findings_to_csv(static_findings)
        if csv_data:
            st.download_button(
                label="⬇️ Download Static CSV",
                data=csv_data,
                file_name="static_findings.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button(
                "⬇️ Download Static CSV",
                disabled=True,
                help="No static findings to export.",
                use_container_width=True,
            )

    with exp_col3:
        gem_csv = gemini_findings_to_csv(gemini_findings)
        if gem_csv:
            st.download_button(
                label="⬇️ Download Gemini CSV",
                data=gem_csv,
                file_name="gemini_findings.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button(
                "⬇️ Download Gemini CSV",
                disabled=True,
                help="No Gemini findings to export.",
                use_container_width=True,
            )

    # Raw JSON preview
    with st.expander("🔍 Raw JSON Report Preview"):
        st.json(report)

else:
    # Welcome state
    st.markdown("""
    ### How to use AutoCodeGuard

    1. **Paste** your source code in the text area above, or **upload** a file.
    2. Select the **source language** in the sidebar.
    3. Toggle **Gemini AI Review** on or off.
    4. Click **🔍 Run Review**.
    5. Review findings in the dashboard, then **download** the report.

    ---

    #### What this tool checks (Static Analysis)
    | Rule | What it detects |
    |------|----------------|
    | ACG-PY-001 | `eval()` / `exec()` usage |
    | ACG-PY-002 | `subprocess` with `shell=True` |
    | ACG-PY-003 | Bare `except:` clauses |
    | ACG-PY-004 | `assert` for input validation |
    | ACG-PY-005 | Mutable default arguments |
    | ACG-PY-006 | `os.system()` calls |
    | ACG-RE-001 | Hardcoded credentials |
    | ACG-RE-002 | Weak cryptographic hashes (MD5, SHA-1) |
    | ACG-RE-003 | String-formatted SQL queries |
    | ACG-RE-004 | TODO / FIXME markers |
    | ACG-RE-005 | `DEBUG = True` in code |
    | ACG-RE-006 | `print()` diagnostic statements |

    ---
    > ⚠️ This is a **student prototype** for educational purposes.
    > Findings are heuristic potential issues, not confirmed vulnerabilities.
    """)
