"""Composant d'affichage des résultats."""

import streamlit as st

from .charts import create_gauge


def render_result(result: dict, payload: dict) -> None:
    """Affiche le résultat de la prédiction."""
    prob = result["probabilite_grave"]
    label = result["label"]
    is_grave = result["gravite"] == 1

    # Métriques
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(
            label="Prédiction",
            value=label,
            delta="Risque élevé" if is_grave else "Risque faible",
            delta_color="inverse",
        )
    with col_m2:
        st.metric(
            label="Probabilité d'accident grave",
            value=f"{prob:.1%}",
        )

    # Gauge
    fig = create_gauge(prob, label)
    st.plotly_chart(fig, use_container_width=True)

    # Détails
    with st.expander("📝 Détails de la requête"):
        st.json(payload)


def render_empty_state() -> None:
    """Affiche l'état vide."""
    st.info("👈 Remplissez le formulaire et cliquez sur **Prédire** pour obtenir une estimation.")


def render_error(message: str) -> None:
    """Affiche une erreur."""
    st.error(message)


def render_warning(message: str) -> None:
    """Affiche un avertissement."""
    st.warning(message)