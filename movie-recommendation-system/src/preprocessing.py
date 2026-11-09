"""Data Preprocessing & Sparse Matrix Module for Recommender Systems.

This module cleans raw data, validates rating ranges, filters noise/sparsity,
performs train-test splitting to prevent data leakage, and constructs
efficient SciPy CSR sparse user-item interaction matrices.
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def clean_ratings(
    ratings_df: pd.DataFrame,
    min_rating: float = 0.5,
    max_rating: float = 5.0
) -> pd.DataFrame:
    """Cleans ratings dataframe by dropping nulls, duplicates, and invalid ranges.

    Args:
        ratings_df: Raw ratings DataFrame.
        min_rating: Minimum allowable rating score (MovieLens minimum is 0.5).
        max_rating: Maximum allowable rating score (MovieLens maximum is 5.0).

    Returns:
        Cleaned ratings DataFrame.
    """
    df = ratings_df.copy()

    # Drop null values across critical columns
    df = df.dropna(subset=["userId", "movieId", "rating"])

    # Remove duplicates if any (keep latest rating by timestamp if present)
    if "timestamp" in df.columns:
        df = df.sort_values(by="timestamp", ascending=True)
        df = df.drop_duplicates(subset=["userId", "movieId"], keep="last")
    else:
        df = df.drop_duplicates(subset=["userId", "movieId"], keep="first")

    # Ensure correct data types
    df["userId"] = df["userId"].astype(int)
    df["movieId"] = df["movieId"].astype(int)
    df["rating"] = df["rating"].astype(float)

    # Validate rating score boundary
    df = df[(df["rating"] >= min_rating) & (df["rating"] <= max_rating)]

    return df.reset_index(drop=True)


def clean_movies(movies_df: pd.DataFrame) -> pd.DataFrame:
    """Cleans movies dataframe and handles missing titles or genres.

    Args:
        movies_df: Raw movies DataFrame.

    Returns:
        Cleaned movies DataFrame.
    """
    df = movies_df.copy()

    # Drop null titles or movieIds
    df = df.dropna(subset=["movieId", "title"])
    df["movieId"] = df["movieId"].astype(int)
    df["title"] = df["title"].astype(str).str.strip()

    # Fill missing genres with '(no genres listed)'
    if "genres" in df.columns:
        df["genres"] = df["genres"].fillna("(no genres listed)").astype(str)

    # Remove duplicate movie entries by movieId
    df = df.drop_duplicates(subset=["movieId"], keep="first")

    return df.reset_index(drop=True)


def filter_insufficient_ratings(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    min_movie_ratings: int = 10,
    min_user_ratings: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filters out movies and users with too few ratings to eliminate noise.

    Sparse items with only 1 or 2 ratings introduce heavy noise into similarity
    calculations. Filtering ensures that every item and user has sufficient
    co-occurrence observations for collaborative filtering.

    Args:
        ratings_df: Cleaned ratings DataFrame.
        movies_df: Cleaned movies DataFrame.
        min_movie_ratings: Minimum ratings required for a movie to be retained.
        min_user_ratings: Minimum ratings required for a user to be retained.

    Returns:
        Tuple of (filtered_ratings_df, filtered_movies_df).
    """
    # Count ratings per movie
    movie_counts = ratings_df["movieId"].value_counts()
    valid_movies = movie_counts[movie_counts >= min_movie_ratings].index

    # Count ratings per user
    user_counts = ratings_df["userId"].value_counts()
    valid_users = user_counts[user_counts >= min_user_ratings].index

    # Filter ratings
    filtered_ratings = ratings_df[
        ratings_df["movieId"].isin(valid_movies) & ratings_df["userId"].isin(valid_users)
    ].copy()

    # Synchronize movies catalog
    filtered_movies = movies_df[movies_df["movieId"].isin(valid_movies)].copy()

    return filtered_ratings.reset_index(drop=True), filtered_movies.reset_index(drop=True)


def train_test_split_ratings(
    ratings_df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits ratings into train and test sets to prevent data leakage.

    CRITICAL RULE:
    Train and test ratings must be strictly partitioned. Test ratings are withheld
    and never used during similarity matrix construction or training.
    They serve solely as the ground-truth benchmark during model evaluation.

    Args:
        ratings_df: Filtered ratings DataFrame.
        test_size: Proportion of ratings allocated to evaluation (default: 0.20).
        random_state: Reproducible seed.

    Returns:
        Tuple of (train_ratings_df, test_ratings_df).
    """
    # Shuffle indices reproducibly
    rng = np.random.RandomState(random_state)
    shuffled_indices = rng.permutation(len(ratings_df))

    test_count = int(len(ratings_df) * test_size)
    test_idx = shuffled_indices[:test_count]
    train_idx = shuffled_indices[test_count:]

    train_df = ratings_df.iloc[train_idx].copy().reset_index(drop=True)
    test_df = ratings_df.iloc[test_idx].copy().reset_index(drop=True)

    return train_df, test_df


def build_user_item_matrix(
    ratings_df: pd.DataFrame,
    movies_df: Optional[pd.DataFrame] = None
) -> Tuple[csr_matrix, Dict[int, int], Dict[int, int], Dict[int, int], Dict[int, int], pd.DataFrame]:
    """Creates a user-item interaction matrix and converts it into a SciPy CSR sparse matrix.

    Why Sparse Matrices (CSR)?
    A dense user-item matrix of 600 users x 9,000 movies has 5.4 million cells. Over 98%
    of these cells are zeros (unrated movies). A dense float matrix wastes RAM and wastes
    thousands of CPU cycles computing 0 * 0 during vector multiplications.
    Compressed Sparse Row (CSR) storage only stores non-zero ratings and their index
    locations, slashing memory footprint by 95%+ and accelerating dot products.

    Args:
        ratings_df: Training ratings dataframe (userId, movieId, rating).
        movies_df: Optional movies dataframe to ensure all known movies are present as columns.

    Returns:
        Tuple containing:
        - sparse_matrix: SciPy csr_matrix of shape (num_users, num_movies).
        - user_to_idx: Map from actual userId to 0-based matrix row index.
        - idx_to_user: Map from matrix row index back to actual userId.
        - movie_to_idx: Map from actual movieId to 0-based matrix column index.
        - idx_to_movie: Map from matrix column index back to actual movieId.
        - user_item_df: Pandas DataFrame representation with user/movie IDs as index/columns.
    """
    # Unique users
    unique_users = sorted(ratings_df["userId"].unique())
    user_to_idx = {uid: idx for idx, uid in enumerate(unique_users)}
    idx_to_user = {idx: uid for uid, idx in user_to_idx.items()}

    # Unique movies (either from ratings or from reference movies_df)
    if movies_df is not None:
        unique_movies = sorted(movies_df["movieId"].unique())
    else:
        unique_movies = sorted(ratings_df["movieId"].unique())

    movie_to_idx = {mid: idx for idx, mid in enumerate(unique_movies)}
    idx_to_movie = {idx: mid for mid, idx in movie_to_idx.items()}

    # Filter ratings only to known items/users
    valid_ratings = ratings_df[
        ratings_df["userId"].isin(user_to_idx) & ratings_df["movieId"].isin(movie_to_idx)
    ]

    # Map IDs to consecutive integers
    row_indices = valid_ratings["userId"].map(user_to_idx).values
    col_indices = valid_ratings["movieId"].map(movie_to_idx).values
    data_values = valid_ratings["rating"].values

    num_users = len(unique_users)
    num_movies = len(unique_movies)

    # Construct SciPy CSR matrix: csr_matrix((data, (row_ind, col_ind)), shape=(N, M))
    sparse_matrix = csr_matrix(
        (data_values, (row_indices, col_indices)),
        shape=(num_users, num_movies),
        dtype=np.float32
    )

    # Create pivot DataFrame representation (useful for lookups and debugging)
    # Pivot maps missing ratings to 0.0
    user_item_df = valid_ratings.pivot(
        index="userId", columns="movieId", values="rating"
    ).fillna(0.0)

    # Reindex columns to include all unique movies if movies_df was supplied
    user_item_df = user_item_df.reindex(index=unique_users, columns=unique_movies, fill_value=0.0)

    return sparse_matrix, user_to_idx, idx_to_user, movie_to_idx, idx_to_movie, user_item_df

