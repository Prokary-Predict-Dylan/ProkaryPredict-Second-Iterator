# app.py
import streamlit as st
from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import features_to_blocks
from viz import blocks_to_figure
from export_pdf import (
    export_gene_reaction_pdf,
    export_fasta_summary_pdf
)
import time

st.set_page_config(page_title="ProkaryPredict Second Iterator", layout="wide")
st.title("ProkaryPredict — (Second Iterator)")

# ---------------------------
# Session state
# ---------------------------
for k in ["confirm_export", "do_export", "input_type", "model"]:
    st.session_state.setdefault(k, None)

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader(
        "GenBank / FASTA / SBML",
        accept_multiple_files=False
    )

    st.markdown("---")
    st.header("Export")
    export_name = st.text_input("PDF filename", "prokarypredict_report")

    if st.button("Export PDF"):
        st.session_state["confirm_export"] = True

# ---------------------------
# File parsing
# ---------------------------
feature_list = []

if uploaded:
    fn = uploaded.name.lower()

    try:
        if fn.endswith((".fa", ".fasta")):
            feature_list = parse_fasta(uploaded)
            st.session_state["input_type"] = "fasta"
            st.success(f"Parsed FASTA: {len(feature_list)} sequences")

        elif fn.endswith((".gb", ".gbk", ".genbank")):
            feature_list = parse_genbank(uploaded)
            st.session_state["input_type"] = "genbank"
            st.success(f"Parsed GenBank: {len(feature_list)} features")

        elif fn.endswith((".xml", ".sbml")):
            sbml = parse_sbml(uploaded)
            st.session_state["model"] = sbml["cobra_model"]
            st.session_state["input_type"] = "sbml"

            for i, g in enumerate(sbml["genes"]):
                feature_list.append({
                    "id": g["id"],
                    "name": g["name"],
                    "product": g["product"],
                    "start": i * 200,
                    "end": i * 200 + 100,
                    "length": 100,
                    "source": "sbml"
                })

            st.success(f"Parsed SBML: {len(feature_list)} genes")

        else:
            st.error("Unsupported file type")

    except Exception as e:
        st.error(f"Parsing failed: {e}")

# ---------------------------
# Visualization (layered system)
# ---------------------------
if feature_list:
    blocks = features_to_blocks(feature_list)

    # ---- Layer selector ----
    layer = st.sidebar.radio(
        "Color by layer",
        ["structural", "function", "evidence", "context"],
        index=0
    )

    # ---- Data completeness filters ----
    flags = ["has_sequence", "has_coordinates", "has_product", "has_reactions"]
    active_flags = st.sidebar.multiselect(
        "Filter by data completeness",
        flags,
        default=[]
    )

    # ---- Apply filters + active color ----
    filtered = []
    for b in blocks:
        if all(b["data_flags"].get(f, False) for f in active_flags):
            b["active_color"] = b["colors"][layer]
            filtered.append(b)

    st.subheader("Block visualization")
    fig = blocks_to_figure(filtered)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Block data"):
        st.json(filtered)

# ---------------------------
# Export confirmation
# ---------------------------
if st.session_state["confirm_export"]:
    st.warning("Are you sure you want to export?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, export"):
            st.session_state["do_export"] = True
            st.session_state["confirm_export"] = False
    with c2:
        if st.button("Cancel"):
            st.session_state["confirm_export"] = False

# ---------------------------
# Export execution
# ---------------------------
if st.session_state["do_export"]:
    itype = st.session_state["input_type"]

    if itype == "sbml" and st.session_state.get("model"):
        pdf = export_gene_reaction_pdf(st.session_state["model"])

    elif itype == "fasta":
        pdf = export_fasta_summary_pdf(feature_list)

    else:
        st.error("Export not available for this file type")
        pdf = None

    if pdf:
        st.download_button(
            "Download PDF",
            data=pdf,
            file_name=f"{export_name}.pdf",
            mime="application/pdf"
        )

    st.session_state["do_export"] = False
