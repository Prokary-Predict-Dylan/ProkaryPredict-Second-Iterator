# blocks.py
import re

# ---------------------------
# Primary biological classes
# ---------------------------
CLASS_COLORS = {
    "protein_coding": "#4c72b0",
    "non_coding": "#cccccc",
    "fragment": "#999999",
    "unknown": "#dddddd"
}

# ---------------------------
# Secondary functional tags
# ---------------------------
FUNCTION_KEYWORDS = {
    "enzyme": ["ase", "dehydrogenase", "kinase", "synthase"],
    "transporter": ["transporter", "pump", "channel", "abc"],
    "regulator": ["regulator", "repressor", "activator", "sigma"]
}

STOP_CODONS = {"TAA", "TAG", "TGA"}

def is_protein_coding(seq):
    if not seq or len(seq) < 90:
        return False
    if len(seq) % 3 != 0:
        return False
    for i in range(0, len(seq) - 3, 3):
        if seq[i:i+3].upper() in STOP_CODONS:
            return False
    return True

def classify_feature(f):
    # -------- GenBank explicit RNA --------
    if f.get("type") in ("tRNA", "rRNA", "ncRNA"):
        return "non_coding"

    # -------- FASTA sequence inference --------
    if f.get("source") == "fasta":
        seq = f.get("sequence", "")
        if len(seq) < 90:
            return "fragment"
        if is_protein_coding(seq):
            return "protein_coding"
        return "non_coding"

    # -------- Default --------
    if f.get("length", 0) < 90:
        return "fragment"
    return "protein_coding"

def infer_function(f):
    text = ((f.get("product") or "") + " " + (f.get("name") or "")).lower()
    for func, keys in FUNCTION_KEYWORDS.items():
        if any(k in text for k in keys):
            return func
    return "unknown"

def features_to_blocks(features):
    blocks = []
    pos = 0

    for f in features:
        length = f.get("length", 100)
        cls = classify_feature(f)
        func = infer_function(f)
        color = CLASS_COLORS.get(cls, CLASS_COLORS["unknown"])

        start = f.get("start", pos)
        end = f.get("end", start + length)

        blocks.append({
            "id": f.get("id"),
            "label": f.get("name") or f.get("id"),
            "class": cls,
            "function": func,
            "start": start,
            "end": end,
            "length": length,
            "color": color,
            "metadata": f
        })

        pos = end + int(length * 0.1)

    return blocks
