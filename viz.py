import plotly.graph_objects as go

def blocks_to_figure(blocks, genome_length=None):
    if genome_length is None:
        genome_length = max((b["end"] for b in blocks), default=1)
    fig = go.Figure()
    for b in blocks:
        x0 = b.get("start",0)
        x1 = b.get("end",x0+b.get("length",1))
        fig.add_trace(go.Bar(
            x=[x1-x0], y=[1], base=[x0],
            orientation='h', marker=dict(color=b.get("color","#cccccc")),
            hoverinfo='text',
            text=f"{b.get('label')}<br>len:{b.get('length')}<br>cat:{b.get('category')}",
            name=b.get("label"), showlegend=False
        ))
    fig.update_layout(barmode='stack', title="Block visualization",
                      xaxis_title="Genomic coordinate", yaxis_visible=False,
                      height=350, margin=dict(l=10,r=10,t=30,b=20))
    fig.update_xaxes(range=[0, genome_length*1.02])
    return fig
