"""Composant formulaire de prédiction."""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass

import streamlit as st


DEPARTEMENTS = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "21": "Côte-d'Or",
    "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne", "25": "Doubs",
    "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "2A": "Corse-du-Sud", "2B": "Haute-Corse",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde",
    "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire",
    "38": "Isère", "39": "Jura", "40": "Landes", "41": "Loir-et-Cher",
    "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret",
    "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire",
    "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne",
    "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan", "57": "Moselle",
    "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres",
    "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var",
    "84": "Vaucluse", "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne",
    "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "976": "Mayotte",
}


@dataclass
class FormData:
    """Données du formulaire."""
    date: str
    heure: str
    departement: str
    agg: bool
    vma: int
    impl_vehicule_leger: bool
    impl_poids_lourd: bool
    impl_pieton: bool

    def to_payload(self) -> dict:
        """Convertit en payload pour l'API."""
        return {
            "date": self.date,
            "heure": format_heure(self.heure),
            "departement": self.departement,
            "agg": self.agg,
            "vma": self.vma,
            "impl_vehicule_leger": self.impl_vehicule_leger,
            "impl_poids_lourd": self.impl_poids_lourd,
            "impl_pieton": self.impl_pieton,
        }

    def is_valid(self) -> bool:
        """Vérifie si le formulaire est valide."""
        return bool(self.departement)


def format_heure(heure: str) -> str:
    """Formate l'heure au format HH:MM."""
    match = re.match(r"(\d{1,2})[h:](\d{1,2})", heure.strip())
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return f"{h:02d}:{m:02d}"
    return heure


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