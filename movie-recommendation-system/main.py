"""End-to-End Movie Recommendation System Runner.

Executes the complete pipeline:
1. Loads MovieLens dataset.
2. Preprocesses data and creates train/test partitions.
3. Fits Item-Based and User-Based Collaborative Filtering models.
4. Evaluates performance (RMSE, MAE, Precision@K, Recall@K, Catalog Coverage).
5. Generates all 7 visualization charts.
6. Demonstrates live recommendations for existing users, movie similarities, and cold-start users.
"""

import os
import sys
import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import clean_movies, clean_ratings, filter_insufficient_ratings
from src.recommender import MovieRecommender
from src.model_training import train_and_save_pipeline
from src.visualizations import generate_all_visualizations


def print_recommendation_table(title: str, recs: list):
    """Formats and prints recommendations nicely in console."""
    print(f"\n{'-'*65}")
    print(f"🎬 {title.upper()}")
    print(f"{'-'*65}")
    if not recs:
        print("  (No recommendations generated)")
        return

    df = pd.DataFrame(recs)
    cols_to_show = [c for c in ["movieId", "title", "genres", "predicted_score", "similarity_score", "method"] if c in df.columns]
    print(df[cols_to_show].to_string(index=False))


def main():
    print("=" * 65)
    print("🚀 MOVIE RECOMMENDATION SYSTEM - COMPLETE END-TO-END PIPELINE")
    print("=" * 65)

    # 1. Train and save model & evaluate
    pipeline_output = train_and_save_pipeline(
        data_dir="dataset",
        model_output_path="models/recommender_model.joblib",
        min_movie_ratings=10,
        min_user_ratings=5,
        test_size=0.20,
        random_state=42
    )

    recommender = pipeline_output["recommender"]
    eval_results = pipeline_output["eval_results"]

    # 2. Generate all visualizations
    movies_raw, ratings_raw, _, _ = load_dataset("dataset")
    generate_all_visualizations(
        ratings_df=ratings_raw,
        movies_df=movies_raw,
        recommender=recommender,
        eval_results=eval_results,
        output_dir="visualizations"
    )

    # 3. Model Serving Demonstration (Load from disk to verify independence)
    print("\n" + "=" * 65)
    print("🧪 MODEL SERVING & INFERENCE DEMONSTRATION")
    print("=" * 65)
    print("Loading serialized model artifact from 'models/recommender_model.joblib'...")
    serving_model = MovieRecommender.load("models/recommender_model.joblib")
    print("✓ Model successfully loaded into memory without retraining!")

    # Demo 1: Movie-to-Movie Similarity (Item-Based CF)
    sample_movie = "Toy Story (1995)"
    matches = serving_model.search_movies("Toy Story", top_k=1)
    if matches:
        target_mid = matches[0]["movieId"]
        similar_movies = serving_model.recommend_similar_movies(movie_id=target_mid, top_k=5)
        print_recommendation_table(f"Movies Similar to '{matches[0]['title']}' (Item-Item Cosine Similarity)", similar_movies)

    # Demo 2: Personalized User Recommendations (Item-Based CF)
    target_user_id = 1
    item_recs = serving_model.recommend(user_id=target_user_id, method="item_based", top_k=5)
    print_recommendation_table(f"Personalized Recommendations for User {target_user_id} (Item-Based CF)", item_recs)

    # Demo 3: Personalized User Recommendations (User-Based CF)
    user_recs = serving_model.recommend(user_id=target_user_id, method="user_based", top_k=5)
    print_recommendation_table(f"Personalized Recommendations for User {target_user_id} (User-Based CF)", user_recs)

    # Demo 4: Cold-Start Handling (Brand New User with ID 99999 and zero ratings)
    cold_start_user_id = 99999
    cold_recs = serving_model.recommend(user_id=cold_start_user_id, top_k=5)
    print_recommendation_table(f"Cold-Start Recommendations for New User {cold_start_user_id} (Bayesian Popularity Fallback)", cold_recs)

    print("\n" + "=" * 65)
    print("✅ ALL PIPELINE MODULES COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()

