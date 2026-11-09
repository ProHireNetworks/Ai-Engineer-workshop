"""Evaluation Metrics Module for Recommender Systems.

This module implements:
1. RMSE (Root Mean Squared Error)
2. MAE (Mean Absolute Error)
3. Precision@K
4. Recall@K
5. Catalog Coverage
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates Root Mean Squared Error (RMSE).

    Formula:
        RMSE = sqrt((1 / N) * sum((y_true - y_pred)^2))

    Args:
        y_true: Array of actual ratings.
        y_pred: Array of predicted ratings.

    Returns:
        RMSE value.
    """
    errors = y_true - y_pred
    return float(np.sqrt(np.mean(errors ** 2)))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates Mean Absolute Error (MAE).

    Formula:
        MAE = (1 / N) * sum(|y_true - y_pred|)

    Args:
        y_true: Array of actual ratings.
        y_pred: Array of predicted ratings.

    Returns:
        MAE value.
    """
    return float(np.mean(np.abs(y_true - y_pred)))


def evaluate_rating_predictions(
    recommender,
    test_ratings_df: pd.DataFrame,
    method: str = "item_based",
    max_samples: Optional[int] = 2000
) -> Dict[str, float]:
    """Evaluates RMSE and MAE for rating prediction on held-out test data.

    Args:
        recommender: Fitted MovieRecommender instance.
        test_ratings_df: Clean test ratings dataframe withheld during training.
        method: Prediction strategy ('item_based' or 'user_based').
        max_samples: Optional limit on test sample pairs to speed up evaluation.

    Returns:
        Dictionary with 'rmse', 'mae', and 'evaluated_pairs_count'.
    """
    test_data = test_ratings_df.copy()
    if max_samples and len(test_data) > max_samples:
        test_data = test_data.sample(n=max_samples, random_state=42)

    actuals = []
    predictions = []

    predict_fn = (
        recommender.predict_rating_item_based
        if method == "item_based"
        else recommender.predict_rating_user_based
    )

    for _, row in test_data.iterrows():
        u_id = int(row["userId"])
        m_id = int(row["movieId"])
        actual_rating = float(row["rating"])

        pred = predict_fn(u_id, m_id)
        if pred is not None:
            actuals.append(actual_rating)
            predictions.append(pred)

    if not actuals:
        return {"rmse": 0.0, "mae": 0.0, "evaluated_pairs_count": 0}

    y_true = np.array(actuals)
    y_pred = np.array(predictions)

    return {
        "rmse": round(compute_rmse(y_true, y_pred), 4),
        "mae": round(compute_mae(y_true, y_pred), 4),
        "evaluated_pairs_count": len(actuals)
    }


def evaluate_ranking_metrics(
    recommender,
    test_ratings_df: pd.DataFrame,
    k: int = 10,
    relevance_threshold: float = 3.5,
    method: str = "item_based",
    max_users: int = 100
) -> Dict[str, float]:
    """Calculates Precision@K and Recall@K across users on test data.

    Relevance Definition:
        A movie in the test set is considered 'relevant' to user u if actual rating >= relevance_threshold.
        Threshold choice rationale: On a 1-5 scale, 3.5+ represents clear user preference and enjoyment.

    Formulas:
        Precision@K = |Recommended@K intersect Relevant| / K
        Recall@K    = |Recommended@K intersect Relevant| / |Relevant|

    Args:
        recommender: Fitted MovieRecommender instance.
        test_ratings_df: Withheld test ratings DataFrame.
        k: Top-K list size.
        relevance_threshold: Rating cutoff for true positive relevance.
        method: Recommendation method ('item_based' or 'user_based').
        max_users: Number of users to sample for evaluation.

    Returns:
        Dictionary with 'precision_at_k', 'recall_at_k', and 'evaluated_users_count'.
    """
    # Find relevant items per user in test set
    relevant_test_ratings = test_ratings_df[test_ratings_df["rating"] >= relevance_threshold]
    user_relevant_map = relevant_test_ratings.groupby("userId")["movieId"].apply(set).to_dict()

    eligible_users = [u for u in user_relevant_map.keys() if u in recommender.user_to_idx]
    if max_users and len(eligible_users) > max_users:
        rng = np.random.RandomState(42)
        eligible_users = list(rng.choice(eligible_users, size=max_users, replace=False))

    precisions = []
    recalls = []

    for u_id in eligible_users:
        ground_truth_relevant = user_relevant_map[u_id]
        if not ground_truth_relevant:
            continue

        # Get top-K recommendations
        recs = recommender.recommend(user_id=u_id, method=method, top_k=k)
        rec_ids = {r["movieId"] for r in recs}

        # Calculate hits
        hits = len(rec_ids.intersection(ground_truth_relevant))

        precision = hits / float(k)
        recall = hits / float(len(ground_truth_relevant))

        precisions.append(precision)
        recalls.append(recall)

    mean_precision = float(np.mean(precisions)) if precisions else 0.0
    mean_recall = float(np.mean(recalls)) if recalls else 0.0

    return {
        f"precision_at_{k}": round(mean_precision, 4),
        f"recall_at_{k}": round(mean_recall, 4),
        "evaluated_users_count": len(precisions)
    }


def evaluate_catalog_coverage(
    recommender,
    user_ids: List[int],
    k: int = 10,
    method: str = "item_based"
) -> float:
    """Calculates catalog coverage of recommendations.

    Formula:
        Coverage = |Unique Recommended Items across all users| / |Total Items in Catalog|

    Args:
        recommender: Fitted MovieRecommender instance.
        user_ids: List of userIds to generate recommendations for.
        k: Top-K recommendations.
        method: Recommendation strategy.

    Returns:
        Percentage of catalog covered (in [0.0, 100.0]).
    """
    if recommender.movies_df is None or len(recommender.movies_df) == 0:
        return 0.0

    total_catalog_items = len(recommender.movie_to_idx)
    if total_catalog_items == 0:
        return 0.0

    recommended_items = set()
    for u_id in user_ids:
        recs = recommender.recommend(user_id=u_id, method=method, top_k=k)
        for r in recs:
            recommended_items.add(r["movieId"])

    coverage_pct = (len(recommended_items) / float(total_catalog_items)) * 100.0
    return round(coverage_pct, 2)


def run_full_evaluation(
    recommender,
    test_ratings_df: pd.DataFrame,
    k: int = 10,
    relevance_threshold: float = 3.5,
    num_eval_users: int = 100,
    max_rating_pairs: int = 2000
) -> Dict[str, Dict[str, float]]:
    """Runs end-to-end evaluation comparing Item-Based and User-Based Collaborative Filtering.

    Args:
        recommender: Fitted MovieRecommender.
        test_ratings_df: Test set DataFrame.
        k: Cutoff for ranking metrics.
        relevance_threshold: Rating cutoff for relevant items.
        num_eval_users: Number of users to sample for ranking evaluation.
        max_rating_pairs: Number of test pairs for RMSE/MAE.

    Returns:
        Dictionary mapping model names to their evaluation metrics.
    """
    results = {}

    for method in ["item_based", "user_based"]:
        # Rating error metrics
        rating_metrics = evaluate_rating_predictions(
            recommender=recommender,
            test_ratings_df=test_ratings_df,
            method=method,
            max_samples=max_rating_pairs
        )

        # Ranking metrics
        ranking_metrics = evaluate_ranking_metrics(
            recommender=recommender,
            test_ratings_df=test_ratings_df,
            k=k,
            relevance_threshold=relevance_threshold,
            method=method,
            max_users=num_eval_users
        )

        # Sample user list for coverage
        sample_users = list(recommender.user_to_idx.keys())[:num_eval_users]
        coverage = evaluate_catalog_coverage(
            recommender=recommender,
            user_ids=sample_users,
            k=k,
            method=method
        )

        results[method] = {
            "RMSE": rating_metrics["rmse"],
            "MAE": rating_metrics["mae"],
            f"Precision@{k}": ranking_metrics[f"precision_at_{k}"],
            f"Recall@{k}": ranking_metrics[f"recall_at_{k}"],
            f"Coverage@{k} (%)": coverage,
            "Evaluated_Ratings": rating_metrics["evaluated_pairs_count"],
            "Evaluated_Users": ranking_metrics["evaluated_users_count"]
        }

    return results

