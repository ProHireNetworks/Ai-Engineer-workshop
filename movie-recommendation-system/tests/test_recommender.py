"""Unit Tests for Movie Recommendation System.

Tests cover:
1. Dataset loading & structure
2. Data preprocessing & cleaning
3. Insufficient rating filtering
4. Train-test splitting & data leakage prevention
5. User-Item sparse matrix construction
6. Similarity calculations (Item-Item & User-User)
7. Item-based recommendation generation & score ordering
8. User-based recommendation generation
9. Cold-start fallback for new users
10. Exclusion of already-rated movies
11. Evaluation metrics (RMSE, MAE, Precision@K, Recall@K, Coverage)
12. Model serialization (save & load)
"""

import os
import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

from src.data_loader import load_dataset, get_dataset_summary
from src.preprocessing import (
    clean_movies,
    clean_ratings,
    filter_insufficient_ratings,
    train_test_split_ratings,
    build_user_item_matrix
)
from src.similarity import (
    compute_item_similarity,
    compute_user_similarity,
    get_top_similar_items,
    get_top_similar_users
)
from src.recommender import MovieRecommender
from src.evaluation import (
    compute_rmse,
    compute_mae,
    evaluate_rating_predictions,
    evaluate_ranking_metrics,
    evaluate_catalog_coverage
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture(scope="session")
def loaded_data():
    """Loads dataset from project folder."""
    return load_dataset(data_dir="dataset")


@pytest.fixture(scope="session")
def trained_model():
    """Loads pre-trained model or trains one if missing."""
    model_path = "models/recommender_model.joblib"
    if os.path.exists(model_path):
        return MovieRecommender.load(model_path)
    # If not existing, build a lightweight test model
    movies_df, ratings_df, _, _ = load_dataset(data_dir="dataset")
    movies_clean = clean_movies(movies_df)
    ratings_clean = clean_ratings(ratings_df)
    r_filt, m_filt = filter_insufficient_ratings(ratings_clean, movies_clean, min_movie_ratings=10)
    train_r, _ = train_test_split_ratings(r_filt, test_size=0.2, random_state=42)
    model = MovieRecommender(method="item_based")
    model.fit(train_r, m_filt)
    return model


# ==============================================================================
# 1. DATASET LOADING TESTS
# ==============================================================================

def test_dataset_loading(loaded_data):
    movies_df, ratings_df, tags_df, links_df = loaded_data
    assert isinstance(movies_df, pd.DataFrame), "movies_df must be a DataFrame"
    assert isinstance(ratings_df, pd.DataFrame), "ratings_df must be a DataFrame"
    assert len(movies_df) > 0, "movies_df should not be empty"
    assert len(ratings_df) > 0, "ratings_df should not be empty"
    assert set(["movieId", "title", "genres"]).issubset(movies_df.columns)
    assert set(["userId", "movieId", "rating", "timestamp"]).issubset(ratings_df.columns)


def test_dataset_summary(loaded_data):
    movies_df, ratings_df, _, _ = loaded_data
    summary = get_dataset_summary(movies_df, ratings_df)
    assert summary["total_movies"] > 0
    assert summary["total_users"] > 0
    assert summary["total_ratings"] > 0
    assert summary["min_rating"] >= 0.5
    assert summary["max_rating"] <= 5.0
    assert 0.0 < summary["matrix_sparsity_pct"] < 100.0


# ==============================================================================
# 2. PREPROCESSING TESTS
# ==============================================================================

def test_clean_ratings_validation():
    dirty_data = pd.DataFrame({
        "userId": [1, 1, 2, np.nan, 3],
        "movieId": [10, 10, 20, 30, 40],
        "rating": [4.0, 5.0, 9.0, 3.0, -1.0],  # 9.0 and -1.0 are invalid
        "timestamp": [100, 200, 300, 400, 500]
    })
    cleaned = clean_ratings(dirty_data, min_rating=0.5, max_rating=5.0)
    assert len(cleaned) == 1, "Only valid, non-null ratings within range [0.5, 5.0] should remain"
    assert cleaned.iloc[0]["userId"] == 1
    assert cleaned.iloc[0]["rating"] == 5.0  # deduplicated to latest timestamp


def test_filter_insufficient_ratings(loaded_data):
    movies_df, ratings_df, _, _ = loaded_data
    r_clean = clean_ratings(ratings_df)
    m_clean = clean_movies(movies_df)

    filt_ratings, filt_movies = filter_insufficient_ratings(
        r_clean, m_clean, min_movie_ratings=15, min_user_ratings=5
    )
    # Check that all remaining movies have >= 15 ratings
    counts = filt_ratings["movieId"].value_counts()
    assert (counts >= 15).all(), "Every movie must meet the minimum rating threshold"
    assert len(filt_movies) == len(counts), "Catalog must match filtered movies count"


# ==============================================================================
# 3. TRAIN-TEST SPLITTING & LEAKAGE TESTS
# ==============================================================================

def test_train_test_split_isolation(loaded_data):
    _, ratings_df, _, _ = loaded_data
    r_clean = clean_ratings(ratings_df)

    train_df, test_df = train_test_split_ratings(r_clean, test_size=0.2, random_state=42)

    assert len(train_df) + len(test_df) == len(r_clean), "Splits must sum to total ratings"
    assert abs(len(test_df) / len(r_clean) - 0.2) < 0.01, "Test size should be approx 20%"

    # Verify no exact (userId, movieId, timestamp) row overlaps between train and test
    train_keys = set(zip(train_df["userId"], train_df["movieId"], train_df["timestamp"]))
    test_keys = set(zip(test_df["userId"], test_df["movieId"], test_df["timestamp"]))
    intersection = train_keys.intersection(test_keys)
    assert len(intersection) == 0, "Zero ratings may leak from test into train"


# ==============================================================================
# 4. SPARSE MATRIX TESTS
# ==============================================================================

def test_build_user_item_matrix():
    sample_ratings = pd.DataFrame({
        "userId": [1, 1, 2, 3],
        "movieId": [10, 20, 20, 30],
        "rating": [4.0, 5.0, 3.5, 2.0]
    })
    sparse_mat, u2idx, idx2u, m2idx, idx2m, df = build_user_item_matrix(sample_ratings)

    assert issparse(sparse_mat), "Matrix must be a SciPy sparse matrix"
    assert sparse_mat.shape == (3, 3), "Shape must match (num_users, num_movies)"
    assert sparse_mat[u2idx[1], m2idx[10]] == 4.0
    assert sparse_mat[u2idx[1], m2idx[20]] == 5.0
    assert sparse_mat[u2idx[2], m2idx[20]] == 3.5
    assert sparse_mat[u2idx[2], m2idx[10]] == 0.0  # unrated is 0.0


# ==============================================================================
# 5. SIMILARITY TESTS
# ==============================================================================

def test_similarity_computation():
    sample_ratings = pd.DataFrame({
        "userId": [1, 1, 2, 2, 3, 3],
        "movieId": [10, 20, 10, 20, 10, 30],
        "rating": [5.0, 5.0, 4.0, 4.0, 5.0, 1.0]
    })
    sparse_mat, u2idx, idx2u, m2idx, idx2m, _ = build_user_item_matrix(sample_ratings)

    item_sim = compute_item_similarity(sparse_mat)
    user_sim = compute_user_similarity(sparse_mat)

    # Check diagonal is 1.0 (self similarity)
    assert np.allclose(np.diag(item_sim), 1.0), "Item self-similarity must be 1.0"
    assert np.allclose(np.diag(user_sim), 1.0), "User self-similarity must be 1.0"

    # Check similarity is symmetric: sim(i, j) == sim(j, i)
    assert np.allclose(item_sim, item_sim.T), "Item similarity matrix must be symmetric"
    assert np.allclose(user_sim, user_sim.T), "User similarity matrix must be symmetric"

    # Movie 10 and 20 are co-rated identically by user 1 and user 2 -> high similarity
    idx_10 = m2idx[10]
    idx_20 = m2idx[20]
    assert item_sim[idx_10, idx_20] > 0.75, "Correlated movies must have high similarity"


# ==============================================================================
# 6. RECOMMENDATION GENERATION TESTS
# ==============================================================================

def test_recommend_item_based(trained_model):
    recs = trained_model.recommend_item_based(user_id=1, top_k=5)
    assert len(recs) == 5, "Must return exactly top-K recommendations"
    for r in recs:
        assert "movieId" in r and "title" in r and "predicted_score" in r
        assert r["predicted_score"] >= 0.0


def test_recommend_user_based(trained_model):
    recs = trained_model.recommend_user_based(user_id=1, top_k=5)
    assert len(recs) == 5
    for r in recs:
        assert "movieId" in r and "title" in r and "predicted_score" in r


def test_exclusion_of_already_rated_movies(trained_model):
    user_id = 1
    watched_movie_ids = trained_model.user_watched.get(user_id, set())
    assert len(watched_movie_ids) > 0, "User 1 should have watched movies in training set"

    # Generate item-based recs
    item_recs = trained_model.recommend_item_based(user_id=user_id, top_k=20)
    for r in item_recs:
        assert r["movieId"] not in watched_movie_ids, f"Watched movie {r['movieId']} was recommended!"

    # Generate user-based recs
    user_recs = trained_model.recommend_user_based(user_id=user_id, top_k=20)
    for r in user_recs:
        assert r["movieId"] not in watched_movie_ids, f"Watched movie {r['movieId']} was recommended!"


def test_cold_start_fallback_for_new_user(trained_model):
    # User 88888 has never rated anything
    new_user_id = 88888
    recs = trained_model.recommend(user_id=new_user_id, top_k=10)
    assert len(recs) == 10, "Must return 10 recommendations for cold-start user"
    assert all(r["method"] == "popular_fallback" for r in recs), "Must route to popular fallback"


def test_recommend_similar_movies(trained_model):
    # Toy Story (movieId=1)
    recs = trained_model.recommend_similar_movies(movie_id=1, top_k=5)
    assert len(recs) == 5
    assert all(r["movieId"] != 1 for r in recs), "Target movie must be excluded from its own similar list"
    assert recs[0]["similarity_score"] >= recs[1]["similarity_score"], "Must be sorted descending by similarity"


# ==============================================================================
# 7. EVALUATION METRICS TESTS
# ==============================================================================

def test_evaluation_metric_calculations():
    y_true = np.array([4.0, 5.0, 3.0, 2.0])
    y_pred = np.array([4.0, 4.0, 3.0, 3.0])

    # Differences: [0, 1, 0, -1] -> abs sum = 2 -> MAE = 2/4 = 0.5
    # Squared differences: [0, 1, 0, 1] -> sum = 2 -> MSE = 2/4 = 0.5 -> RMSE = sqrt(0.5) ~ 0.7071
    mae = compute_mae(y_true, y_pred)
    rmse = compute_rmse(y_true, y_pred)

    assert pytest.approx(mae, 0.001) == 0.5
    assert pytest.approx(rmse, 0.001) == 0.7071


def test_catalog_coverage(trained_model):
    users = list(trained_model.user_to_idx.keys())[:20]
    coverage = evaluate_catalog_coverage(trained_model, user_ids=users, k=5, method="item_based")
    assert 0.0 < coverage <= 100.0, "Coverage must be a valid percentage"


# ==============================================================================
# 8. MODEL SERIALIZATION TESTS
# ==============================================================================

def test_model_save_and_load(tmp_path, trained_model):
    save_path = str(tmp_path / "test_model.joblib")
    trained_model.save(save_path)
    assert os.path.exists(save_path), "Saved file must exist on disk"

    loaded = MovieRecommender.load(save_path)
    assert loaded.sparse_matrix.shape == trained_model.sparse_matrix.shape
    assert len(loaded.movie_to_idx) == len(trained_model.movie_to_idx)

    # Inferences from loaded model should match original
    orig_recs = trained_model.recommend(user_id=1, top_k=5)
    loaded_recs = loaded.recommend(user_id=1, top_k=5)
    assert [r["movieId"] for r in orig_recs] == [r["movieId"] for r in loaded_recs]
