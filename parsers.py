# parsers.py
from Bio import SeqIO
import io
import cobra
import re
from collections import defaultdict, Counter

# ---------------------------------------------------------
# FASTA PARSER
# ---------------------------------------------------------
def parse_fasta(handle):
    records = list(SeqIO.parse(handle, "fasta"))
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "name": getattr(r, "name", r.id),
            "description": r.description,
            "sequence": str(r.seq),
            "length": len(r.seq),
            "source": "fasta"
        })
    return results

# ---------------------------------------------------------
# GENBANK PARSER
# ---------------------------------------------------------
def parse_genbank(handle):
    records = list(SeqIO.parse(handle, "genbank"))
    results = []
    for r in records:
        for feat in r.features:
            if feat.type in ("gene", "CDS", "rRNA", "tRNA"):
                gene_name = None
                qualifiers = feat.qualifiers or {}
                if "gene" in qualifiers:
                    gene_name = qualifiers.get("gene")[0]
                elif "locus_tag" in qualifiers:
                    gene_name = qualifiers.get("locus_tag")[0]
                prod = qualifiers.get("product", [""])[0]
                seq_len = int(len(feat.location)) if feat.location is not None else 0
                results.append({
                    "id": qualifiers.get("locus_tag", [f"{r.id}_{len(results)}"])[0],
                    "name": gene_name or qualifiers.get("locus_tag", ["unknown"])[0],
                    "product": prod,
                    "start": int(feat.location.start) if feat.location is not None else None,
                    "end": int(feat.location.end) if feat.location is not None else None,
                    "length": seq_len,
                    "type": feat.type,
                    "source": "genbank",
                    "qualifiers": qualifiers
                })
    return results

# ---------------------------------------------------------
# AUTO-GENERATED CATEGORY SYSTEM FOR SBML
# ---------------------------------------------------------
def autogenerate_categories_from_model(model):
    """
    Analyze reaction names/IDs/subsystems to create a model-specific categorization map.
    Returns: {category: set(keywords)}
    """
    categories = {
        "energy_systems": set(),
        "core_metabolism": set(),
        "biosynthesis": set(),
        "transport": set(),
        "regulation": set(),
    }

    # collect reaction text
    reaction_texts = {}
    for r in model.reactions:
        text = " ".join([
            r.id or "",
            r.name or "",
            getattr(r, "subsystem", "") or ""
        ]).lower()
        reaction_texts[r.id] = text

    # base heuristic keywords
    heuristics = {
        "energy_systems": ["photosystem", "psa", "psb", "ndh", "cytochrome",
                           "oxidase", "electron", "respir", "atp", "ferro"],
        "core_metabolism": ["glycolysis", "g6p", "f6p", "ppp", "pentose", "tca",
                            "krebs", "gdh", "gap", "pyk", "pgi", "pgk", "fba",
                            "aldolase", "isomerase"],
        "biosynthesis": ["synthase", "synthetase", "ribose", "fatty", "amino",
                         "biosynth", "mur", "acc", "trp", "his", "pyr"],
        "transport": ["transporter", "export", "import", "abc", "symport",
                      "antiport", "ex_", "_t"],
        "regulation": ["regulator", "sensor", "two-component", "sigma", "tf"],
    }

    # apply heuristics
    for rid, text in reaction_texts.items():
        for category, keys in heuristics.items():
            for k in keys:
                if k in text:
                    categories[category].add(k)

    # token frequency analysis
    token_counts = Counter()
    for _, text in reaction_texts.items():
        for token in re.findall(r"[a-zA-Z0-9_]+", text):
            token_counts[token] += 1

    # enrich categories dynamically
    for rid, text in reaction_texts.items():
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for category in list(categories.keys()):
            if any(k in text for k in categories[category]):
                for t in tokens:
                    if token_counts[t] > 5 and len(t) > 2:
                        categories[category].add(t)

    return categories

# ---------------------------------------------------------
# SBML PARSER WITH AUTO-CATEGORIZATION
# ---------------------------------------------------------
def parse_sbml(file_like):
    try:
        model = cobra.io.read_sbml_model(file_like)
    except Exception:
        file_like.seek(0)
        model = cobra.io.read_sbml_model(io.StringIO(file_like.read().decode("utf-8")))

    # generate model-specific categories
    auto_categories = autogenerate_categories_from_model(model)

    genes = []
    for g in model.genes:
        reaction_text = []
        for r in g.reactions:
            if r.name:
                reaction_text.append(r.name)
            else:
                reaction_text.append(r.id)
            if hasattr(r, "subsystem") and r.subsystem:
                reaction_text.append(r.subsystem)

        combined_text = "; ".join(reaction_text).lower()

        genes.append({
            "id": g.id,
            "name": g.name or g.id,
            "product": combined_text,
            "auto_categories": auto_categories,
            "reactions": [r.id for r in g.reactions],
            "source": "sbml"
        })

    reactions = [{
        "id": r.id,
        "name": r.name or r.id,
        "bounds": (r.lower_bound, r.upper_bound),
        "genes": [g.id for g in r.genes],
        "source": "sbml"
    } for r in model.reactions]

    # Add COBRA model for PDF export
    return {"cobra_model": model, "genes": genes, "reactions": reactions, "auto_categories": auto_categories}