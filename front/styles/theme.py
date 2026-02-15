"""Constantes de styles et thème centralisés."""


class Colors:
    """Palette de couleurs."""

    PRIMARY = "#3b82f6"
    PRIMARY_DARK = "#1d4ed8"
    SUCCESS = "#22c55e"
    SUCCESS_LIGHT = "#dcfce7"
    DANGER = "#ef4444"
    DANGER_LIGHT = "#fee2e2"
    DANGER_DARK = "#991b1b"
    WARNING = "#eab308"
    WARNING_LIGHT = "#fef9c3"
    GRAY_100 = "#f3f4f6"
    GRAY_400 = "#9ca3af"
    GRAY_200 = "#e5e7eb"


class GaugeConfig:
    """Configuration du gauge Plotly."""

    STEPS = [
        {"range": [0, 33.3], "color": Colors.SUCCESS_LIGHT},
        {"range": [33.3, 66.6], "color": Colors.WARNING_LIGHT},
        {"range": [66.6, 100], "color": Colors.DANGER_LIGHT},
    ]
    THRESHOLD_VALUE = 50
    BAR_THICKNESS = 0.75
    HEIGHT = 280


class Layout:
    """Configuration du layout."""

    FORM_RATIO = 1
    RESULT_RATIO = 1.5
    GAUGE_MARGIN = {"l": 30, "r": 30, "t": 60, "b": 30}


CSS = """
<style>
    .main > div { padding-top: 2rem; }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1e293b !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {
        display: none;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] > div {
        background: #dc2626;
        color: white !important;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
</style>
"""
