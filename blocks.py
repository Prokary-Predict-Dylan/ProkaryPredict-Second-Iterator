import re

# =========================================================
# STRUCTURAL COLORS
# =========================================================
STRUCTURAL_COLORS = {
    "protein_coding": "#4c72b0",
    "non_coding": "#999999",
    "fragment": "#bbbbbb",
    "unknown": "#dddddd"
}

# =========================================================
# FUNCTION KEYWORDS - FULL LIBRARY
# =========================================================
FUNCTION_KEYWORDS = {
    "enzyme": [
        "ase", "dehydrogenase", "kinase", "synthase", "synthetase", "transferase",
        "ligase", "isomerase", "oxidase", "reductase", "phosphatase", "hydrolase",
        "lyase", "epimerase", "mutase", "carboxylase", "protease", "peptidase",
        "polymerase", "nuclease", "lipase", "glycosylase", "cyclase",
        "formyltransferase", "acetyltransferase", "methyltransferase"
    ],
    "transporter": [
        "transporter", "pump", "channel", "abc", "symporter", "antiport",
        "efflux", "importer", "exporter", "permease", "porin",
        "ion channel", "glucose transporter", "amino acid transporter",
        "metal transporter", "nitrate transporter", "phosphate transporter"
    ],
    "regulator": [
        "regulator", "repressor", "activator", "sigma", "tf",
        "transcription factor", "sensor", "two-component",
        "response regulator", "modulator", "activator protein",
        "inhibitor", "co-activator", "co-repressor",
        "riboswitch", "antisense rna", "small rna", "operon regulator"
    ],
    "structural": [
        "ribosomal", "cytoskeleton", "flagellin", "pilin",
        "chaperone", "heat shock", "filament", "microtubule",
        "actin", "tubulin", "scaffold", "membrane protein",
        "extracellular matrix", "envelope protein", "capsid",
        "coat protein"
    ],
    "energy": [
        "photosystem", "psa", "psb", "ndh", "cytochrome",
        "oxidase", "electron transport", "respiratory",
        "atp synthase", "ferrodoxin", "photoreaction",
        "hydrogenase", "rubisco", "nitrogenase"
    ],
    "biosynthesis": [
        "ribose", "fatty acid", "amino acid", "nucleotide",
        "mur", "peptidoglycan", "polyketide", "isoprenoid",
        "sterol", "sugar synthase", "cofactor",
        "vitamin", "heme", "chlorophyll", "carotenoid"
    ],
    "unknown": [
        "hypothetical", "putative", "uncharacterized",
        "unknown", "predicted"
    ]
}

# =========================================================
# FUNCTION COLORS (FIXED, CLEAN)
# =========================================================
FUNCTION_COLORS = {
    "enzyme": "#80bc8f",
    "transporter": "#aa5064",
    "regulator": "#8172b2",
    "structural": "#75a2c4",
    "energy": "#d4a017",
    "biosynthesis": "#4db6ac",
    "unknown": "#262d48"
}


# =========================================================
# Structural classification
# =========================================================
STOP_CODONS = {"TAA", "TAG", "TGA"}

def is_protein_coding(seq):
    if not seq or len(seq) < 90 or len(seq) % 3 != 0:
        return False
    for i in range(0, len(seq)-3, 3):
        if seq[i:i+3].upper() in STOP_CODONS:
            return False
    return True


def classify_structural(f):
    if f.get("type", "").lower() in ("trna", "rrna", "ncrna"):
        return "non_coding"

    if f.get("length", 0) < 90:
        return "fragment"

    return "protein_coding"


# =========================================================
# Functional classification
# =========================================================
def infer_function(f):
    text = f"{f.get('name','')} {f.get('product','')}".lower()

    for func, keywords in FUNCTION_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return func

    return "unknown"


# =========================================================
# Block conversion
# =========================================================
def features_to_blocks(features):
    blocks = []

    for f in features:
        structural = classify_structural(f)
        function = f.get("function_override") or infer_function(f)

        blocks.append({
            "id": f["id"],
            "label": f.get("label", f.get("name", f["id"])),
            "class": structural,
            "function": function,
            "start": f.get("start", 0),
            "end": f.get("end", f.get("start", 0) + f.get("length", 100)),
            "length": f.get("length", 100),
            "active": f.get("active", True)
        })

    return blocks
