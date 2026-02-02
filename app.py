import streamlit as st
import os
import json
from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import features_to_blocks, STRUCTURAL_COLORS, FUNCTION_KEYWORDS
from viz import blocks_to_figure
from export_pdf import export_gene_reaction_pdf, export_fasta_summary_pdf

# ---------------------------
# Derived FUNCTION_COLORS
# ---------------------------
FUNCTION_COLORS = {
    func: "#" + "".join([f"{hash(func + str(i)) % 256:02x}" for i in range(3)])  # fix: str(i)
    for func in FUNCTION_KEYWORDS.keys()
}
FUNCTION_COLORS["unknown"] = "#262d48"

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="ProkaryPredict — Second Iterator", layout="wide")
st.title("ProkaryPredict — Second Iterator")

# ---------------------------
# Session state defaults
# ---------------------------
for k in ["confirm_export", "do_export", "input_type", "model", "feature_list"]:
    st.session_state.setdefault(k, None)

# ---------------------------
# Sidebar: Templates + Upload + Visualization + Export
# ---------------------------
with st.sidebar:
    st.header("Templates")
    templates = ["None"] + (os.listdir("templates") if os.path.exists("templates") else [])
    template_choice = st.selectbox("Load template", templates)
    
    st.header("Upload")
    uploaded = st.file_uploader("GenBank / FASTA / SBML", accept_multiple_files=False)
    
    st.markdown("---")
    st.header("Visualization")
    color_layer = st.radio("Color by", ["structural", "functional"], index=0)
    
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
        elif fn.endswith((".gb", ".gbk", ".genbank")):
            feature_list = parse_genbank(uploaded)
            st.session_state["input_type"] = "genbank"
        elif fn.endswith((".xml", ".sbml")):
            sbml_data = parse_sbml(uploaded)
            st.session_state["model"] = sbml_data["cobra_model"]
            st.session_state["input_type"] = "sbml"
            # convert genes to feature_list
            for i, g in enumerate(sbml_data["genes"]):
                feature_list.append({
                    "id": g["id"],
                    "name": g["name"],
                    "product": g["product"],
                    "start": i*200,
                    "end": i*200+100,
                    "length": 100,
                    "source": "sbml"
                })
        else:
            st.error("Unsupported file type")
    except Exception as e:
        st.error(f"Parsing failed: {e}")

st.session_state["feature_list"] = feature_list

# ---------------------------
# Template integration
# ---------------------------
if template_choice != "None":
    template_path = f"templates/{template_choice}/metadata.json"
    if os.path.exists(template_path):
        with open(template_path) as f:
            template_meta = json.load(f)
        st.info(f"Template loaded: {template_meta.get('species', template_choice)}")

# ---------------------------
# Editing UI
# ---------------------------
if feature_list:
    st.subheader("Edit features")
    for i, f in enumerate(feature_list):
        col1, col2, col3 = st.columns([3,3,2])
        with col1:
            f["label"] = st.text_input(f"Label {f['id']}", f.get("label", f.get("name", f['id'])), key=f"label_{i}")
        with col2:
            current_func = f.get("function_override") or "unknown"
            f["function_override"] = st.selectbox(
                "Function",
                list(FUNCTION_COLORS.keys()),
                index=list(FUNCTION_COLORS.keys()).index(current_func),
                key=f"func_{i}"
            )
        with col3:
            f["active"] = st.checkbox("Active", f.get("active", True), key=f"active_{i}")

# ---------------------------
# Visualization
# ---------------------------
if feature_list:
    blocks = features_to_blocks(feature_list)
    for b in blocks:
        b["active_color"] = STRUCTURAL_COLORS[b["class"]] if color_layer=="structural" else FUNCTION_COLORS[b["function"]]
        if not b["active"]:
            b["active_color"] = "#dddddd"  # gray out inactive
    st.subheader("Block visualization")
    fig = blocks_to_figure(blocks)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Export PDF
# ---------------------------
if st.session_state.get("confirm_export"):
    st.warning("Are you sure you want to export?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, export"):
            st.session_state["do_export"] = True
            st.session_state["confirm_export"] = False
    with c2:
        if st.button("Cancel"):
            st.session_state["confirm_export"] = False

if st.session_state.get("do_export"):
    itype = st.session_state.get("input_type")
    pdf = None
    if itype=="sbml" and st.session_state.get("model"):
        pdf = export_gene_reaction_pdf(st.session_state["model"])
    elif itype=="fasta":
        pdf = export_fasta_summary_pdf(feature_list)
    else:
        st.error("Export not available for this file type")
    if pdf:
        st.download_button("Download PDF", data=pdf, file_name=f"{export_name}.pdf", mime="application/pdf")
    st.session_state["do_export"] = False
