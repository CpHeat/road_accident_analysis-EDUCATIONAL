"""
Module d'optimisation bayesienne des hyperparametres pour modeles boostes.

Fournit une fonction unique `optimize_boosting_model` pour trouver les meilleurs
hyperparametres de XGBoost, LightGBM, CatBoost ou RandomForest via Hyperopt.

Usage dans un notebook:
    from ML.functions.hyperopt_tuning import optimize_boosting_model

    best_params, best_score, trials = optimize_boosting_model(
        X_train, y_train,
        model_type='catboost',
        max_evals=50,
        scoring='f1'
    )
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Literal
from sklearn.model_selection import cross_val_score
from sklearn.impute import SimpleImputer
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials


# Espaces de recherche par defaut pour chaque type de modele
DEFAULT_SEARCH_SPACES = {
    "xgboost": {
        "n_estimators": hp.quniform("n_estimators", 100, 500, 50),
        "max_depth": hp.quniform("max_depth", 3, 10, 1),
        "learning_rate": hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
        "min_child_weight": hp.quniform("min_child_weight", 1, 10, 1),
        "subsample": hp.uniform("subsample", 0.6, 1.0),
        "colsample_bytree": hp.uniform("colsample_bytree", 0.6, 1.0),
    },
    "lightgbm": {
        "n_estimators": hp.quniform("n_estimators", 100, 500, 50),
        "max_depth": hp.quniform("max_depth", 3, 10, 1),
        "learning_rate": hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
        "num_leaves": hp.quniform("num_leaves", 20, 100, 10),
        "min_child_samples": hp.quniform("min_child_samples", 5, 50, 5),
        "subsample": hp.uniform("subsample", 0.6, 1.0),
        "colsample_bytree": hp.uniform("colsample_bytree", 0.6, 1.0),
    },
    "catboost": {
        "iterations": hp.quniform("iterations", 100, 500, 50),
        "learning_rate": hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
        "depth": hp.quniform("depth", 4, 10, 1),
        "l2_leaf_reg": hp.loguniform("l2_leaf_reg", np.log(1), np.log(10)),
    },
    "randomforest": {
        "n_estimators": hp.quniform("n_estimators", 50, 400, 50),
        "max_depth": hp.choice("max_depth", [5, 10, 15, 20, 25, None]),
        "min_samples_split": hp.quniform("min_samples_split", 2, 20, 1),
        "min_samples_leaf": hp.quniform("min_samples_leaf", 1, 10, 1),
        "max_features": hp.choice("max_features", ["sqrt", "log2", None]),
    },
}


def _get_model_class(model_type: str):
    """Importe et retourne la classe du modele."""
    model_type = model_type.lower()

    if model_type == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier
    elif model_type == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier
    elif model_type == "catboost":
        from catboost import CatBoostClassifier

        return CatBoostClassifier
    elif model_type == "randomforest":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier
    else:
        raise ValueError(
            f"model_type inconnu: {model_type}. Valeurs acceptees: xgboost, lightgbm, catboost, randomforest"
        )


def _convert_params(params: Dict, model_type: str) -> Dict:
    """Convertit les parametres Hyperopt en parametres utilisables par le modele."""
    model_type = model_type.lower()
    converted = {}

    for key, value in params.items():
        # Parametres entiers
        int_params = {
            "n_estimators",
            "max_depth",
            "min_child_weight",
            "num_leaves",
            "min_child_samples",
            "iterations",
            "depth",
            "min_samples_split",
            "min_samples_leaf",
        }

        if key in int_params and value is not None:
            converted[key] = int(value)
        else:
            converted[key] = value

    # Gestion speciale pour RandomForest max_depth (hp.choice retourne un index)
    if model_type == "randomforest" and "max_depth" in params:
        max_depth_choices = [5, 10, 15, 20, 25, None]
        if isinstance(params["max_depth"], int) and params["max_depth"] < len(max_depth_choices):
            converted["max_depth"] = max_depth_choices[params["max_depth"]]

    # Gestion speciale pour RandomForest max_features
    if model_type == "randomforest" and "max_features" in params:
        max_features_choices = ["sqrt", "log2", None]
        if isinstance(params["max_features"], int) and params["max_features"] < len(max_features_choices):
            converted["max_features"] = max_features_choices[params["max_features"]]

    return converted


def _get_default_model_kwargs(model_type: str, random_state: int, n_jobs: int) -> Dict:
    """Retourne les kwargs par defaut pour chaque type de modele."""
    model_type = model_type.lower()

    if model_type == "xgboost":
        return {
            "random_state": random_state,
            "n_jobs": n_jobs,
            "eval_metric": "logloss",
        }
    elif model_type == "lightgbm":
        return {
            "random_state": random_state,
            "n_jobs": n_jobs,
            "verbose": -1,
        }
    elif model_type == "catboost":
        return {
            "random_state": random_state,
            "verbose": False,
            "auto_class_weights": "Balanced",
        }
    elif model_type == "randomforest":
        return {
            "random_state": random_state,
            "n_jobs": n_jobs,
            "class_weight": "balanced",
        }
    return {}


def optimize_boosting_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    model_type: Literal["xgboost", "lightgbm", "catboost", "randomforest"],
    max_evals: int = 50,
    cv: int = 3,
    scoring: str = "f1",
    search_space: Optional[Dict] = None,
    random_state: int = 42,
    n_jobs: int = -1,
    show_progress: bool = True,
) -> Tuple[Dict, float, Trials]:
    """
    Optimise les hyperparametres d'un modele booste via Hyperopt.

    Args:
        X_train: Features d'entrainement
        y_train: Labels d'entrainement
        model_type: Type de modele ('xgboost', 'lightgbm', 'catboost', 'randomforest')
        max_evals: Nombre d'evaluations Hyperopt
        cv: Nombre de folds pour la cross-validation
        scoring: Metrique a optimiser ('f1', 'accuracy', 'roc_auc', etc.)
        search_space: Espace de recherche personnalise (None = defaut)
        random_state: Seed pour reproductibilite
        n_jobs: Nombre de jobs paralleles (-1 = tous les cores)
        show_progress: Afficher la barre de progression

    Returns:
        Tuple contenant:
            - best_params: Dict des meilleurs hyperparametres
            - best_score: Meilleur score obtenu (CV)
            - trials: Objet Trials Hyperopt (historique)

    Example:
        >>> best_params, best_score, trials = optimize_boosting_model(
        ...     X_train, y_train,
        ...     model_type='catboost',
        ...     max_evals=50
        ... )
        >>> # Utiliser les params pour creer le modele
        >>> model = CatBoostClassifier(**best_params, random_state=42, verbose=False)
    """
    model_type = model_type.lower()

    # Validation
    if model_type not in DEFAULT_SEARCH_SPACES:
        raise ValueError(
            f"model_type '{model_type}' non supporte. Valeurs acceptees: {list(DEFAULT_SEARCH_SPACES.keys())}"
        )

    # Espace de recherche
    space = search_space if search_space is not None else DEFAULT_SEARCH_SPACES[model_type]

    # Classe du modele
    ModelClass = _get_model_class(model_type)

    # Kwargs par defaut
    default_kwargs = _get_default_model_kwargs(model_type, random_state, n_jobs)

    # Gestion du desequilibre pour XGBoost
    if model_type == "xgboost":
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        if n_pos > 0:
            default_kwargs["scale_pos_weight"] = n_neg / n_pos

    # Preprocessing (imputation) - preserver les noms de colonnes si DataFrame
    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X_train)
    if hasattr(X_train, "columns"):
        X_imputed = pd.DataFrame(X_imputed, columns=X_train.columns, index=X_train.index)

    def objective(params):
        """Fonction objectif pour Hyperopt."""
        converted_params = _convert_params(params, model_type)

        try:
            model = ModelClass(**converted_params, **default_kwargs)
            scores = cross_val_score(model, X_imputed, y_train, cv=cv, scoring=scoring, n_jobs=n_jobs)
            score = scores.mean()
            return {"loss": -score, "status": STATUS_OK, "score": score, "std": scores.std()}
        except Exception as e:
            return {"loss": 0, "status": STATUS_OK, "score": 0, "std": 0, "error": str(e)}

    # Lancer l'optimisation
    print(f"Optimisation Hyperopt pour {model_type.upper()}...")
    print(f"  - max_evals: {max_evals}")
    print(f"  - cv: {cv} folds")
    print(f"  - scoring: {scoring}")
    print()

    trials = Trials()
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=max_evals,
        trials=trials,
        rstate=np.random.default_rng(random_state),
        show_progressbar=show_progress,
    )

    # Convertir les meilleurs parametres
    best_params = _convert_params(best, model_type)

    # Recuperer le meilleur score
    best_trial_idx = np.argmin([t["result"]["loss"] for t in trials.trials])
    best_score = trials.trials[best_trial_idx]["result"]["score"]
    best_std = trials.trials[best_trial_idx]["result"]["std"]

    print()
    print(f"Meilleurs parametres {model_type.upper()}:")
    for k, v in best_params.items():
        print(f"  - {k}: {v}")
    print(f"\nMeilleur {scoring} (CV): {best_score:.4f} (+/- {best_std:.4f})")

    return best_params, best_score, trials


def plot_optimization_history(trials: Trials, scoring: str = "score") -> None:
    """
    Affiche l'historique de convergence de l'optimisation.

    Args:
        trials: Objet Trials de Hyperopt
        scoring: Nom de la metrique optimisee
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly requis pour la visualisation")
        return

    scores = [t["result"]["score"] for t in trials.trials]
    best_so_far = np.maximum.accumulate(scores)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(scores) + 1)),
            y=scores,
            mode="markers",
            name="Score par essai",
            marker=dict(size=6, opacity=0.6),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(best_so_far) + 1)),
            y=best_so_far,
            mode="lines",
            name="Meilleur score",
            line=dict(color="red", width=2),
        )
    )

    fig.update_layout(
        title="Convergence Hyperopt", xaxis_title="Numero essai", yaxis_title=scoring.upper(), height=400, width=700
    )

    fig.show()
