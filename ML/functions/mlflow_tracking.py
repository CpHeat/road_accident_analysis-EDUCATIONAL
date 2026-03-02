"""
Module de tracking MLflow pour le pipeline ML.

Toutes les fonctions sont non-intrusives : si MLflow est indisponible,
elles affichent un warning et retournent sans erreur.

Usage dans un notebook:
    from functions.mlflow_tracking import init_mlflow, log_training_run
    from ml_config import MLFLOW_EXPERIMENT_ACCIDENT

    mlflow_ready = init_mlflow(MLFLOW_EXPERIMENT_ACCIDENT)

    if mlflow_ready:
        log_training_run(...)
"""

import logging
import tempfile
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import confusion_matrix

logger = logging.getLogger(__name__)

# Charger le .env depuis la racine du projet (rendu/)
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(os.path.abspath(_env_path))


def init_mlflow(experiment_name: str) -> bool:
    """
    Initialise MLflow : tracking URI + experiment.

    Charge les credentials depuis les variables d'environnement :
        MLFLOW_TRACKING_USERNAME / MLFLOW_TRACKING_PASSWORD

    Args:
        experiment_name: Nom de l'experience MLflow.

    Returns:
        True si MLflow est pret, False sinon.
    """
    try:
        import mlflow
        from ml_config import MLFLOW_TRACKING_URI
    except ImportError as e:
        print(f"MLflow non disponible : {e}")
        return False

    try:
        os.environ.setdefault("MLFLOW_TRACKING_USERNAME", "")
        os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", "")

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(experiment_name)
        print(f"MLflow connecte a {MLFLOW_TRACKING_URI} (experiment: {experiment_name})")
        return True
    except Exception as e:
        print(f"MLflow indisponible ({MLFLOW_TRACKING_URI}) : {e}")
        return False


def _log_plotly_figure(fig, name: str, tmpdir: str) -> Optional[str]:
    """
    Sauvegarde une figure Plotly en PNG (fallback HTML) et retourne le chemin.
    """
    # Essayer PNG via kaleido
    try:
        path = os.path.join(tmpdir, f"{name}.png")
        fig.write_image(path, width=900, height=600, scale=2)
        return path
    except Exception:
        pass

    # Fallback HTML
    try:
        path = os.path.join(tmpdir, f"{name}.html")
        fig.write_html(path, include_plotlyjs="cdn")
        return path
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder la figure {name} : {e}")
        return None


def _log_confusion_matrix_csv(y_true, y_pred, class_labels, tmpdir: str) -> Optional[str]:
    """
    Sauvegarde la matrice de confusion en CSV et retourne le chemin.
    """
    try:
        cm = confusion_matrix(y_true, y_pred)
        if class_labels is None:
            class_labels = [str(i) for i in sorted(np.unique(y_true))]
        df_cm = pd.DataFrame(cm, index=class_labels, columns=class_labels)
        path = os.path.join(tmpdir, "confusion_matrix.csv")
        df_cm.to_csv(path)
        return path
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder la matrice de confusion : {e}")
        return None


def _get_mlflow_model_logger(model_name: str):
    """
    Retourne la fonction de logging MLflow appropriee selon le type de modele.

    Returns:
        Tuple (module, input_example_needed)
    """
    name_lower = model_name.lower()

    if "catboost" in name_lower:
        import mlflow.catboost
        return mlflow.catboost
    else:
        # sklearn Pipeline fonctionne pour RF, XGBoost, LightGBM wrapes dans Pipeline
        import mlflow.sklearn
        return mlflow.sklearn


def log_training_run(
    run_name: str,
    model: Any,
    model_name: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    y_true=None,
    y_pred=None,
    y_proba=None,
    class_labels: Optional[List[str]] = None,
    figures: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Log un run d'entrainement complet dans MLflow.

    Args:
        run_name: Nom du run (ex: "baseline_XGBoost")
        model: Modele entraine (Pipeline sklearn ou CatBoost)
        model_name: Nom de l'algorithme ("RandomForest", "XGBoost", "CatBoost", "LightGBM")
        params: Hyperparametres du modele
        metrics: Dict de metriques (accuracy, f1, roc_auc, etc.)
        y_true: Labels reels (pour matrice de confusion)
        y_pred: Predictions (pour matrice de confusion)
        y_proba: Probabilites (optionnel, pour info)
        class_labels: Noms des classes (ex: ["Non grave", "Grave"])
        figures: Dict de figures Plotly a logger comme artefacts
        tags: Tags supplementaires (ex: {"dataset": "accident", "stage": "baseline"})

    Returns:
        Le run_id MLflow si succes, None sinon.
    """
    try:
        import mlflow

        with mlflow.start_run(run_name=run_name):
            # Parametres
            safe_params = {k: v for k, v in params.items() if v is not None}
            mlflow.log_params(safe_params)

            # Metriques
            for metric_name, value in metrics.items():
                if value is not None and metric_name != "model":
                    try:
                        mlflow.log_metric(metric_name, float(value))
                    except (ValueError, TypeError):
                        pass

            # Tags
            if tags:
                mlflow.set_tags(tags)
            mlflow.set_tag("model_type", model_name)

            # Modele
            try:
                model_logger = _get_mlflow_model_logger(model_name)
                model_logger.log_model(model, artifact_path="model")
            except Exception as e:
                logger.warning(f"Impossible de logger le modele : {e}")

            # Artefacts
            with tempfile.TemporaryDirectory() as tmpdir:
                # Matrice de confusion
                if y_true is not None and y_pred is not None:
                    cm_path = _log_confusion_matrix_csv(y_true, y_pred, class_labels, tmpdir)
                    if cm_path:
                        mlflow.log_artifact(cm_path, "confusion_matrix")

                # Figures Plotly
                if figures:
                    for fig_name, fig in figures.items():
                        if fig is not None:
                            fig_path = _log_plotly_figure(fig, fig_name, tmpdir)
                            if fig_path:
                                mlflow.log_artifact(fig_path, "figures")

            run_id = mlflow.active_run().info.run_id
            print(f"  MLflow: run '{run_name}' logue (id: {run_id[:8]})")
            return run_id

    except Exception as e:
        print(f"  MLflow: erreur pour '{run_name}' : {e}")
        return None


def log_hyperopt_run(
    model_type: str,
    best_params: Dict[str, Any],
    best_score: float,
    trials: Any,
    scoring: str = "f1",
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Log les resultats d'une optimisation Hyperopt dans MLflow.

    Args:
        model_type: Type de modele ("xgboost", "catboost", etc.)
        best_params: Meilleurs hyperparametres trouves
        best_score: Meilleur score CV
        trials: Objet Trials de Hyperopt
        scoring: Metrique optimisee
        tags: Tags supplementaires

    Returns:
        Le run_id MLflow si succes, None sinon.
    """
    try:
        import mlflow

        run_name = f"hyperopt_{model_type}"

        with mlflow.start_run(run_name=run_name):
            # Parametres
            safe_params = {k: v for k, v in best_params.items() if v is not None}
            mlflow.log_params(safe_params)
            mlflow.log_param("hyperopt_max_evals", len(trials.trials))
            mlflow.log_param("hyperopt_scoring", scoring)

            # Metriques
            mlflow.log_metric(f"best_cv_{scoring}", best_score)

            # Tags
            if tags:
                mlflow.set_tags(tags)
            mlflow.set_tag("model_type", model_type)
            mlflow.set_tag("stage", "hyperopt")

            # Historique de convergence
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    scores = [t["result"].get("score", 0) for t in trials.trials]
                    df_history = pd.DataFrame({
                        "trial": range(1, len(scores) + 1),
                        "score": scores,
                        "best_so_far": np.maximum.accumulate(scores),
                    })
                    history_path = os.path.join(tmpdir, "convergence_history.csv")
                    df_history.to_csv(history_path, index=False)
                    mlflow.log_artifact(history_path, "hyperopt")
                except Exception:
                    pass

            run_id = mlflow.active_run().info.run_id
            print(f"  MLflow: hyperopt '{model_type}' logue (id: {run_id[:8]})")
            return run_id

    except Exception as e:
        print(f"  MLflow: erreur pour hyperopt '{model_type}' : {e}")
        return None


def log_final_model(
    run_name: str,
    model_path: str,
    metrics_df: pd.DataFrame,
    f1_test: float,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Log la selection finale du meilleur modele dans MLflow.

    Args:
        run_name: Nom du run (ex: "best_model_XGBoost")
        model_path: Chemin du fichier .joblib sauvegarde
        metrics_df: DataFrame des metriques de tous les candidats
        f1_test: F1 sur le test set apres reentrainement complet
        tags: Tags supplementaires

    Returns:
        Le run_id MLflow si succes, None sinon.
    """
    try:
        import mlflow

        with mlflow.start_run(run_name=run_name):
            # Metriques
            mlflow.log_metric("f1_test_final", f1_test)

            # Tags
            if tags:
                mlflow.set_tags(tags)
            mlflow.set_tag("stage", "final_selection")

            # Artefacts
            with tempfile.TemporaryDirectory() as tmpdir:
                # Tableau comparatif
                try:
                    comparison_path = os.path.join(tmpdir, "models_comparison.csv")
                    metrics_df.to_csv(comparison_path, index=False)
                    mlflow.log_artifact(comparison_path, "selection")
                except Exception:
                    pass

            # Fichier joblib
            if os.path.exists(model_path):
                mlflow.log_artifact(model_path, "model_joblib")

            run_id = mlflow.active_run().info.run_id
            print(f"  MLflow: modele final '{run_name}' logue (id: {run_id[:8]})")
            return run_id

    except Exception as e:
        print(f"  MLflow: erreur pour '{run_name}' : {e}")
        return None
