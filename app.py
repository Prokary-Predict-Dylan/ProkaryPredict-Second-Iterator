import streamlit as st
import os
import json

from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import (
    features_to_blocks,
    STRUCTURAL_COLORS,
    FUNCTION_COLORS
)
from viz import blocks_to_figure
from export_pdf import export_gene_reaction_pdf, export_fasta_summary_pdf


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ProkaryPredict — (0.2)",
    layout="wide"
)
st.title("ProkaryPredict — (0.2)")


# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
DEFAULTS = {
    "feature_list": [],
    "input_type": None,
    "model": None,
    "confirm_export": False,
    "do_export": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.header("Upload")

    uploaded = st.file_uploader(
        "GenBank / FASTA / SBML",
        accept_multiple_files=False
    )

    st.markdown("---")

    st.header("Visualization")

    color_layer = st.radio(
        "Color by",
        ["structural", "functional"],
        index=0
    )

    st.markdown("---")

    st.header("Export")

    export_name = st.text_input(
        "PDF filename",
        "prokarypredict_report"
    )

    if st.button("Export PDF"):
        st.session_state["confirm_export"] = True


# =========================================================
# FILE PARSING
# =========================================================
if uploaded:
    name = uploaded.name.lower()

    try:
        new_features = []

        if name.endswith((".fa", ".fasta")):
            new_features = parse_fasta(uploaded)
            st.session_state["input_type"] = "fasta"

        elif name.endswith((".gb", ".gbk", ".genbank")):
            new_features = parse_genbank(uploaded)
            st.session_state["input_type"] = "genbank"

        elif name.endswith((".xml", ".sbml")):
            sbml = parse_sbml(uploaded)
            st.session_state["model"] = sbml["cobra_model"]
            st.session_state["input_type"] = "sbml"

            for i, g in enumerate(sbml["genes"]):
                new_features.append({
                    "id": g["id"],
                    "name": g.get("name"),
                    "product": g.get("product"),
                    "start": i * 200,
                    "end": i * 200 + 100,
                    "length": 100,
                    "source": "sbml"
                })

        else:
            st.error("Unsupported file type")

        st.session_state["feature_list"] = new_features

    except Exception as e:
        st.error(f"Parsing failed: {e}")


feature_list = st.session_state["feature_list"]


# =========================================================
# VISUALIZATION — CLASSIC BARCODE
# =========================================================
if feature_list:

    blocks = features_to_blocks(feature_list)

    if not blocks:
        st.error("No blocks generated.")
    else:

        for b in blocks:
            if color_layer == "structural":
                b["active_color"] = STRUCTURAL_COLORS.get(
                    b["class"], "#999999"
                )
            else:
                b["active_color"] = FUNCTION_COLORS.get(
                    b["function"], "#999999"
                )

        st.subheader("Visualization")

        fig = blocks_to_figure(blocks)

        if fig:
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Figure failed to render.")


# =========================================================
# EXPORT
# =========================================================
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


if st.session_state["do_export"]:

    pdf = None
    itype = st.session_state["input_type"]

    if itype == "sbml" and st.session_state["model"]:
        pdf = export_gene_reaction_pdf(st.session_state["model"])

    elif itype == "fasta":
        pdf = export_fasta_summary_pdf(feature_list)

    else:
        st.error("Export not available for this file type")

    if pdf:
        st.download_button(
            "Download PDF",
            data=pdf,
            file_name=f"{export_name}.pdf",
            mime="application/pdf"
        )

    st.session_state["do_export"] = False
