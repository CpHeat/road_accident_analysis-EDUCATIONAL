"""Vue du formulaire de prédiction."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st
from models import DEPARTEMENTS, FormData


def render_prediction_form() -> tuple[FormData, bool]:
    """Affiche le formulaire et retourne les données + état du bouton."""
    st.subheader("📋 Paramètres")

    # Date et heure
    col_date, col_heure = st.columns(2)
    with col_date:
        date_val = st.date_input("Date", value=date.today())
    with col_heure:
        heure_now = datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M")
        heure = st.text_input("Heure", value=heure_now, placeholder="HH:MM")

    # Département
    dept_options = [f"{code} - {nom}" for code, nom in DEPARTEMENTS.items()]
    departement_select = st.selectbox("Département", options=[""] + dept_options)
    departement = departement_select.split(" - ")[0] if departement_select else ""

    # VMA et agglomération
    col_vma, col_agg = st.columns(2)
    with col_vma:
        vma = st.number_input("Vitesse max. autorisée (km/h)", min_value=20, max_value=130, value=50)
    with col_agg:
        st.write("")
        st.write("")
        agg = st.checkbox("En agglomération", value=True)

    # Véhicules impliqués
    st.markdown("**Véhicules impliqués**")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        vehicule_leger = st.checkbox("Véhicule léger", value=True)
    with col_v2:
        poids_lourd = st.checkbox("Poids lourd")
    with col_v3:
        pieton = st.checkbox("Piéton")

    st.write("")
    submitted = st.button("🔮 Prédire la gravité", type="primary")

    form_data = FormData(
        date=str(date_val),
        heure=heure,
        departement=departement,
        agg=agg,
        vma=int(vma),
        impl_vehicule_leger=vehicule_leger,
        impl_poids_lourd=poids_lourd,
        impl_pieton=pieton,
    )

    return form_data, submitted
