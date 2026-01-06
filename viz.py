#viz.py
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
            marker=dict(color=b["active_color"]),
            hoverinfo="text",
            text=(
                f"{b['label']}<br>"
                f"Structural: {b['structural_class']}<br>"
                f"Function: {b['function_hint']}<br>"
                f"Evidence: {b['evidence']}<br>"
                f"Context: {b['model_context']}"
            ),
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