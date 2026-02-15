"""Contrôleur de la page de prédiction."""

import requests
import streamlit as st
from models import FormData
from services.api_service import predict
from views import render_empty_state, render_error, render_result, render_warning


def handle_prediction(form_data: FormData, submitted: bool) -> None:
    """Orchestre le flux formulaire → API → affichage."""
    st.subheader("📊 Résultat")

    if submitted:
        if not form_data.is_valid():
            render_warning("Veuillez sélectionner un département.")
        else:
            payload = form_data.to_payload()

            with st.spinner("Analyse en cours..."):
                try:
                    result = predict(payload)
                    render_result(result, payload)

                except requests.exceptions.ConnectionError:
                    render_error("Impossible de se connecter à l'API. Vérifiez que le backend est lancé.")
                except requests.exceptions.RequestException as e:
                    render_error(f"Erreur : {e!s}")
    else:
        render_empty_state()
