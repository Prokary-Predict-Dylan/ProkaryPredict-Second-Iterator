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
                    color=b.get("active_color", "#cccccc"),
                    width=8
                ),
                hoverinfo="text",
                text=(
                    f"<b>{b['label']}</b><br>"
                    f"Function: {b['function']}<br>"
                    f"Class: {b['class']}<br>"
                    f"Length: {b['length']}"
                ),
                showlegend=False
            )
        )

    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(
            title="Genomic position",
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            visible=False
        ),
        plot_bgcolor="white"
    )

    return fig
