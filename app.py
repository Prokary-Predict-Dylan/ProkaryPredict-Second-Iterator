# app.py
import streamlit as st
from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import features_to_blocks
from viz import blocks_to_figure
from export_pdf import export_gene_reaction_pdf
import io, base64, time

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="ProkaryPredict Second Iterator", layout="wide")
st.title("ProkaryPredict — (Second Iterator)")

# Initialize export_request
if "export_request" not in st.session_state:
    st.session_state["export_request"] = None

# ---------------------------
# Sidebar: upload & export
# ---------------------------
with st.sidebar:
    st.header("Upload files")
    uploaded = st.file_uploader(
        "Upload GenBank (.gb/.gbk) / FASTA / SBML (.xml/.sbml)",
        accept_multiple_files=False
    )
    st.markdown("---")
    st.header("Export PDF")
    export_name = st.text_input("PDF filename (without ext)", value="prokarypredict_report")
    if st.button("Export PDF"):
        st.session_state["export_request"] = time.time()

st.info("Upload a GenBank, FASTA, or SBML file. Parsed features will be converted to blocks and displayed.")

# ---------------------------
# File handling: FASTA, GenBank, SBML
# ---------------------------
feature_list = []

if uploaded is not None:
    fn = uploaded.name.lower()
    try:
        # -----------------
        # FASTA
        # -----------------
        if fn.endswith((".fa", ".fasta")):
            feature_list = parse_fasta(uploaded)
            st.success(f"Parsed FASTA: {len(feature_list)} sequences")

        # -----------------
        # GenBank
        # -----------------
        elif fn.endswith((".gb", ".gbk", ".genbank")):
            feature_list = parse_genbank(uploaded)
            st.success(f"Parsed GenBank: {len(feature_list)} features found")

        # -----------------
        # SBML / XML
        # -----------------
        elif fn.endswith((".xml", ".sbml")):
            sbml_res = parse_sbml(uploaded)
            st.session_state["model"] = sbml_res["cobra_model"]

            # convert genes to features for block visualization
            for idx, g in enumerate(sbml_res["genes"]):
                feature_list.append({
                    "id": g["id"],
                    "name": g.get("name") or g["id"],
                    "product": g.get("product", ""),
                    "auto_categories": sbml_res.get("auto_categories", {}),
                    "start": idx * 200,
                    "end": idx * 200 + 100,
                    "length": 100,
                    "source": "sbml",
                    "reactions": g.get("reactions", [])
                })
            st.success(f"Parsed SBML: {len(feature_list)} genes")

        else:
            st.error("Unsupported file type. Upload FASTA, GenBank, or SBML.")

    except Exception as e:
        st.error(f"Parsing failed: {e}")

# ---------------------------
# Block conversion & visualization
# ---------------------------
if feature_list:
    blocks = features_to_blocks(feature_list)

    # Sidebar category filter
    categories = sorted(set(b["category"] for b in blocks))
    sel_cats = st.sidebar.multiselect("Show categories", options=categories, default=categories)
    filtered_blocks = [b for b in blocks if b["category"] in sel_cats]

    # Block visualization
    st.subheader("Block visualization")
    fig = blocks_to_figure(filtered_blocks)
    st.plotly_chart(fig, use_container_width=True)

    # JSON export
    with st.expander("Block data (JSON)"):
        st.json(filtered_blocks)

# ---------------------------
# PDF export
# ---------------------------
if st.session_state.get("export_request") and 'model' in st.session_state:
    model = st.session_state['model']
    try:
        pdf_bytes = export_gene_reaction_pdf(
            model,
            metadata={
                "source_file": uploaded.name if uploaded else "unknown",
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        b64 = base64.b64encode(pdf_bytes).decode()
        fname = f"{export_name}.pdf"
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{fname}">Download PDF report</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF export failed: {e}")

    st.session_state["export_request"] = None
