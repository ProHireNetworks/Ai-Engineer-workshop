"""Model Training & Artifact Serialization Pipeline.

Separates training from serving:
1. Loads raw MovieLens data.
2. Cleans and filters sparse items.
3. Performs reproducible train-test split without data leakage.
4. Fits Item-Based and User-Based Collaborative Filtering models.
5. Evaluates model performance on test set.
6. Serializes model artifact to `models/recommender_model.joblib`.
"""

import os
from typing import Dict, Any
import pandas as pd

from src.data_loader import load_dataset, get_dataset_summary
from src.preprocessing import (
    clean_movies,
    clean_ratings,
    filter_insufficient_ratings,
    train_test_split_ratings,
)
from src.recommender import MovieRecommender
from src.evaluation import run_full_evaluation


def train_and_save_pipeline(
    data_dir: str = "dataset",
    model_output_path: str = "models/recommender_model.joblib",
    min_movie_ratings: int = 10,
    min_user_ratings: int = 5,
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """Executes the complete recommendation model training pipeline.

    Args:
        data_dir: Folder containing CSV files.
        model_output_path: Destination path for serialized model.
        min_movie_ratings: Minimum ratings cutoff for movies.
        min_user_ratings: Minimum ratings cutoff for users.
        test_size: Fraction of ratings withheld for testing.
        random_state: Seed for reproducibility.

    Returns:
        Dictionary with training statistics and evaluation results.
    """
    print("=" * 65)
    print("🎬 STARTING MOVIE RECOMMENDATION SYSTEM TRAINING PIPELINE")
    print("=" * 65)

    # 1. Load Data
    print("\n[Step 1/6] Loading MovieLens dataset...")
    movies_raw, ratings_raw, tags_raw, links_raw = load_dataset(data_dir=data_dir)
    raw_summary = get_dataset_summary(movies_raw, ratings_raw)
    print(f"  • Raw Movies: {int(raw_summary['total_movies']):,}")
    print(f"  • Raw Ratings: {int(raw_summary['total_ratings']):,}")
    print(f"  • Unique Users: {int(raw_summary['total_users']):,}")
    print(f"  • Matrix Sparsity: {raw_summary['matrix_sparsity_pct']}%")

    # 2. Clean & Preprocess Data
    print("\n[Step 2/6] Cleaning data and filtering sparse items...")
    movies_clean = clean_movies(movies_raw)
    ratings_clean = clean_ratings(ratings_raw)

    ratings_filtered, movies_filtered = filter_insufficient_ratings(
        ratings_clean,
        movies_clean,
        min_movie_ratings=min_movie_ratings,
        min_user_ratings=min_user_ratings
    )
    print(f"  • Retained Movies (>= {min_movie_ratings} ratings): {len(movies_filtered):,}")
    print(f"  • Retained Ratings: {len(ratings_filtered):,}")
    print(f"  • Retained Users: {ratings_filtered['userId'].nunique():,}")

    # 3. Train-Test Split (Prevent Data Leakage)
    print(f"\n[Step 3/6] Splitting ratings (train: {int((1-test_size)*100)}%, test: {int(test_size*100)}%)...")
    train_ratings, test_ratings = train_test_split_ratings(
        ratings_filtered, test_size=test_size, random_state=random_state
    )
    print(f"  • Training ratings: {len(train_ratings):,}")
    print(f"  • Test ratings (withheld for evaluation): {len(test_ratings):,}")

    # Save partitioned splits for auditability and standalone testing
    os.makedirs(os.path.dirname(model_output_path) or ".", exist_ok=True)
    train_ratings.to_csv(os.path.join(data_dir, "train_ratings.csv"), index=False)
    test_ratings.to_csv(os.path.join(data_dir, "test_ratings.csv"), index=False)
    movies_filtered.to_csv(os.path.join(data_dir, "processed_movies.csv"), index=False)

    # 4. Train Model
    print("\n[Step 4/6] Building sparse matrix & computing similarities...")
    recommender = MovieRecommender(method="item_based")
    recommender.fit(
        train_ratings_df=train_ratings,
        movies_df=movies_filtered,
        compute_user_sim=True
    )
    print("  • Sparse User-Item Matrix shape:", recommender.sparse_matrix.shape)
    print("  • Item Cosine Similarity matrix shape:", recommender.item_similarity.shape)
    print("  • User Cosine Similarity matrix shape:", recommender.user_similarity.shape)
    print("  • Bayesian popularity ranking calculated.")

    # 5. Evaluate Model
    print("\n[Step 5/6] Evaluating models on held-out test data...")
    eval_results = run_full_evaluation(
        recommender=recommender,
        test_ratings_df=test_ratings,
        k=10,
        relevance_threshold=3.5,
        num_eval_users=80,
        max_rating_pairs=2000
    )

    print("\n📊 MODEL EVALUATION RESULTS:")
    eval_df = pd.DataFrame(eval_results).T
    print(eval_df.to_string())

    # 6. Save Model Artifact
    print(f"\n[Step 6/6] Serializing model artifact to: {model_output_path}...")
    recommender.save(model_output_path)
    file_size_mb = os.path.getsize(model_output_path) / (1024 * 1024)
    print(f"  • Model artifact successfully saved! ({file_size_mb:.2f} MB)")
    print("=" * 65)

    return {
        "raw_summary": raw_summary,
        "eval_results": eval_results,
        "model_output_path": model_output_path,
        "recommender": recommender,
        "test_ratings": test_ratings
    }


if __name__ == "__main__":
    train_and_save_pipeline()

