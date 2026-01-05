# export_pdf.py
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def export_gene_reaction_pdf(model):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height-1*inch, "Gene → Reaction Report")

    y = height - 1.5*inch
    c.setFont("Helvetica", 9)

    for rxn in model.reactions:
        for g in rxn.genes:
            line = f"{g.id} → {rxn.id}: {rxn.name or ''}"
            c.drawString(1*inch, y, line[:110])
            y -= 12
            if y < inch:
                c.showPage()
                y = height - inch

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def export_fasta_summary_pdf(features):
    df = pd.DataFrame([
        {
            "ID": f["id"],
            "Length": f["length"],
            "Class": f.get("class", "unknown")
        }
        for f in features
    ])

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height-1*inch, "FASTA Gene Summary")

    y = height - 1.5*inch
    c.setFont("Helvetica", 10)

    for _, row in df.iterrows():
        c.drawString(1*inch, y, f"{row['ID']} | {row['Length']} bp | {row['Class']}")
        y -= 12
        if y < inch:
            c.showPage()
            y = height - inch

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
