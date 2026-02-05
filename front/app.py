"""Dashboard Streamlit pour la prédiction d'accidents routiers."""

import requests
import os

import streamlit as st

from styles import CSS, Layout
from components import (
    render_prediction_form,
    render_result,
    render_empty_state,
    render_error,
    render_warning,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")


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
    st.subheader("📊 Résultat")

    if submitted:
        if not form_data.is_valid():
            render_warning("Veuillez sélectionner un département.")
        else:
            payload = form_data.to_payload()

            with st.spinner("Analyse en cours..."):
                try:
                    response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
                    response.raise_for_status()
                    result = response.json()
                    render_result(result, payload)

                except requests.exceptions.ConnectionError:
                    render_error("Impossible de se connecter à l'API. Vérifiez que le backend est lancé.")
                except requests.exceptions.RequestException as e:
                    render_error(f"Erreur : {str(e)}")
    else:
        render_empty_state()

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 0.875rem;'>"
    "Dashboard de prédiction d'accidents routiers"
    "</div>",
    unsafe_allow_html=True,
)