

#blocks.py
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
# Functional layer
# ---------------------------
FUNCTION_COLORS = {
    "enzyme": "#80bc8f",
    "transporter": "#aa5064",
    "regulator": "#8172b2",
    "structural": "#75a2c4",
    "unknown": "#262d48"
}

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

def is_protein_coding(seq):
    if not seq or len(seq) < 90:
        return False
    if len(seq) % 3 != 0:
        return False
    for i in range(0, len(seq) - 3, 3):
        if seq[i:i+3].upper() in STOP_CODONS:
            return False
    return True

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
        structural = classify_structural(f)
        function = infer_function(f)

        start = f.get("start", pos)
        end = f.get("end", start + length)

        blocks.append({
            "id": f.get("id"),
            "label": f.get("name") or f.get("id"),
            "class": structural,
            "function": function,
            "start": start,
            "end": end,
            "length": length,
            "color": STRUCTURAL_COLORS.get(structural),
            "metadata": f
        })

        pos = end + int(length * 0.1)

    return blocks


