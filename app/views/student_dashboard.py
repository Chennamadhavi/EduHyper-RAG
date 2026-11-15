"""
Streamlit Student Dashboard View for EduHyperRAG.
Features:
- Enrolled Course & Document selection
- Document-scoped Question Answering with Agentic Verification (Phases 4-8)
- Real-time Evidence Display & Claim Map
- Personal Question Answering History
"""

from pathlib import Path
import streamlit as st

from src.agents.explanation_agent import EduExplainabilityEngine
from src.agents.verification_graph import run_agentic_verification
from src.config import config
from src.database.models import (
    get_all_courses,
    get_student_accessible_documents,
    get_student_enrolled_courses,
    get_student_qa_history,
    record_qa_history,
    enroll_student_in_course,
)
from src.evaluation.hallucination_checker import HallucinationChecker
from src.generation.answer_generator import EducationalAnswerGenerator
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine


def render_student_dashboard() -> None:
    """Renders the Student Dashboard UI."""
    student_id = st.session_state["user_id"]
    username = st.session_state["username"]

    st.markdown(f"## 🎓 Student Learning Portal — Welcome, **{username}**!")
    st.write("Ask educational questions about your course materials. Answers are verified using hypergraph evidence and multi-pass agentic verification.")

    tab1, tab2, tab3 = st.tabs([
        "❓ Question Answering & Verification",
        "🌐 Hypergraph Knowledge Explorer",
        "📜 Personal QA History",
    ])

    # Ensure student is enrolled in courses
    enrolled_courses = get_student_enrolled_courses(student_id)
    if not enrolled_courses:
        all_courses = get_all_courses()
        if all_courses:
            for c in all_courses:
                enroll_student_in_course(c["id"], student_id)
            enrolled_courses = get_student_enrolled_courses(student_id)

    # -------------------------------------------------------------------------
    # TAB 1: QUESTION ANSWERING & AGENTIC VERIFICATION
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Interactive Factual QA System")

        accessible_docs = get_student_accessible_documents(student_id)
        if not accessible_docs:
            st.info("No documents currently available in your enrolled courses. Please ask your teacher to upload course materials.")
        else:
            doc_options = {
                f"{d['course_code']}: {d['filename']} ({d['doc_id']})": (d["doc_id"], d["course_id"])
                for d in accessible_docs
            }
            selected_doc_label = st.selectbox("Select Target Course Document:", list(doc_options.keys()))
            selected_doc_id, selected_course_id = doc_options[selected_doc_label]

            # Sidebar Controls
            st.sidebar.header("⚙ System Configuration")
            max_iterations = st.sidebar.slider("Max Verification Iterations", min_value=1, max_value=4, value=2)
            min_support_score = st.sidebar.slider("Min Support Score", min_value=0.5, max_value=0.9, value=0.7, step=0.05)
            st.sidebar.markdown("---")
            st.sidebar.info(f"Active Document: **{selected_doc_id}**")

            # Sample Preset Questions
            sample_queries = [
                "Select a sample question...",
                "How does water photolysis work in Photosystem II to produce oxygen?",
                "What is the role of Rubisco in the Calvin cycle?",
                "How do C4 plants suppress photorespiration compared to C3 plants?",
                "What is the mechanism of dark matter annihilation in black hole thermodynamics?",
            ]
            selected_sample = st.selectbox("Sample Educational Questions:", sample_queries)
            default_input = selected_sample if selected_sample != "Select a sample question..." else ""

            user_query = st.text_input("Or enter your question:", value=default_input, placeholder="e.g. How does water split in Photosystem II?")

            if st.button("Submit Question", type="primary"):
                if not user_query.strip():
                    st.warning("Please enter a valid question.")
                else:
                    with st.spinner("Executing EduHyperRAG Agentic Workflow..."):
                        # 1. Agentic Verification Workflow with doc_id filter
                        verified_state = run_agentic_verification(
    user_query=user_query,
    max_iterations=max_iterations,
    doc_id=selected_doc_id,
    course_id=selected_course_id,
)

                        # 2. Answer Generation
                        answer_gen = EducationalAnswerGenerator()
                        answer_result = answer_gen.generate_answer(verified_state)

                        # 3. Hallucination Verification
                        checker = HallucinationChecker(min_support_score=min_support_score)
                        ver_report = checker.verify_answer(
                            answer_text=answer_result["answer"],
                            retrieved_chunks=verified_state["retrieved_chunks"],
                            retrieved_hyperedges=verified_state["retrieved_hyperedges"],
                            retrieved_concepts=verified_state["retrieved_concepts"],
                        )

                        # 4. Explainability Engine
                        exp_engine = EduExplainabilityEngine()
                        exp_report = exp_engine.generate_explanation(verified_state, answer_result, ver_report)

                        # 5. Record Interaction in Database History
                        record_qa_history(
                            student_id=student_id,
                            doc_id=selected_doc_id,
                            course_id=selected_course_id,
                            user_query=user_query,
                            generated_answer=answer_result["answer"],
                            confidence_level=exp_report.confidence_level,
                            support_score=ver_report.support_score,
                            verification_decision=ver_report.decision,
                        )

                    # Render Answer Results UI
                    st.markdown("---")
                    col_ans, col_meta = st.columns([3, 1])

                    with col_ans:
                        st.markdown("### Generated Answer")
                        st.markdown(answer_result["answer"])

                    with col_meta:
                        st.markdown("### System Status")
                        conf_level = exp_report.confidence_level
                        if conf_level == "High":
                            st.markdown('<span class="badge-ok">Confidence: HIGH</span>', unsafe_allow_html=True)
                        elif conf_level == "Medium":
                            st.markdown('<span class="badge-warn">Confidence: MEDIUM</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-err">Confidence: LOW/REFUSED</span>', unsafe_allow_html=True)

                        st.write(f"**Verification:** `{ver_report.decision}`")
                        st.write(f"**Support Score:** `{ver_report.support_score:.2f}`")
                        st.write(f"**Iterations:** `{verified_state['iteration_count']} / {max_iterations}`")

                    # Verification Badges
                    st.markdown("#### Verification Badges")
                    badge_cols = st.columns(len(exp_report.verification_badges))
                    for idx, badge in enumerate(exp_report.verification_badges):
                        badge_cols[idx].info(badge)

                    # Evidence Breakdown Tabs
                    ev_tab1, ev_tab2, ev_tab3, ev_tab4 = st.tabs([
                        "🧬 Supporting Concepts",
                        "🕸 High-Order Hyperedges",
                        "📄 Source Chunks",
                        "🔍 Claim Verification Map",
                    ])

                    with ev_tab1:
                        if exp_report.supporting_concepts:
                            for c in exp_report.supporting_concepts:
                                st.markdown(f"- **{c.name}** (`{c.entity_type}`): {c.description}")
                        else:
                            st.write("No concept nodes retrieved.")

                    with ev_tab2:
                        if exp_report.supporting_hyperedges:
                            for h in exp_report.supporting_hyperedges:
                                st.markdown(f"- **{h.label}** {{{', '.join(h.concepts)}}} [Size={h.cardinality}]")
                                st.caption(h.description)
                        else:
                            st.write("No hyperedges retrieved.")

                    with ev_tab3:
                        if exp_report.source_chunks:
                            for sc in exp_report.source_chunks:
                                with st.expander(f"Chunk ID: {sc.chunk_id} ({sc.source_file})"):
                                    st.write(sc.snippet)
                        else:
                            st.write("No source chunks available.")

                    with ev_tab4:
                        if exp_report.claim_evidences:
                            for ce in exp_report.claim_evidences:
                                st.markdown(f"**Claim:** *\"{ce.claim}\"* | Status: **{ce.status.upper()}** (Score: {ce.score})")
                                for ex in ce.supporting_excerpts:
                                    st.caption(f"Evidence: {ex}")
                                st.markdown("---")
                        else:
                            st.write("No claim verification map available.")

    # -------------------------------------------------------------------------
    # TAB 2: HYPERGRAPH KNOWLEDGE EXPLORER
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Hypergraph Structural Explorer")
        accessible_docs = get_student_accessible_documents(student_id)
        if accessible_docs:
            doc_options = {f"{d['filename']} ({d['doc_id']})": d["doc_id"] for d in accessible_docs}
            sel_doc_label = st.selectbox("Select Document to Explore:", list(doc_options.keys()))
            target_doc_id = doc_options[sel_doc_label]

            h_json_path = config.knowledge_base_dir / f"hypergraph_{target_doc_id}.json"
            if not h_json_path.exists():
                h_json_path = config.knowledge_base_dir / "hypergraph.json"

            if h_json_path.exists():
                query_engine = EduHypergraphQueryEngine(h_json_path)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Concept Nodes (|V|)", len(query_engine.concepts))
                c2.metric("Total Hyperedges (|E|)", len(query_engine.hyperedges))
                c3.metric("Largest Hyperedge Size", query_engine.metadata.get("largest_hyperedge_size", 0))
                c4.metric("Active Domain", target_doc_id)

                st.markdown("---")
                selected_concept = st.selectbox("Select Concept Node:", sorted(list(query_engine.concepts.keys())))
                if selected_concept:
                    node_info = query_engine.concepts[selected_concept]
                    st.write(f"**Name:** {node_info['name']}")
                    st.write(f"**Type:** {node_info['entity_type']}")
                    st.write(f"**Description:** {node_info['description']}")

                    st.markdown("**Connected Hyperedges:**")
                    matched_edges = query_engine.get_hyperedges_containing_concept(selected_concept)
                    for me in matched_edges:
                        st.markdown(f"- **{me['label']}** (Size={len(me['concepts'])}): {{{', '.join(me['concepts'])}}}")
            else:
                st.error("Hypergraph file not found for selected document.")

    # -------------------------------------------------------------------------
    # TAB 3: PERSONAL QUESTION HISTORY
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Your Personal Question History")
        history = get_student_qa_history(student_id)
        if history:
            for item in history:
                with st.expander(f"❓ **{item['user_query']}** ({item['timestamp']})"):
                    st.write(f"**Course Code:** {item.get('course_code', 'N/A')} | **Doc ID:** {item['doc_id']}")
                    st.write(f"**Confidence Level:** `{item['confidence_level']}` | **Support Score:** `{item['support_score']:.2f}`")
                    st.markdown("**Generated Answer:**")
                    st.markdown(item["generated_answer"])
        else:
            st.info("No personal question history recorded yet. Ask a question in the first tab to see your log here!")
