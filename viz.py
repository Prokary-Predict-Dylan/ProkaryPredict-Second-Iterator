import plotly.graph_objects as go


def blocks_to_figure(blocks, selected_id=None):

    fig = go.Figure()

    for b in blocks:

        color = b["active_color"]

        # Highlight selected gene
        line_width = 3 if b["id"] == selected_id else 0

        fig.add_trace(
            go.Bar(
                x=[b["end"] - b["start"]],
                y=["Genome"],
                base=[b["start"]],
                orientation="h",
                marker=dict(
                    color=color,
                    line=dict(color="black", width=line_width)
                ),
                hovertext=f"{b['label']} ({b['function']})",
                showlegend=False
            )
        )

        # Strand arrow
        arrow_x = b["end"] if b["strand"] == "+" else b["start"]

        fig.add_annotation(
            x=arrow_x,
            y=0,
            text="▶" if b["strand"] == "+" else "◀",
            showarrow=False,
            yshift=12
        )

    fig.update_layout(
        barmode="overlay",
        height=300,
        xaxis_title="Position (bp)",
        yaxis=dict(showticklabels=False),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig
