"""
Streamlit Web Application Entry Point for EduHyperRAG System.
Features:
- Role-Based Authentication & Access Control (Teacher / Student)
- Dynamic PDF Processing & Course Management (Teacher Dashboard)
- Document-Scoped Question Answering with Agentic Verification (Student Dashboard)
- Teacher System Analytics & QA Monitoring
- Benchmark Evaluation Dashboard (Phase 9)
"""

import sys
from pathlib import Path
import streamlit as st

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.views.auth_view import render_auth_view
from app.views.student_dashboard import render_student_dashboard
from app.views.teacher_dashboard import render_teacher_dashboard
from src.auth.authenticator import init_session_state, logout_user, seed_demo_data
from src.config import config
from src.utils.file_io import read_json

# Page Configuration
st.set_page_config(
    page_title="EduHyperRAG AI Tutor Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1E88E5; margin-bottom: 0px; }
    .sub-title { font-size: 1.05rem; color: #555555; margin-bottom: 20px; }
    .badge-ok { background-color: #E8F5E9; color: #2E7D32; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
    .badge-warn { background-color: #FFF3E0; color: #E65100; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
    .badge-err { background-color: #FFEBEE; color: #C62828; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
    .user-card { background-color: #F4F6F9; padding: 12px; border-radius: 8px; border-left: 4px solid #1E88E5; }
</style>
""", unsafe_allow_html=True)


def render_evaluation_dashboard() -> None:
    """Renders the Benchmark Evaluation Dashboard (Phase 9)."""
    st.subheader("System Evaluation Dashboard (Phase 9)")
    st.write("Comparative evaluation results across 6 RAG architectures evaluated on 10 benchmark queries.")

    results_json_path = config.project_root / "data" / "evaluation" / "results.json"
    chart_png_path = config.project_root / "data" / "evaluation" / "comparison_chart.png"

    if results_json_path.exists():
        bench_data = read_json(results_json_path)
        agg = bench_data.get("aggregated_metrics", {})
        imps = bench_data.get("improvements_vs_baselines", {})

        st.markdown("### Comparative Performance Table")
        table_data = []
        for arch_name, m in agg.items():
            table_data.append({
                "Architecture": arch_name,
                "Answer Correctness": m["answer_correctness"],
                "Faithfulness": m["faithfulness"],
                "Context Recall": m["context_recall"],
                "KMR (Missing Rate)": m["key_knowledge_missing_rate"],
                "HER (Hallucination Rate)": m["hallucination_error_rate"],
                "Latency (ms)": m["total_response_time_ms"],
            })
        st.dataframe(table_data, use_container_width=True)

        st.markdown("---")
        c_chart, c_imp = st.columns([1, 1])

        with c_chart:
            st.markdown("### Benchmark Metrics Chart")
            if chart_png_path.exists():
                st.image(str(chart_png_path), use_container_width=True)

        with c_imp:
            st.markdown("### Improvement Highlights vs Baselines")
            sel_baseline = st.selectbox("Select Baseline Comparator:", list(imps.keys()))
            if sel_baseline:
                b_imp = imps[sel_baseline]
                st.success(f"**Faithfulness Improvement:** `{b_imp['faithfulness']:+.2f}%`")
                st.success(f"**Hallucination (HER) Reduction:** `{b_imp['hallucination_error_rate']:+.2f}%`")
                st.info(f"**Context Recall:** `{b_imp['context_recall']:+.2f}%`")
                st.caption("Note: Multi-pass agentic verification adds latency to ensure zero-hallucination factual grounding.")
    else:
        st.error("Evaluation results.json not found. Please run Phase 9 evaluation first.")


def main():
    # Initialize Session State & Database Seeds
    init_session_state()
    seed_demo_data()

    st.markdown('<p class="main-title">🧬 EduHyperRAG Platform</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-title">Adaptive Hypergraph-Driven AI Tutor Platform with Role-Based Access Control & Agentic Verification</p>',
        unsafe_allow_html=True,
    )

    # Sidebar Navigation & Session Info
    st.sidebar.title("🧬 Navigation")

    if st.session_state.get("authenticated", False):
        user_role = st.session_state["user_role"]
        username = st.session_state["username"]

        st.sidebar.markdown(
            f"""
            <div class="user-card">
                <strong>Logged In User:</strong> {username}<br/>
                <strong>Role:</strong> {user_role.capitalize()}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("---")

        if user_role == "teacher":
            menu_option = st.sidebar.radio(
                "Select View:",
                ["👨‍🏫 Teacher Dashboard", "📊 Benchmark Evaluation", "🚪 Logout"],
            )
            if menu_option == "👨‍🏫 Teacher Dashboard":
                render_teacher_dashboard()
            elif menu_option == "📊 Benchmark Evaluation":
                render_evaluation_dashboard()
            elif menu_option == "🚪 Logout":
                logout_user()
                st.rerun()

        elif user_role == "student":
            menu_option = st.sidebar.radio(
                "Select View:",
                ["🎓 Student Portal", "📊 Benchmark Evaluation", "🚪 Logout"],
            )
            if menu_option == "🎓 Student Portal":
                render_student_dashboard()
            elif menu_option == "📊 Benchmark Evaluation":
                render_evaluation_dashboard()
            elif menu_option == "🚪 Logout":
                logout_user()
                st.rerun()

    else:
        menu_option = st.sidebar.radio(
            "Select View:",
            ["🔑 Portal Login", "📊 Benchmark Evaluation"],
        )
        if menu_option == "🔑 Portal Login":
            render_auth_view()
        elif menu_option == "📊 Benchmark Evaluation":
            render_evaluation_dashboard()

    st.sidebar.markdown("---")
    st.sidebar.caption("EduHyperRAG System v2.0")


if __name__ == "__main__":
    main()
