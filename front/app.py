"""Dashboard Streamlit pour la prédiction d'accidents routiers."""

import streamlit as st
from controllers.prediction import handle_prediction
from styles import CSS, Layout
from views import render_prediction_form

# Configuration page
st.set_page_config(
    page_title="Prédiction Accidents Routiers",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injection CSS
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.title("🚗 Prédiction de Gravité des Accidents")
st.markdown("Estimez la gravité potentielle d'un accident routier en fonction des conditions.")
st.divider()

# Layout principal
col_form, col_result = st.columns([Layout.FORM_RATIO, Layout.RESULT_RATIO], gap="large")

with col_form:
    form_data, submitted = render_prediction_form()

with col_result:
    handle_prediction(form_data, submitted)

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 0.875rem;'>"
    "Dashboard de prédiction d'accidents routiers"
    "</div>",
    unsafe_allow_html=True,
)
