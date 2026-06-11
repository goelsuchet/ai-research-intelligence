import plotly.graph_objects as go

def render_visual(spec):
    """
    Takes a deterministic spec dictionary from the quant engine and returns a Plotly Figure.
    """
    v_type = spec.get("type", "bar")
    title = spec.get("title", "")
    x = spec.get("x", [])
    y = spec.get("y", [])
    x_label = spec.get("x_label", "")
    y_label = spec.get("y_label", "")
    
    fig = go.Figure()
    
    if v_type == "bar":
        fig.add_trace(go.Bar(x=x, y=y, marker_color='#636EFA'))
    elif v_type == "hist":
        fig.add_trace(go.Bar(x=x, y=y, marker_color='#EF553B'))
    elif v_type == "line":
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#00CC96', width=3)))
    elif v_type == "funnel":
        fig.add_trace(go.Funnel(y=y, x=x, marker=dict(color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"])))
    elif v_type == "scatter":
        text = spec.get("text", [])
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='markers+text', 
            text=text, textposition="top center",
            marker=dict(size=12, color='#AB63FA', line=dict(width=2, color='DarkSlateGrey'))
        ))
        
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="closest"
    )
    
    return fig
