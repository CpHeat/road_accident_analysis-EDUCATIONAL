"""
Module de visualisation des metriques ML.

Fournit une fonction unique `show_all_metrics` pour afficher de maniere
coherente et complete les performances d'un ou plusieurs modeles.

Usage dans un notebook:
    from ML.functions.show_metrics import show_all_metrics

    show_all_metrics(
        models_results=[
            {"name": "RandomForest", "y_true": y_test, "y_pred": y_pred_rf, "y_proba": y_proba_rf},
            {"name": "XGBoost", "y_true": y_test, "y_pred": y_pred_xgb, "y_proba": y_proba_xgb},
        ],
        class_labels=["Non grave", "Grave"]
    )
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    auc,
    matthews_corrcoef,
    balanced_accuracy_score,
)
from typing import List, Dict, Optional, Union


def _compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: Optional[np.ndarray] = None, average: str = "weighted"
) -> Dict[str, float]:
    """
    Calcule toutes les metriques de classification.

    Args:
        y_true: Labels reels
        y_pred: Predictions
        y_proba: Probabilites (optionnel, pour AUC)
        average: Methode d'agregation pour multiclasse ('weighted', 'macro', 'micro')

    Returns:
        Dictionnaire avec toutes les metriques
    """
    is_binary = len(np.unique(y_true)) == 2

    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average=average, zero_division=0),
        "recall": recall_score(y_true, y_pred, average=average, zero_division=0),
        "f1": f1_score(y_true, y_pred, average=average, zero_division=0),
    }

    # Metriques specifiques binaires
    if is_binary:
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            metrics["specificity"] = tn / (tn + fp) if (tn + fp) > 0 else 0
            metrics["sensitivity"] = tp / (tp + fn) if (tp + fn) > 0 else 0  # = recall
        metrics["mcc"] = matthews_corrcoef(y_true, y_pred)

        # AUC
        if y_proba is not None:
            y_score = y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba
            metrics["roc_auc"] = roc_auc_score(y_true, y_score)
    else:
        # AUC multiclasse (One-vs-Rest)
        if y_proba is not None:
            try:
                metrics["roc_auc"] = roc_auc_score(y_true, y_proba, multi_class="ovr", average=average)
            except ValueError:
                metrics["roc_auc"] = None

    return metrics


def _plot_confusion_matrices(
    models_results: List[Dict],
    class_labels: Optional[List[str]] = None,
    normalize: bool = True,
    show_counts: bool = True,
    colorscale: str = "Blues",
) -> go.Figure:
    """
    Affiche les matrices de confusion pour un ou plusieurs modeles.

    Args:
        models_results: Liste de dict avec 'name', 'y_true', 'y_pred'
        class_labels: Labels des classes
        normalize: Afficher les pourcentages par ligne
        show_counts: Afficher aussi les valeurs absolues
        colorscale: Palette de couleurs Plotly

    Returns:
        Figure Plotly
    """
    n_models = len(models_results)

    # Calcul du layout de la grille
    n_cols = min(n_models, 3)
    n_rows = (n_models + n_cols - 1) // n_cols

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[m["name"] for m in models_results],
        horizontal_spacing=0.1,
        vertical_spacing=0.15,
    )

    for idx, model in enumerate(models_results):
        row = idx // n_cols + 1
        col = idx % n_cols + 1

        y_true = model["y_true"]
        y_pred = model["y_pred"]
        name = model["name"]

        cm = confusion_matrix(y_true, y_pred)

        if class_labels is None:
            labels = [str(i) for i in sorted(np.unique(y_true))]
        else:
            labels = class_labels

        # Normalisation par ligne (recall par classe)
        if normalize:
            cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis] * 100
        else:
            cm_norm = cm.astype("float")

        # Annotations
        text_annotations = []
        for i in range(len(cm)):
            row_text = []
            for j in range(len(cm[0])):
                if show_counts and normalize:
                    row_text.append(f"{cm[i][j]}<br>({cm_norm[i][j]:.1f}%)")
                elif normalize:
                    row_text.append(f"{cm_norm[i][j]:.1f}%")
                else:
                    row_text.append(f"{cm[i][j]}")
            text_annotations.append(row_text)

        heatmap = go.Heatmap(
            z=cm_norm,
            x=labels,
            y=labels,
            text=text_annotations,
            texttemplate="%{text}",
            colorscale=colorscale,
            showscale=(idx == n_models - 1),  # Echelle sur le dernier uniquement
            hovertemplate="Reel: %{y}<br>Predit: %{x}<br>Valeur: %{text}<extra></extra>",
        )

        fig.add_trace(heatmap, row=row, col=col)

        # Titres des axes
        fig.update_xaxes(title_text="Prediction", row=row, col=col)
        fig.update_yaxes(title_text="Realite", row=row, col=col)

    fig.update_layout(
        title="Matrices de Confusion",
        height=350 * n_rows,
        width=400 * n_cols,
    )

    return fig


def _plot_roc_curves(models_results: List[Dict], class_labels: Optional[List[str]] = None) -> Optional[go.Figure]:
    """
    Affiche les courbes ROC pour un ou plusieurs modeles (binaire ou multiclasse).

    Args:
        models_results: Liste de dict avec 'name', 'y_true', 'y_proba'
        class_labels: Labels des classes (pour multiclasse)

    Returns:
        Figure Plotly ou None si pas de probabilites
    """
    # Filtrer les modeles avec probabilites
    valid_models = [m for m in models_results if m.get("y_proba") is not None]

    if not valid_models:
        print("ROC non disponible: aucun modele avec probabilites")
        return None

    # Determiner si binaire ou multiclasse
    first_y_true = valid_models[0]["y_true"]
    n_classes = len(np.unique(first_y_true))
    is_binary = n_classes == 2

    if is_binary:
        return _plot_roc_binary(valid_models)
    else:
        return _plot_roc_multiclass(valid_models, class_labels)


def _plot_roc_binary(models_results: List[Dict]) -> go.Figure:
    """Courbes ROC pour classification binaire."""
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c"]

    fig = go.Figure()

    for idx, model in enumerate(models_results):
        y_true = model["y_true"]
        y_proba = model["y_proba"]
        name = model["name"]

        y_score = y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba
        fpr, tpr, _ = roc_curve(y_true, y_score)
        roc_auc = auc(fpr, tpr)

        color = colors[idx % len(colors)]

        fig.add_trace(
            go.Scatter(
                x=fpr, y=tpr, mode="lines", name=f"{name} (AUC = {roc_auc:.3f})", line=dict(color=color, width=2)
            )
        )

    # Ligne de reference (random)
    fig.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="Random (AUC = 0.5)", line=dict(color="gray", width=1, dash="dash")
        )
    )

    fig.update_layout(
        title="Courbes ROC",
        xaxis_title="Taux de Faux Positifs (FPR)",
        yaxis_title="Taux de Vrais Positifs (TPR)",
        width=650,
        height=500,
        legend=dict(x=0.6, y=0.1),
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1.05]),
    )

    return fig


def _plot_roc_multiclass(models_results: List[Dict], class_labels: Optional[List[str]] = None) -> go.Figure:
    """Courbes ROC One-vs-Rest pour classification multiclasse."""
    n_models = len(models_results)

    fig = make_subplots(
        rows=1, cols=n_models, subplot_titles=[m["name"] for m in models_results], horizontal_spacing=0.1
    )

    colors = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c"]

    for model_idx, model in enumerate(models_results):
        y_true = model["y_true"]
        y_proba = model["y_proba"]

        classes = sorted(np.unique(y_true))
        n_classes = len(classes)

        if class_labels is None:
            labels = [str(c) for c in classes]
        else:
            labels = class_labels

        for class_idx, cls in enumerate(classes):
            y_true_bin = (y_true == cls).astype(int)
            y_score = y_proba[:, class_idx]

            fpr, tpr, _ = roc_curve(y_true_bin, y_score)
            roc_auc = auc(fpr, tpr)

            color = colors[class_idx % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=fpr,
                    y=tpr,
                    mode="lines",
                    name=f"{labels[class_idx]} (AUC={roc_auc:.2f})",
                    line=dict(color=color, width=2),
                    showlegend=(model_idx == 0),  # Legende uniquement sur le premier
                ),
                row=1,
                col=model_idx + 1,
            )

        # Ligne random
        fig.add_trace(
            go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines", line=dict(color="gray", width=1, dash="dash"), showlegend=False
            ),
            row=1,
            col=model_idx + 1,
        )

    fig.update_layout(
        title="Courbes ROC (One-vs-Rest)",
        height=450,
        width=500 * n_models,
    )

    for i in range(n_models):
        fig.update_xaxes(title_text="FPR", row=1, col=i + 1, range=[0, 1])
        fig.update_yaxes(title_text="TPR", row=1, col=i + 1, range=[0, 1.05])

    return fig


def _plot_metrics_comparison(
    models_results: List[Dict], metrics_to_show: Optional[List[str]] = None, average: str = "weighted"
) -> go.Figure:
    """
    Affiche un graphique en barres comparant les metriques de plusieurs modeles.

    Args:
        models_results: Liste de dict avec 'name', 'y_true', 'y_pred', 'y_proba'
        metrics_to_show: Liste des metriques a afficher (None = toutes)
        average: Methode d'agregation pour multiclasse

    Returns:
        Figure Plotly
    """
    # Calcul des metriques pour chaque modele
    all_metrics = []
    for model in models_results:
        m = _compute_metrics(model["y_true"], model["y_pred"], model.get("y_proba"), average=average)
        m["name"] = model["name"]
        all_metrics.append(m)

    df = pd.DataFrame(all_metrics)

    # Selection des metriques a afficher
    if metrics_to_show is None:
        # Metriques par defaut
        metrics_to_show = ["accuracy", "precision", "recall", "f1"]
        if "roc_auc" in df.columns and df["roc_auc"].notna().any():
            metrics_to_show.append("roc_auc")
        if "mcc" in df.columns:
            metrics_to_show.append("mcc")

    # Filtrer les metriques disponibles
    metrics_to_show = [m for m in metrics_to_show if m in df.columns]

    colors = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c"]

    fig = go.Figure()

    for idx, row in df.iterrows():
        values = [row[m] if pd.notna(row[m]) else 0 for m in metrics_to_show]

        fig.add_trace(
            go.Bar(
                name=row["name"],
                x=metrics_to_show,
                y=values,
                text=[f"{v:.3f}" for v in values],
                textposition="outside",
                marker_color=colors[idx % len(colors)],
            )
        )

    fig.update_layout(
        title="Comparaison des Metriques",
        barmode="group",
        height=450,
        width=max(600, 100 * len(metrics_to_show) * len(df)),
        yaxis_range=[0, 1.15],
        xaxis_title="Metrique",
        yaxis_title="Score",
        legend=dict(orientation="h", y=1.1),
    )

    return fig


def _get_metrics_table(models_results: List[Dict], average: str = "weighted") -> pd.DataFrame:
    """
    Retourne un DataFrame avec toutes les metriques pour chaque modele.

    Args:
        models_results: Liste de dict avec 'name', 'y_true', 'y_pred', 'y_proba'
        average: Methode d'agregation pour multiclasse

    Returns:
        DataFrame avec les metriques
    """
    all_metrics = []

    for model in models_results:
        m = _compute_metrics(model["y_true"], model["y_pred"], model.get("y_proba"), average=average)
        m["model"] = model["name"]
        all_metrics.append(m)

    df = pd.DataFrame(all_metrics)

    # Reordonner les colonnes
    cols_order = [
        "model",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "mcc",
        "specificity",
        "sensitivity",
    ]
    cols_order = [c for c in cols_order if c in df.columns]

    return df[cols_order].round(4)


def display_metrics(
    models_results: List[Dict],
    class_labels: Optional[List[str]] = None,
    show_confusion_matrix: bool = True,
    show_roc_curve: bool = True,
    show_bar_chart: bool = True,
    show_table: bool = True,
    average: str = "weighted",
    normalize_cm: bool = True,
) -> Dict:
    """
    Affiche toutes les metriques pour un ou plusieurs modeles.

    C'est la fonction principale a utiliser dans les notebooks.

    Args:
        models_results: Liste de dictionnaires, chaque dict contenant:
            - 'name': str - Nom du modele
            - 'y_true': array - Labels reels
            - 'y_pred': array - Predictions
            - 'y_proba': array (optionnel) - Probabilites pour ROC/AUC

        class_labels: Liste des labels de classes (optionnel)
        show_confusion_matrix: Afficher les matrices de confusion
        show_roc_curve: Afficher les courbes ROC
        show_bar_chart: Afficher le graphique comparatif
        show_table: Afficher le tableau des metriques
        average: 'weighted', 'macro', ou 'micro' pour multiclasse
        normalize_cm: Normaliser les matrices de confusion (pourcentages)

    Returns:
        Dictionnaire avec:
            - 'metrics_df': DataFrame des metriques
            - 'figures': Dict des figures Plotly

    Example:
        >>> results = show_all_metrics(
        ...     models_results=[
        ...         {"name": "RF", "y_true": y_test, "y_pred": pred_rf, "y_proba": proba_rf},
        ...         {"name": "XGB", "y_true": y_test, "y_pred": pred_xgb, "y_proba": proba_xgb},
        ...     ],
        ...     class_labels=["Non grave", "Grave"]
        ... )
    """
    figures = {}

    # Validation
    if not models_results:
        raise ValueError("models_results ne peut pas etre vide")

    for m in models_results:
        if "name" not in m or "y_true" not in m or "y_pred" not in m:
            raise ValueError("Chaque modele doit avoir 'name', 'y_true', 'y_pred'")

    print("=" * 70)
    print(f"EVALUATION DES MODELES ({len(models_results)} modele(s))")
    print("=" * 70)

    # 1. Tableau des metriques
    metrics_df = _get_metrics_table(models_results, average=average)

    if show_table:
        print("\n📊 TABLEAU DES METRIQUES")
        print("-" * 70)
        print(metrics_df.to_string(index=False))
        print()

    # 2. Graphique comparatif
    if show_bar_chart and len(models_results) > 0:
        fig_bar = _plot_metrics_comparison(models_results, average=average)
        figures["bar_chart"] = fig_bar
        fig_bar.show()

    # 3. Matrices de confusion
    if show_confusion_matrix:
        print("\n📈 MATRICES DE CONFUSION")
        print("-" * 70)
        fig_cm = _plot_confusion_matrices(models_results, class_labels=class_labels, normalize=normalize_cm)
        figures["confusion_matrices"] = fig_cm
        fig_cm.show()

    # 4. Courbes ROC
    if show_roc_curve:
        print("\n📉 COURBES ROC")
        print("-" * 70)
        fig_roc = _plot_roc_curves(models_results, class_labels=class_labels)
        if fig_roc:
            figures["roc_curves"] = fig_roc
            fig_roc.show()

    # 5. Resume
    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)

    # Meilleur modele selon F1
    best_idx = metrics_df["f1"].idxmax()
    best_model = metrics_df.loc[best_idx, "model"]
    best_f1 = metrics_df.loc[best_idx, "f1"]

    print(f"Meilleur modele (F1): {best_model} (F1 = {best_f1:.4f})")

    if "roc_auc" in metrics_df.columns and metrics_df["roc_auc"].notna().any():
        best_auc_idx = metrics_df["roc_auc"].idxmax()
        best_auc_model = metrics_df.loc[best_auc_idx, "model"]
        best_auc = metrics_df.loc[best_auc_idx, "roc_auc"]
        print(f"Meilleur modele (AUC): {best_auc_model} (AUC = {best_auc:.4f})")

    print("=" * 70)

    return {"metrics_df": metrics_df, "figures": figures}
