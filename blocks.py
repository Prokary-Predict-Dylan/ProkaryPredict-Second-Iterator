#blocks.py
import re

# =========================================================
# COLOR SYSTEMS (one per layer — NEVER reused)
# =========================================================

STRUCTURAL_COLORS = {
    "protein_coding": "#4C72B0",
    "non_coding": "#DD8452",
    "fragment": "#A9A9A9",
    "unknown": "#CCCCCC"
}

FUNCTION_COLORS = {
    "enzyme": "#55A868",
    "transporter": "#C44E52",
    "regulator": "#8172B3",
    "unknown": "#BBBBBB"
}

EVIDENCE_COLORS = {
    "sequence_only": "#937860",
    "annotated": "#64B5CD",
    "model_linked": "#4DB6AC",
    "experimental": "#2ECC71"
}

MODEL_CONTEXT_COLORS = {
    "energy_systems": "#F39C12",
    "core_metabolism": "#27AE60",
    "biosynthesis": "#2980B9",
    "transport": "#8E44AD",
    "regulation": "#C0392B",
    "none": "#E0E0E0"
}

STOP_CODONS = {"TAA", "TAG", "TGA"}

FUNCTION_KEYWORDS = {
    "enzyme": ["ase", "kinase", "dehydrogenase", "synthase"],
    "transporter": ["transporter", "pump", "channel", "abc"],
    "regulator": ["regulator", "repressor", "activator", "sigma"]
}

# =========================================================
# SEQUENCE LOGIC
# =========================================================

def is_protein_coding(seq):
    if not seq or len(seq) < 90:
        return False
    if len(seq) % 3 != 0:
        return False
    for i in range(0, len(seq) - 3, 3):
        if seq[i:i+3].upper() in STOP_CODONS:
            return False
    return True

# =========================================================
# CLASSIFICATION LAYERS
# =========================================================

def classify_structural(f):
    if f.get("type") in ("tRNA", "rRNA", "ncRNA"):
        return "non_coding"

    if f.get("source") == "fasta":
        seq = f.get("sequence", "")
        if len(seq) < 90:
            return "fragment"
        return "protein_coding" if is_protein_coding(seq) else "non_coding"

    if f.get("length", 0) < 90:
        return "fragment"

    return "protein_coding"

def infer_function_hint(f):
    text = ((f.get("product") or "") + " " + (f.get("name") or "")).lower()
    for func, keys in FUNCTION_KEYWORDS.items():
        if any(k in text for k in keys):
            return func
    return "unknown"

def determine_evidence(f):
    return {
        "fasta": "sequence_only",
        "genbank": "annotated",
        "sbml": "model_linked"
    }.get(f.get("source"), "unknown")

def extract_model_context(f):
    if f.get("source") != "sbml":
        return "none"

    text = (f.get("product") or "").lower()
    if any(k in text for k in ["photosystem", "psa", "psb", "atp"]):
        return "energy_systems"
    if any(k in text for k in ["glycolysis", "tca", "gap", "pyk"]):
        return "core_metabolism"
    if any(k in text for k in ["synthase", "synthetase", "amino", "fatty"]):
        return "biosynthesis"
    if any(k in text for k in ["transporter", "abc", "import", "export"]):
        return "transport"
    if any(k in text for k in ["regulator", "sigma", "tf"]):
        return "regulation"

    return "none"

def data_flags(f):
    return {
        "has_sequence": "sequence" in f,
        "has_coordinates": f.get("start") is not None,
        "has_product": bool(f.get("product")),
        "has_reactions": bool(f.get("reactions"))
    }

# =========================================================
# BLOCK GENERATION
# =========================================================

def features_to_blocks(features):
    blocks = []
    pos = 0

    for f in features:
        length = f.get("length", 100)

        structural = classify_structural(f)
        function = infer_function_hint(f)
        evidence = determine_evidence(f)
        context = extract_model_context(f)
        flags = data_flags(f)

        start = f.get("start", pos)
        end = f.get("end", start + length)

        blocks.append({
            "id": f.get("id"),
            "label": f.get("name") or f.get("id"),

            "structural_class": structural,
            "function_hint": function,
            "evidence": evidence,
            "model_context": context,
            "data_flags": flags,

            "colors": {
                "structural": STRUCTURAL_COLORS[structural],
                "function": FUNCTION_COLORS[function],
                "evidence": EVIDENCE_COLORS[evidence],
                "context": MODEL_CONTEXT_COLORS[context]
            },

            "start": start,
            "end": end,
            "length": length,
            "metadata": f
        })

        pos = end + int(length * 0.1)

    return blocks