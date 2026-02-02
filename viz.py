# viz.py
import plotly.graph_objects as go

def blocks_to_figure(blocks):
    fig = go.Figure()

    for b in blocks:
        fig.add_trace(
            go.Scatter(
                x=[b["start"], b["end"]],
                y=[0, 0],
                mode="lines",
                line=dict(
                    color=b["active_color"],
                    width=10
                ),
                hoverinfo="text",
                text=(
                    f"<b>{b['label']}</b><br>"
                    f"Structural: {b['class']}<br>"
                    f"Function: {b['function']}<br>"
                    f"Length: {b['length']} bp"
                ),
                showlegend=False
            )
        )

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="Genome position"),
        yaxis=dict(visible=False),
        plot_bgcolor="white"
    )

    return fig
