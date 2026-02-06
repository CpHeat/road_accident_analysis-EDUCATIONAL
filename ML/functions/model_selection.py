"""Fonctions pour la selection et sauvegarde des modeles."""

from typing import Dict, List, Callable, Any, Optional
import joblib
from sklearn.metrics import f1_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def select_best_model(models_eval: List[Dict], metric: str = "f1", average: str = "weighted") -> Dict:
    """
    Selectionne le meilleur modele parmi une liste de resultats.

    Args:
        models_eval: Liste de dictionnaires contenant:
            - 'name': str - Nom du modele
            - 'y_true': array - Labels reels
            - 'y_pred': array - Predictions
        metric: Metrique de selection ('f1' par defaut)
        average: Methode de calcul du F1 ('weighted', 'binary', 'macro')
            - 'weighted': moyenne ponderee (coherent avec display_metrics)
            - 'binary': F1 de la classe positive uniquement

    Returns:
        Dictionnaire du meilleur modele avec son score
    """
    if metric == "f1":
        best = max(models_eval, key=lambda x: f1_score(x["y_true"], x["y_pred"], average=average))
        best["score"] = f1_score(best["y_true"], best["y_pred"], average=average)
    else:
        raise ValueError(f"Metrique '{metric}' non supportee. Utilisez 'f1'.")

    return best


def save_best_model(
    best_model_name: str,
    model_configs: Dict[str, Callable],
    X_full,
    y_full,
    X_test,
    y_test,
    save_path: str,
    catboost_models: Optional[List[str]] = None,
    average: str = "weighted",
) -> Dict[str, Any]:
    """
    Entraine et sauvegarde le meilleur modele sur les donnees completes.

    Args:
        best_model_name: Nom du meilleur modele (cle dans model_configs)
        model_configs: Dict de fonctions lambda retournant les modeles configures
            Exemple: {'RF': lambda: create_pipeline(RandomForestClassifier(...))}
        X_full: Features completes pour l'entrainement final
        y_full: Target complet
        X_test: Features de test pour verification
        y_test: Target de test
        save_path: Chemin de sauvegarde (.joblib)
        catboost_models: Liste des noms de modeles CatBoost (sans pipeline)
        average: Methode de calcul du F1 ('weighted', 'binary', 'macro')

    Returns:
        Dict avec 'model', 'f1_test', 'path'

    Example:
        >>> model_configs = {
        ...     'RF': lambda: create_pipeline(RandomForestClassifier(...)),
        ...     'XGB': lambda: create_pipeline(XGBClassifier(...)),
        ...     'CatBoost': lambda: CatBoostClassifier(...)
        ... }
        >>> result = save_best_model(
        ...     'RF', model_configs, X_full, y_full, X_test, y_test,
        ...     'models/best_model.joblib'
        ... )
    """
    if catboost_models is None:
        catboost_models = ["CatBoost"]

    # Extraire la liste des features
    feature_names = (
        list(X_full.columns) if hasattr(X_full, "columns") else [f"feature_{i}" for i in range(X_full.shape[1])]
    )

    print(f"Entrainement du modele: {best_model_name}")

    # Instancier le modele
    model = model_configs[best_model_name]()

    is_catboost = best_model_name in catboost_models

    if is_catboost:
        # CatBoost sans pipeline - preprocessing manuel
        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        X_full_processed = scaler.fit_transform(imputer.fit_transform(X_full))
        model.fit(X_full_processed, y_full)

        # Sauvegarder avec les transformers
        save_object = {
            "model": model,
            "imputer": imputer,
            "scaler": scaler,
            "model_name": best_model_name,
            "feature_names": feature_names,
        }
        joblib.dump(save_object, save_path)

        # Verification
        X_test_processed = scaler.transform(imputer.transform(X_test))
        y_pred = model.predict(X_test_processed)
    else:
        # Pipeline sklearn standard
        model.fit(X_full, y_full)
        save_object = {"model": model, "model_name": best_model_name, "feature_names": feature_names}
        joblib.dump(save_object, save_path)
        y_pred = model.predict(X_test)

    f1_test = f1_score(y_test, y_pred, average=average)
    print(f"Sauvegarde: {save_path}")
    print(f"F1 sur test ({average}): {f1_test:.4f}")
    print(f"\nFeatures attendues en entree ({len(feature_names)}):")
    for i, feat in enumerate(feature_names):
        print(f"  {i + 1}. {feat}")

    return {
        "model": model,
        "f1_test": f1_test,
        "path": save_path,
        "model_name": best_model_name,
        "feature_names": feature_names,
    }
