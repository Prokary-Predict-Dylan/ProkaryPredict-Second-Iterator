# viz.py
import plotly.graph_objects as go

def blocks_to_figure(blocks):
    genome_length = max(b["end"] for b in blocks)
    fig = go.Figure()

    for b in blocks:
        fig.add_trace(go.Bar(
            x=[b["length"]],
            y=[1],
            base=[b["start"]],
            orientation="h",
            marker=dict(color=b["color"]),
            hoverinfo="text",
            text=f"{b['label']}<br>{b['class']}<br>{b['function']}",
            showlegend=False
        ))

    fig.update_layout(
        barmode="stack",
        height=350,
        xaxis_title="Coordinate",
        yaxis_visible=False
    )
    fig.update_xaxes(range=[0, genome_length * 1.02])
    return fig
