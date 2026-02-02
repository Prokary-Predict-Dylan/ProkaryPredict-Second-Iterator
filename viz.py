# viz.py
import plotly.graph_objects as go

def barcode_view(blocks):
    fig = go.Figure()
    for b in blocks:
        fig.add_trace(go.Scatter(
            x=[b["start"], b["end"]],
            y=[0, 0],
            mode="lines",
            line=dict(color=b["active_color"], width=8),
            hoverinfo="text",
            text=f"{b['label']}<br>{b['class']}<br>{b['function']}",
            showlegend=False
        ))
    fig.update_layout(height=180, yaxis_visible=False)
    return fig

def stacked_view(blocks):
    fig = go.Figure()
    for b in blocks:
        fig.add_bar(
            x=[b["length"]],
            y=[1],
            base=[b["start"]],
            orientation="h",
            marker=dict(color=b["active_color"]),
            hoverinfo="text",
            text=b["label"],
            showlegend=False
        )
    fig.update_layout(barmode="stack", height=350, yaxis_visible=False)
    return fig

def blocks_to_figure(blocks, mode="barcode"):
    return barcode_view(blocks) if mode == "barcode" else stacked_view(blocks)
