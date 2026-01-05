#blocks.py
import re

DEFAULT_COLORS = {
    "core_metabolism": "#2c3e91", "energy_systems": "#c1d6be",
    "biosynthesis": "#267331", "transport": "#b34237",
    "other_functions": "#524d5c", "unassigned": "#cccccc",
    "non_coding": "#ffffff", "regulation": "#9a6bd1"
}

EC_CATEGORY_MAP = {"1":"core_metabolism","2":"biosynthesis","3":"core_metabolism",
                   "4":"core_metabolism","5":"core_metabolism","6":"biosynthesis","7":"transport"}
EC_REGEX = re.compile(r"(\d+\.\d+\.\d+\.\d+)")

def extract_ec_numbers(f):
    ecs = set()
    q = f.get("qualifiers", {})
    if "EC_number" in q:
        ecs.update(q["EC_number"])
    if "ec_number" in f:
        ecs.add(f["ec_number"])
    matches = EC_REGEX.findall(f.get("product","") or "")
    ecs.update(matches)
    return list(ecs)

def categorize_feature(f):
    if f.get("type") in ("tRNA","rRNA","ncRNA"):
        return "non_coding"
    for ec in extract_ec_numbers(f):
        cls = ec.split(".")[0]
        if cls in EC_CATEGORY_MAP:
            return EC_CATEGORY_MAP[cls]
    subsys = (f.get("subsystem") or "").lower()
    if "transport" in subsys: return "transport"
    if "biosynth" in subsys: return "biosynthesis"
    if "cycle" in subsys or "metabolism" in subsys: return "core_metabolism"
    if "regulation" in subsys: return "regulation"
    text = (f.get("product","") + " " + (f.get("name") or "")).lower()
    if any(k in text for k in ["transporter","channel","pump"]): return "transport"
    if any(k in text for k in ["synthase","synthetase","ligase","synth"]): return "biosynthesis"
    if any(k in text for k in ["dehydrogenase","isomerase","kinase","oxidase"]): return "core_metabolism"
    if any(k in text for k in ["regulator","repressor","activator","sigma"]): return "regulation"
    return "other_functions"

def assign_color(category):
    return DEFAULT_COLORS.get(category, DEFAULT_COLORS["unassigned"])

def features_to_blocks(features):
    blocks=[]
    have_coords = all("start" in f and "end" in f for f in features)
    if have_coords:
        for f in features:
            cat=categorize_feature(f)
            length=f.get("length") or (f.get("end",0)-f.get("start",0))
            blocks.append({"id":f.get("id"),"label":f.get("name") or f.get("id"),
                           "category":cat,"start":f.get("start"),"end":f.get("end"),
                           "length":length,"color":assign_color(cat),"shape":"rect",
                           "metadata":f})
    else:
        pos=0
        for f in features:
            length=f.get("length",100)
            cat=categorize_feature(f)
            blocks.append({"id":f.get("id"),"label":f.get("name") or f.get("id"),
                           "category":cat,"start":pos,"end":pos+length,
                           "length":length,"color":assign_color(cat),"shape":"rect",
                           "metadata":f})
            pos+=length+int(length*0.1)
    return blocks
