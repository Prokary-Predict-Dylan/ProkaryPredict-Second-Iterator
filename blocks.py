# blocks.py
from typing import List, Dict

# ---------------------------
# Structural colors
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

STOP_CODONS = {"TAA", "TAG", "TGA"}

def is_protein_coding(seq: str) -> bool:
    if not seq or len(seq) < 90 or len(seq) % 3 != 0:
        return False
    return not any(seq[i:i+3].upper() in STOP_CODONS for i in range(0, len(seq)-3, 3))

def classify_structural(f: Dict) -> str:
    if f.get("structural_override"):
        return f["structural_override"]
    if f.get("type", "").lower() in ("trna", "rrna", "ncrna"):
        return "non_coding"
    if f.get("source") == "fasta":
        return "protein_coding" if is_protein_coding(f.get("sequence", "")) else "non_coding"
    if f.get("length", 0) < 90:
        return "fragment"
    return "protein_coding"

def infer_function_keywords(f: Dict) -> str:
    text = f"{f.get('name','')} {f.get('product','')}".lower()
    for func, keys in FUNCTION_KEYWORDS.items():
        if any(k in text for k in keys):
            return func
    return "unknown"

def features_to_blocks(features: List[Dict]) -> List[Dict]:
    blocks = []
    cursor = 0

    for f in features:
        structural = classify_structural(f)
        function = f.get("function_override") or infer_function_keywords(f)
        start = f.get("start", cursor)
        length = f.get("length", 100)
        end = f.get("end", start + length)

        blocks.append({
            "id": f["id"],
            "label": f.get("label") or f.get("name") or f["id"],
            "class": structural,
            "function": function,
            "start": start,
            "end": end,
            "length": length,
            "active": f.get("active", True),
            "metadata": f
        })

        cursor = end + int(length * 0.1)

    return blocks
