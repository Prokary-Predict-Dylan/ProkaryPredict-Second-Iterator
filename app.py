# app.py
import streamlit as st
import json
from parsers import parse_fasta, parse_genbank, parse_sbml
from blocks import features_to_blocks
from viz import blocks_to_figure
from export_pdf import export_gene_reaction_pdf
import io
import base64
import time

st.set_page_config(page_title="ProkaryPredict First Iterator", layout="wide")
st.title("ProkaryPredict — (First Iterator)")

# Ensure export_request exists
if "export_request" not in st.session_state:
    st.session_state["export_request"] = None

# -----------------------------------------------------------
# Sidebar
# -----------------------------------------------------------
with st.sidebar:
    st.header("Upload files")
    uploaded = st.file_uploader(
        "Upload GenBank (.gb/.gbk) / FASTA / SBML (.xml/.sbml)",
        accept_multiple_files=False
    )
    st.markdown("---")
    st.header("Export")
    export_name = st.text_input("PDF filename (without ext)", value="prokarypredict_report")

    if st.button("Export PDF"):
        st.session_state["export_request"] = time.time()

st.info("Upload a GenBank, FASTA, or SBML file. Parsed features will be converted to blocks and displayed.")

# -----------------------------------------------------------
# File Handling
# -----------------------------------------------------------
if uploaded is not None:
    fn = uploaded.name.lower()
    content = uploaded.read()
    feature_list = []

    try:
        # decode a small portion safely for detection
        try:
            preview_text = content[:5000].decode("utf-8", errors="ignore").lower()
        except Exception:
            preview_text = ""

        # ------------------------------
        # GenBank
        # ------------------------------
        if fn.endswith((".gb", ".gbk", ".genbank")):
            feature_list = parse_genbank(io.BytesIO(content))
            st.success(f"Parsed GenBank: {len(feature_list)} features found")

        # ------------------------------
        # FASTA
        # ------------------------------
        elif fn.endswith((".fa", ".fasta")):
            feature_list = parse_fasta(io.BytesIO(content))
            st.success(f"Parsed FASTA: {len(feature_list)} sequences")

        # ------------------------------
        # SBML
        # ------------------------------
        elif fn.endswith((".xml", ".sbml")) or "<sbml" in preview_text:
            sbml_res = parse_sbml(io.BytesIO(content))
            st.session_state['model'] = sbml_res["cobra_model"]

            for idx, g in enumerate(sbml_res["genes"]):
                feature_list.append({
                    "id": g["id"],
                    "name": g.get("name") or g.get("id"),
                    "product": g.get("product", ""),
                    "auto_categories": sbml_res.get("auto_categories", {}),
                    "start": idx * 200,
                    "end": idx * 200 + 100,
                    "length": 100,
                    "source": "sbml",
                    "reactions": g.get("reactions", [])
                })
            st.success(f"Parsed SBML: {len(feature_list)} genes (mapped to blocks)")

        # ------------------------------
        # Unknown file → heuristics
        # ------------------------------
        else:
            st.warning("Unknown extension; attempting heuristics...")
            try:
                feature_list = parse_genbank(io.BytesIO(content))
                st.success(f"Parsed GenBank heuristically: {len(feature_list)} features found")
            except Exception:
                try:
                    feature_list = parse_fasta(io.BytesIO(content))
                    st.success(f"Parsed FASTA heuristically: {len(feature_list)} sequences")
                except Exception:
                    st.error("Could not parse file. Upload a valid GenBank, FASTA, or SBML file.")
                    feature_list = []

    except Exception as e:
        st.error(f"Parsing error: {e}")
        feature_list = []

    # -----------------------------------------------------------
    # Block Conversion
    # -----------------------------------------------------------
    blocks = features_to_blocks(feature_list)

    # -----------------------------------------------------------
    # Category Filter
    # -----------------------------------------------------------
    categories = sorted(set(b["category"] for b in blocks))
    sel_cats = st.sidebar.multiselect(
        "Show categories", options=categories, default=categories
    )
    filtered_blocks = [b for b in blocks if b["category"] in sel_cats]

    # -----------------------------------------------------------
    # Visualization
    # -----------------------------------------------------------
    st.subheader("Block visualization")
    fig = blocks_to_figure(filtered_blocks)
    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------
    # JSON Export
    # -----------------------------------------------------------
    with st.expander("Block data (JSON)"):
        st.json(filtered_blocks)

    # -----------------------------------------------------------
    # Blockly Workspace — Genome Assembly
    # -----------------------------------------------------------
    st.subheader("Block workspace (genome assembly)")

    blockly_xml_blocks = ""
    for i, gene in enumerate(filtered_blocks):
        color = gene.get("color", "#cccccc")
        block_id = f"gene_{i}"

        x_pos = 20 + i * 120  # Horizontal layout spacing

        # Emit each block separately (no nested <next>)
        block_xml = (
            f'<block type="gene_block" id="{block_id}" x="{x_pos}" y="20">'
            f'<field name="GENE">{gene["label"]}</field>'
            f'<field name="COLOR">{color}</field>'
            '</block>'
        )

        blockly_xml_blocks += block_xml

    # Use f-string to interpolate blockly_xml_blocks correctly
    blockly_html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <script src="https://unpkg.com/blockly/blockly.min.js"></script>
        <style>
            html, body {{ height: 100%; margin: 0; }}
            #blocklyDiv {{ height: 520px; width: 100%; }}
        </style>
      </head>
      <body>
        <div id="blocklyDiv"></div>
        <xml id="toolbox" style="display:none">
          <category name="Genome">
            <block type="gene_block"></block>
          </category>
        </xml>
        <script>
          Blockly.Blocks['gene_block'] = {{
            init: function() {{
              var geneName = this.getFieldValue('GENE') || 'Gene';
              var geneColor = this.getFieldValue('COLOR') || '#cccccc';
              this.appendDummyInput()
                  .appendField(new Blockly.FieldTextInput(geneName), "GENE")
                  .appendField(new Blockly.FieldTextInput(geneColor), "COLOR");
              this.setPreviousStatement(true, null);
              this.setNextStatement(true, null);
              this.setColour(this.getFieldValue('COLOR') || '#cccccc');
            }}
          }};
          var workspace = Blockly.inject('blocklyDiv', {{
              toolbox: document.getElementById('toolbox')
          }});
          var xmlText = `<xml>{blockly_xml_blocks}</xml>`;
          var xml = Blockly.Xml.textToDom(xmlText);
          Blockly.Xml.domToWorkspace(xml, workspace);
        </script>
      </body>
    </html>
    """
    st.components.v1.html(blockly_html, height=550, scrolling=True)

    # -----------------------------------------------------------
    # Download JSON Button
    # -----------------------------------------------------------
    if st.button("Download blocks JSON"):
        j = json.dumps(filtered_blocks, indent=2)
        b64 = base64.b64encode(j.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="{uploaded.name}_blocks.json">Download blocks JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

# -----------------------------------------------------------
# PDF Export — Gene → Reaction mapping
# -----------------------------------------------------------
if st.session_state.get("export_request") and 'model' in st.session_state:
    model = st.session_state['model']
    try:
        pdf_bytes = export_gene_reaction_pdf(
            model,
            metadata={"source_file": uploaded.name if uploaded is not None else "unknown",
                      "exported_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        )

        b64 = base64.b64encode(pdf_bytes).decode()
        fname = f"{export_name}.pdf"

        href = (
            f'<a href="data:application/pdf;base64,{b64}" '
            f'download="{fname}">Download PDF report</a>'
        )
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF export failed: {e}")

    # Reset request flag so subsequent clicks are new
    st.session_state["export_request"] = None