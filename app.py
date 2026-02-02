import streamlit as st
import os
import json

from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import features_to_blocks, STRUCTURAL_COLORS, FUNCTION_KEYWORDS
from viz import blocks_to_figure
from export_pdf import export_gene_reaction_pdf, export_fasta_summary_pdf


# =========================================================
# FUNCTION COLORS (deterministic, safe)
# =========================================================
def _func_color(name):
    return "#" + "".join(f"{(hash(name + str(i)) & 0xFF):02x}" for i in range(3))

FUNCTION_COLORS = {k: _func_color(k) for k in FUNCTION_KEYWORDS.keys()}
FUNCTION_COLORS["unknown"] = "#262d48"


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ProkaryPredict — Second Iterator",
    layout="wide"
)
st.title("ProkaryPredict — Second Iterator")


# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "feature_list": [],
    "input_type": None,
    "model": None,
    "confirm_export": False,
    "do_export": False,
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Templates")
    templates = ["None"]
    if os.path.exists("templates"):
        templates += sorted(os.listdir("templates"))
    template_choice = st.selectbox("Load template", templates)

    st.markdown("---")
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
feature_list = []

if uploaded:
    name = uploaded.name.lower()
    try:
        if name.endswith((".fa", ".fasta")):
            feature_list = parse_fasta(uploaded)
            st.session_state["input_type"] = "fasta"

        elif name.endswith((".gb", ".gbk", ".genbank")):
            feature_list = parse_genbank(uploaded)
            st.session_state["input_type"] = "genbank"

        elif name.endswith((".xml", ".sbml")):
            sbml = parse_sbml(uploaded)
            st.session_state["model"] = sbml["cobra_model"]
            st.session_state["input_type"] = "sbml"

            for i, g in enumerate(sbml["genes"]):
                feature_list.append({
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

    except Exception as e:
        st.error(f"Parsing failed: {e}")

st.session_state["feature_list"] = feature_list


# =========================================================
# TEMPLATE METADATA
# =========================================================
if template_choice != "None":
    meta_path = f"templates/{template_choice}/metadata.json"
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        st.info(f"Template loaded: {meta.get('species', template_choice)}")


# =========================================================
# FEATURE EDITOR
# =========================================================
if feature_list:
    st.subheader("Edit features")

    for i, f in enumerate(feature_list):
        c1, c2, c3 = st.columns([3, 3, 2])

        with c1:
            f["label"] = st.text_input(
                f"Label {f['id']}",
                f.get("label", f.get("name", f["id"])),
                key=f"label_{i}"
            )

        with c2:
            current = f.get("function_override") or "unknown"
            f["function_override"] = st.selectbox(
                "Function",
                list(FUNCTION_COLORS.keys()),
                index=list(FUNCTION_COLORS.keys()).index(current),
                key=f"func_{i}"
            )

        with c3:
            f["active"] = st.checkbox(
                "Active",
                f.get("active", True),
                key=f"active_{i}"
            )


# =========================================================
# VISUALIZATION — CLASSIC BARCODE
# =========================================================
if feature_list:
    blocks = features_to_blocks(feature_list)

    for b in blocks:
        b["active_color"] = (
            STRUCTURAL_COLORS[b["class"]]
            if color_layer == "structural"
            else FUNCTION_COLORS[b["function"]]
        )
        if not b["active"]:
            b["active_color"] = "#dddddd"

    st.subheader("Genome barcode")
    fig = blocks_to_figure(blocks)
    st.plotly_chart(fig, use_container_width=True)


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
