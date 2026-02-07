"""Composants graphiques."""

import plotly.graph_objects as go

from styles import Colors, GaugeConfig, Layout


def get_probability_color(probability: float) -> str:
    """Retourne la couleur en fonction de la probabilité."""
    if probability < 0.333:
        return Colors.SUCCESS
    elif probability < 0.666:
        return Colors.WARNING
    return Colors.DANGER


def create_gauge(probability: float, label: str) -> go.Figure:
    """Crée un indicateur gauge avec fond tricolore et pointeur."""
    color = get_probability_color(probability)
    value = probability * 100

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "font": {"size": 48, "color": color}},
            title={"text": label, "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": Colors.GRAY_200},
                "bar": {"color": "rgba(0,0,0,0)", "thickness": 0},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 33.3], "color": Colors.SUCCESS},
                    {"range": [33.3, 66.6], "color": Colors.WARNING},
                    {"range": [66.6, 100], "color": Colors.DANGER},
                ],
                "threshold": {
                    "line": {"color": "#1e293b", "width": 4},
                    "thickness": 0.85,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(
        margin=Layout.GAUGE_MARGIN,
        height=GaugeConfig.HEIGHT,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig
