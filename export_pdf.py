import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import time

def export_gene_reaction_pdf(model, metadata=None):
    mapping=[]
    for rxn in model.reactions:
        if not rxn.genes:
            mapping.append({"Gene ID":"","Reaction ID":rxn.id,"Reaction Name":rxn.name or "",
                            "Reaction Equation":getattr(rxn,"reaction","")})
        else:
            for g in rxn.genes:
                mapping.append({"Gene ID":g.id,"Reaction ID":rxn.id,
                                "Reaction Name":rxn.name or "",
                                "Reaction Equation":getattr(rxn,"reaction","")})
    df=pd.DataFrame(mapping)
    buffer=io.BytesIO()
    c=canvas.Canvas(buffer,pagesize=letter)
    width,height=letter
    def new_page(title="ProkaryPredict Export"):
        c.showPage()
        c.setFont("Helvetica-Bold",16)
        c.drawString(1*inch,height-1*inch,title)
        c.setFont("Helvetica",10)
        return height-1.3*inch
    y=new_page("ProkaryPredict — Gene→Reaction Report")
    if metadata:
        for k,v in metadata.items():
            c.drawString(1*inch,y,f"{k}: {v}")
            y-=12
        y-=10
    if df.empty:
        c.drawString(1*inch,y,"No gene–reaction relationships found.")
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    col_widths=[1.5*inch,1.5*inch,2.5*inch,3*inch]
    row_height=14
    spacing=4
    x_pos=[1*inch]
    for w in col_widths[:-1]: x_pos.append(x_pos[-1]+w)
    c.setFont("Helvetica-Bold",10)
    for i,col in enumerate(df.columns):
        c.drawString(x_pos[i],y,col)
    y-=row_height+spacing
    c.setFont("Helvetica",9)
    for idx,row in df.iterrows():
        if y<1*inch:
            y=new_page("ProkaryPredict — Gene→Reaction Report (cont.)")
            c.setFont("Helvetica-Bold",10)
            for i,col in enumerate(df.columns):
                c.drawString(x_pos[i],y,col)
            y-=row_height+spacing
            c.setFont("Helvetica",9)
        for i,col in enumerate(df.columns):
            text=str(row[col])
            max_chars=max(10,int(col_widths[i]/5))
            if len(text)>max_chars:
                text=text[:max_chars-3]+"..."
            c.drawString(x_pos[i],y,text)
        y-=row_height+spacing
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
