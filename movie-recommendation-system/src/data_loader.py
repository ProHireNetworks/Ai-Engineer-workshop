"""Data Loader Module for MovieLens Dataset.

This module provides functions to load MovieLens CSV files into Pandas DataFrames,
validate file presence, and compute high-level exploratory statistics.
"""

import os
from typing import Dict, Tuple, Optional
import pandas as pd


def load_dataset(data_dir: str = "dataset") -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Loads MovieLens dataset files from the specified directory.

    Args:
        data_dir: Relative or absolute path to the folder containing CSV files.

    Returns:
        Tuple containing (movies_df, ratings_df, tags_df, links_df).
        tags_df and links_df are None if files are missing.

    Raises:
        FileNotFoundError: If movies.csv or ratings.csv is missing.
    """
    movies_path = os.path.join(data_dir, "movies.csv")
    ratings_path = os.path.join(data_dir, "ratings.csv")
    tags_path = os.path.join(data_dir, "tags.csv")
    links_path = os.path.join(data_dir, "links.csv")

    if not os.path.exists(movies_path):
        raise FileNotFoundError(f"movies.csv not found at: {movies_path}")
    if not os.path.exists(ratings_path):
        raise FileNotFoundError(f"ratings.csv not found at: {ratings_path}")

    # Load required datasets
    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    # Load optional auxiliary datasets
    tags_df = pd.read_csv(tags_path) if os.path.exists(tags_path) else None
    links_df = pd.read_csv(links_path) if os.path.exists(links_path) else None

    return movies_df, ratings_df, tags_df, links_df


def get_dataset_summary(movies_df: pd.DataFrame, ratings_df: pd.DataFrame) -> Dict[str, float]:
    """Calculates summary statistics of the dataset including catalog sparsity.

    Sparsity represents the percentage of unobserved ratings in the user-item matrix:
        Sparsity (%) = (1 - (Total Ratings / (Unique Users * Unique Movies))) * 100

    Args:
        movies_df: DataFrame containing movie records (movieId, title, genres).
        ratings_df: DataFrame containing user ratings (userId, movieId, rating, timestamp).

    Returns:
        Dictionary containing key metrics.
    """
    num_ratings = len(ratings_df)
    num_users = ratings_df["userId"].nunique()
    num_movies = movies_df["movieId"].nunique()
    num_rated_movies = ratings_df["movieId"].nunique()

    # Theoretical maximum entries in a complete User x Movie matrix
    total_possible_ratings = num_users * num_rated_movies
    sparsity = (1.0 - (num_ratings / total_possible_ratings)) * 100.0 if total_possible_ratings > 0 else 0.0

    summary = {
        "total_movies": float(num_movies),
        "total_rated_movies": float(num_rated_movies),
        "total_users": float(num_users),
        "total_ratings": float(num_ratings),
        "min_rating": float(ratings_df["rating"].min()),
        "max_rating": float(ratings_df["rating"].max()),
        "mean_rating": float(ratings_df["rating"].mean()),
        "median_rating": float(ratings_df["rating"].median()),
        "matrix_sparsity_pct": round(sparsity, 2),
    }
    return summary

