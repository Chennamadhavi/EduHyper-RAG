"""
Streamlit Teacher Dashboard View for EduHyperRAG.
Features:
- Course creation and management
- Dynamic PDF/Text document upload & automated Phase 1-3 ingestion
- Hypergraph Knowledge Base Explorer for uploaded documents
- Teacher Analytics & Student QA Monitoring
"""

from pathlib import Path
import streamlit as st
from src.config import config
from src.database.models import (
    create_course,
    get_courses_by_teacher,
    get_documents_by_course,
    get_teacher_analytics_summary,
)
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.services.document_service import DocumentProcessingService


def render_teacher_dashboard() -> None:
    """Renders the Teacher Dashboard UI."""
    teacher_id = st.session_state["user_id"]
    username = st.session_state["username"]

    st.markdown(f"## 👨‍🏫 Teacher Control Center — Welcome, **{username}**!")
    st.write("Manage educational courses, upload PDFs for automated Hyper-RAG processing, inspect hypergraphs, and view student analytics.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Course Management",
        "📄 Document Upload & Processing",
        "🌐 Hypergraph Knowledge Explorer",
        "📊 Teacher Analytics & QA Logs",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: COURSE MANAGEMENT
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Create & Manage Courses")

        col_create, col_list = st.columns([1, 1])

        with col_create:
            st.markdown("### ➕ Create New Course")
            with st.form("create_course_form"):
                code = st.text_input("Course Code (e.g. BIO101, CS202)").strip()
                title = st.text_input("Course Title").strip()
                desc = st.text_area("Description / Syllabus Notes").strip()
                submit_course = st.form_submit_button("Create Course", type="primary")

                if submit_course:
                    if not code or not title:
                        st.warning("Please provide both course code and title.")
                    else:
                        try:
                            course = create_course(
                                course_code=code,
                                title=title,
                                description=desc,
                                teacher_id=teacher_id,
                            )
                            st.success(f"Successfully created course '{course['course_code']} - {course['title']}'!")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

        with col_list:
            st.markdown("### 📋 Your Active Courses")
            my_courses = get_courses_by_teacher(teacher_id)
            if my_courses:
                for c in my_courses:
                    with st.expander(f"**{c['course_code']}**: {c['title']}"):
                        st.write(f"**Description:** {c['description'] or 'No description provided.'}")
                        st.caption(f"Created: {c['created_at']}")
                        docs = get_documents_by_course(c["id"])
                        st.write(f"**Associated Documents:** {len(docs)}")
            else:
                st.info("No courses created yet. Use the form on the left to create your first course!")

    # -------------------------------------------------------------------------
    # TAB 2: DOCUMENT UPLOAD & DYNAMIC PROCESSING
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Dynamic PDF / Text Document Upload")
        st.write("Upload educational textbook chapters or lecture PDFs. The system will automatically execute **Phase 1 (Preprocessing)**, **Phase 2 (Entity & Hyperedge Extraction)**, and **Phase 3 (Hypergraph & ChromaDB Indexing)**.")

        my_courses = get_courses_by_teacher(teacher_id)
        if not my_courses:
            st.warning("Please create a course first before uploading documents.")
        else:
            course_dict = {f"{c['course_code']} - {c['title']}": c["id"] for c in my_courses}
            selected_course_name = st.selectbox("Select Target Course:", list(course_dict.keys()))
            selected_course_id = course_dict[selected_course_name]

            uploaded_file = st.file_uploader(
                "Choose a PDF or Text file:", type=["pdf", "txt", "md"], help="Supported formats: .pdf, .txt, .md"
            )

            doc_id_input = st.text_input(
                "Document Identifier (optional):",
                placeholder="e.g. photosynthesis_chapter",
                help="Unique alphanumeric ID for this document. If blank, derived from filename.",
            )

            if st.button("🚀 Process & Build Knowledge Base", type="primary"):
                if not uploaded_file:
                    st.warning("Please select a file to upload.")
                else:
                    file_bytes = uploaded_file.read()
                    file_name = uploaded_file.name

                    doc_service = DocumentProcessingService()
                    with st.spinner("Executing EduHyperRAG Automated Ingestion Pipeline (Phases 1-3)..."):
                        try:
                            res = doc_service.process_uploaded_file(
                                file_name=file_name,
                                file_bytes=file_bytes,
                                course_id=selected_course_id,
                                uploaded_by=teacher_id,
                                custom_doc_id=doc_id_input.strip() if doc_id_input else None,
                            )
                            st.success(f"🎉 Document '{res['filename']}' successfully processed and indexed!")
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Chunks Generated", res["num_chunks"])
                            c2.metric("Concept Entities Extracted", res["num_concepts"])
                            c3.metric("Hyperedges Constructed", res["num_hyperedges"])

                        except Exception as e:
                            st.error(f"Failed to process document: {str(e)}")

            st.markdown("---")
            st.markdown("### 📄 Managed Documents for Selected Course")
            course_docs = get_documents_by_course(selected_course_id)
            if course_docs:
                doc_table = []
                for d in course_docs:
                    doc_table.append({
                        "Doc ID": d["doc_id"],
                        "Filename": d["filename"],
                        "Status": d["status"],
                        "Chunks": d["num_chunks"],
                        "Concepts": d["num_concepts"],
                        "Hyperedges": d["num_hyperedges"],
                        "Uploaded At": d["created_at"],
                    })
                st.dataframe(doc_table, use_container_width=True)
            else:
                st.info("No documents uploaded for this course yet.")

    # -------------------------------------------------------------------------
    # TAB 3: HYPERGRAPH KNOWLEDGE EXPLORER
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Hypergraph Structural Explorer")
        my_courses = get_courses_by_teacher(teacher_id)
        all_docs = []
        if my_courses:
            for c in my_courses:
                all_docs.extend(get_documents_by_course(c["id"]))

        if not all_docs:
            st.info("No documents available. Upload a PDF in the 'Document Upload' tab to inspect its hypergraph.")
        else:
            doc_map = {f"{d['doc_id']} ({d['filename']})": d["doc_id"] for d in all_docs if d["status"] == "READY"}
            if not doc_map:
                st.info("No READY documents found.")
            else:
                sel_doc_label = st.selectbox("Select Document to Inspect:", list(doc_map.keys()))
                target_doc_id = doc_map[sel_doc_label]

                h_json_path = config.knowledge_base_dir / f"hypergraph_{target_doc_id}.json"
                if not h_json_path.exists():
                    h_json_path = config.knowledge_base_dir / "hypergraph.json"

                if h_json_path.exists():
                    query_engine = EduHypergraphQueryEngine(h_json_path)

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Concept Nodes (|V|)", len(query_engine.concepts))
                    c2.metric("Total Hyperedges (|E|)", len(query_engine.hyperedges))
                    c3.metric("Largest Hyperedge Size", query_engine.metadata.get("largest_hyperedge_size", 0))
                    c4.metric("Inspected Document", target_doc_id)

                    st.markdown("---")
                    col_inspect, col_viz = st.columns([1, 1])

                    with col_inspect:
                        st.markdown("### Concept Inspector")
                        selected_concept = st.selectbox(
                            "Select Concept Node:", sorted(list(query_engine.concepts.keys()))
                        )
                        if selected_concept:
                            node_info = query_engine.concepts[selected_concept]
                            st.write(f"**Name:** {node_info['name']}")
                            st.write(f"**Type:** {node_info['entity_type']}")
                            st.write(f"**Description:** {node_info['description']}")
                            st.write(f"**Source Chunks:** `{node_info.get('source_chunk_ids', [])}`")

                            st.markdown("**Connected Hyperedges:**")
                            matched_edges = query_engine.get_hyperedges_containing_concept(selected_concept)
                            for me in matched_edges:
                                st.markdown(f"- **{me['label']}** (Size={len(me['concepts'])}): {{{', '.join(me['concepts'])}}}")

                    with col_viz:
                        st.markdown("### Hypergraph Visualization Plot")
                        vis_img = config.knowledge_base_dir / "hypergraph_visualization.png"
                        if vis_img.exists():
                            st.image(str(vis_img), caption="HyperNetX Visualizer Map", use_container_width=True)
                        else:
                            st.info("HyperNetX visualization plot image not generated for this domain.")

    # -------------------------------------------------------------------------
    # TAB 4: TEACHER ANALYTICS & QA LOGS
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("System Quality & Student Query Analytics")
        analytics = get_teacher_analytics_summary(teacher_id)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Courses", analytics["total_courses"])
        c2.metric("Processed Documents", analytics["total_documents"])
        c3.metric("Total Student Questions", analytics["total_queries"])
        c4.metric("Avg Support Score", f"{analytics['avg_support_score']:.2f}")

        st.markdown("---")
        st.markdown("### ⚠️ Hallucination Monitoring")
        col_hal1, col_hal2 = st.columns([1, 1])

        with col_hal1:
            st.metric("Flagged / Regenerated Queries", analytics["flagged_queries"])
            st.write("Flagged queries are student questions where initial generation fell below factual evidence support thresholds.")

        with col_hal2:
            st.metric("Hallucination Flag Rate", f"{analytics['hallucination_rate_pct']:.1f}%")
            if analytics["hallucination_rate_pct"] < 10.0:
                st.success("High System Grounding Quality: Low hallucination rate detected across student queries.")
            else:
                st.warning("Notice: Some student queries required evidence verification re-retrieval passes.")

        st.markdown("---")
        st.markdown("### 🕒 Recent Student Questions")
        recent = analytics["recent_questions"]
        if recent:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No student queries recorded yet.")
