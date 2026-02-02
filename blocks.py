import re

# ---------------------------
# Structural layer
# ---------------------------
STRUCTURAL_COLORS = {
    "protein_coding": "#4c72b0",
    "non_coding": "#999999",
    "fragment": "#bbbbbb",
    "unknown": "#dddddd"
}

# ---------------------------
# FUNCTION KEYWORDS - Full Library
# ---------------------------
FUNCTION_KEYWORDS = {
    "enzyme": [
        "ase", "dehydrogenase", "kinase", "synthase", "synthetase", "transferase",
        "ligase", "isomerase", "oxidase", "reductase", "phosphatase", "hydrolase",
        "lyase", "epimerase", "mutase", "carboxylase", "protease", "peptidase",
        "polymerase", "nuclease", "lipase", "glycosylase", "cyclase", "formyltransferase",
        "acetyltransferase", "methyltransferase"
    ],
    "transporter": [
        "transporter", "pump", "channel", "abc", "symporter", "antiport",
        "efflux", "importer", "exporter", "permease", "porin", "ion channel",
        "glucose transporter", "amino acid transporter", "metal transporter",
        "nitrate transporter", "phosphate transporter"
    ],
    "regulator": [
        "regulator", "repressor", "activator", "sigma", "tf", "transcription factor",
        "sensor", "two-component", "response regulator", "modulator",
        "activator protein", "inhibitor", "co-activator", "co-repressor",
        "riboswitch", "antisense RNA", "small RNA", "operon regulator"
    ],
    "structural": [
        "ribosomal", "cytoskeleton", "flagellin", "pilin", "chaperone", "heat shock",
        "filament", "microtubule", "actin", "tubulin", "scaffold", "membrane protein",
        "extracellular matrix", "envelope protein", "capsid", "coat protein"
    ],
    "energy": [
        "photosystem", "psa", "psb", "ndh", "cytochrome", "oxidase",
        "electron transport", "respiratory", "atp synthase", "ferrodoxin",
        "photoreaction", "hydrogenase", "rubisco", "nitrogenase"
    ],
    "biosynthesis": [
        "ribose", "fatty acid", "amino acid", "nucleotide", "mur", "peptidoglycan",
        "polyketide", "isoprenoid", "sterol", "sugar synthase", "cofactor",
        "vitamin", "heme", "chlorophyll", "carotenoid"
    ],
    "unknown": [
        "hypothetical", "putative", "uncharacterized", "unknown", "predicted"
    ]
}

# ---------------------------
# Protein coding check
# ---------------------------
STOP_CODONS = {"TAA", "TAG", "TGA"}

def is_protein_coding(seq: str) -> bool:
    """Check if sequence is likely a protein-coding gene."""
    if not seq or len(seq) < 90:
        return False
    if len(seq) % 3 != 0:
        return False
    for i in range(0, len(seq)-3, 3):
        if seq[i:i+3].upper() in STOP_CODONS:
            return False
    return True

# ---------------------------
# Structural classification
# ---------------------------
def classify_structural(f: dict) -> str:
    """Determine structural class of feature."""
    if f.get("structural_override"):
        return f["structural_override"]
    ftype = f.get("type", "").lower()
    if ftype in ("trna", "rrna", "ncrna"):
        return "non_coding"
    if f.get("source") == "fasta":
        seq = f.get("sequence", "")
        if len(seq) < 90:
            return "fragment"
        return "protein_coding" if is_protein_coding(seq) else "non_coding"
    if f.get("length", 0) < 90:
        return "fragment"
    return "protein_coding"

# ---------------------------
# Functional inference
# ---------------------------
def infer_function(f: dict) -> str:
    """Infer functional class from name/product using FUNCTION_KEYWORDS."""
    if f.get("function_override"):
        return f["function_override"]
    text = ((f.get("product") or "") + " " + (f.get("name") or "")).lower()
    for func, keys in FUNCTION_KEYWORDS.items():
        if any(k in text for k in keys):
            return func
    return "unknown"

# ---------------------------
# Convert features to visualization blocks
# ---------------------------
def features_to_blocks(features: list) -> list:
    """Convert feature list into block objects for visualization."""
    blocks = []
    pos = 0
    for f in features:
        structural = classify_structural(f)
        function = infer_function(f)
        start = f.get("start", pos)
        length = f.get("length", 100)
        end = f.get("end", start + length)
        blocks.append({
            "id": f.get("id"),
            "label": f.get("name") or f.get("id"),
            "class": structural,
            "function": function,
            "start": start,
            "end": end,
            "length": length,
            "active": f.get("active", True),
            "color": STRUCTURAL_COLORS.get(structural, "#dddddd"),
            "metadata": f
        })
        pos = end + int(length * 0.1)
    return blocks
