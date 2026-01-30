import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

logger = logging.getLogger(__name__)

# Chemin vers le modèle
MODEL_PATH = Path(__file__).parent / "models" / "model_accident_binary_optimized.joblib"

# Features dans l'ordre attendu par le modèle
FEATURE_ORDER = [
    "est_nuit", "est_heure_pointe", "jour_semaine", "est_weekend",
    "region", "dep", "agg", "vma",
    "impl_vehicule_leger", "impl_poids_lourd", "impl_pieton"
]

# Variables globales pour le pipeline
_model = None
_imputer = None
_scaler = None


def load_model():
    """Charge le modèle et les transformateurs depuis le fichier joblib."""
    global _model, _imputer, _scaler

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modèle non trouvé: {MODEL_PATH}")

    data = joblib.load(MODEL_PATH)
    _model = data["model"]
    _imputer = data["imputer"]
    _scaler = data["scaler"]


def get_pipeline():
    """Retourne le pipeline complet (model, imputer, scaler)."""
    if _model is None:
        load_model()
    return _model, _imputer, _scaler


def predict(features_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Effectue une prédiction à partir d'un dictionnaire de features.

    Args:
        features_dict: Dictionnaire avec les 11 features

    Returns:
        Dictionnaire avec gravite (0/1), probabilite_grave (float), label (str)
    """
    logger.info("--- Début du pipeline de prédiction ---")
    model, imputer, scaler = get_pipeline()

    # Créer le DataFrame avec les features dans le bon ordre
    df = pd.DataFrame([features_dict])[FEATURE_ORDER]
    logger.info(f"DataFrame créé avec colonnes: {list(df.columns)}")
    logger.info(f"Valeurs brutes: {df.iloc[0].to_dict()}")

    # Appliquer le pipeline: imputer -> scaler
    df_imputed = imputer.transform(df)
    logger.info(f"Après imputation: {df_imputed[0].tolist()}")

    df_scaled = scaler.transform(df_imputed)
    logger.info(f"Après scaling: {df_scaled[0].tolist()}")

    # Prédiction
    prediction = int(model.predict(df_scaled)[0])
    logger.info(f"Prédiction brute du modèle: {prediction}")

    # Probabilités
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(df_scaled)[0]
        prob_grave = float(proba[1])
        logger.info(f"Probabilités: [Non grave: {proba[0]:.4f}, Grave: {proba[1]:.4f}]")
    else:
        prob_grave = float(prediction)
        logger.info("Le modèle n'a pas de predict_proba")

    # Label
    label = "Grave" if prediction == 1 else "Non grave"
    logger.info(f"--- Fin du pipeline - Label: {label} ---")

    return {
        "gravite": prediction,
        "probabilite_grave": round(prob_grave, 4),
        "label": label,
    }