"""Collaborative Filtering Recommender Engine.

This module implements Item-Based Collaborative Filtering, User-Based Collaborative
Filtering, and Popularity-based Cold-Start fallbacks with modular scoring and ranking.
"""

from typing import Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from src.preprocessing import build_user_item_matrix
from src.similarity import (
    compute_item_similarity,
    compute_user_similarity,
    get_top_similar_items,
    get_top_similar_users,
)


class MovieRecommender:
    """End-to-End Movie Recommender System.

    Supports:
    - Item-Based Collaborative Filtering (Item-Item Cosine Similarity)
    - User-Based Collaborative Filtering (User-User Cosine / Pearson Similarity)
    - Bayesian Weighted Rating Popularity Fallback for Cold-Start Users
    - Movie-to-Movie Similarity Lookup
    """

    def __init__(self, method: str = "item_based"):
        """Initializes the recommender.

        Args:
            method: Default recommendation strategy ('item_based' or 'user_based').
        """
        self.method = method

        # Datasets & Metadata
        self.movies_df: Optional[pd.DataFrame] = None
        self.train_ratings_df: Optional[pd.DataFrame] = None

        # Matrix and mappings
        self.sparse_matrix: Optional[csr_matrix] = None
        self.user_to_idx: Dict[int, int] = {}
        self.idx_to_user: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}

        # Similarity matrices
        self.item_similarity: Optional[np.ndarray] = None
        self.user_similarity: Optional[np.ndarray] = None

        # Precomputed user stats
        self.user_means: Dict[int, float] = {}
        self.user_watched: Dict[int, set] = {}

        # Cold-start popular movies ranking (computed strictly on training data)
        self.popular_movies_df: Optional[pd.DataFrame] = None

    def fit(
        self,
        train_ratings_df: pd.DataFrame,
        movies_df: pd.DataFrame,
        compute_user_sim: bool = True
    ) -> "MovieRecommender":
        """Fits the recommender on the training dataset.

        Args:
            train_ratings_df: Ratings used for training ONLY (no test leakage).
            movies_df: Movies metadata catalog.
            compute_user_sim: Whether to compute user similarity matrix as well.

        Returns:
            Self instance.
        """
        self.train_ratings_df = train_ratings_df.copy()
        self.movies_df = movies_df.copy()

        # Build sparse user-item interaction matrix
        (
            self.sparse_matrix,
            self.user_to_idx,
            self.idx_to_user,
            self.movie_to_idx,
            self.idx_to_movie,
            _
        ) = build_user_item_matrix(self.train_ratings_df, self.movies_df)

        # Cache watched movies set and mean rating per user
        self.user_watched = (
            self.train_ratings_df.groupby("userId")["movieId"].apply(set).to_dict()
        )
        self.user_means = (
            self.train_ratings_df.groupby("userId")["rating"].mean().to_dict()
        )

        # Compute Item-to-Item Cosine Similarity matrix
        self.item_similarity = compute_item_similarity(self.sparse_matrix)

        # Compute User-to-User Similarity matrix
        if compute_user_sim:
            self.user_similarity = compute_user_similarity(self.sparse_matrix, mean_center=False)

        # Compute Popularity Ranking strictly on training data for Cold Start
        self._compute_bayesian_popularity()

        return self

    def _compute_bayesian_popularity(self) -> None:
        """Computes IMDb-style Bayesian Weighted Rating strictly from training data.

        Formula:
            WR = (v / (v + m)) * R + (m / (v + m)) * C
            where:
                v = number of ratings for the movie in training data
                m = minimum ratings threshold (e.g. 75th percentile of rating counts)
                R = average rating of the movie
                C = mean rating across the entire training catalog
        """
        stats = self.train_ratings_df.groupby("movieId").agg(
            rating_count=("rating", "count"),
            rating_mean=("rating", "mean")
        ).reset_index()

        c_catalog_mean = self.train_ratings_df["rating"].mean()
        # Minimum ratings threshold (75th percentile of count or default 10)
        m_threshold = float(np.percentile(stats["rating_count"], 75))
        m_threshold = max(m_threshold, 10.0)

        def weighted_rating(row):
            v = row["rating_count"]
            r = row["rating_mean"]
            return (v / (v + m_threshold)) * r + (m_threshold / (v + m_threshold)) * c_catalog_mean

        stats["bayesian_score"] = stats.apply(weighted_rating, axis=1)

        # Merge with movies metadata
        merged = stats.merge(self.movies_df, on="movieId", how="inner")
        self.popular_movies_df = merged.sort_values(
            by=["bayesian_score", "rating_count"], ascending=[False, False]
        ).reset_index(drop=True)

    def recommend_popular(
        self,
        top_k: int = 10,
        exclude_movie_ids: Optional[set] = None
    ) -> List[Dict[str, Union[int, str, float]]]:
        """Returns top popular movies for cold-start users or fallback scenarios.

        Args:
            top_k: Number of recommendations to return.
            exclude_movie_ids: Optional set of movieIds to omit.

        Returns:
            List of movie recommendation records with title, genres, and popularity score.
        """
        if self.popular_movies_df is None:
            return []

        df = self.popular_movies_df
        if exclude_movie_ids:
            df = df[~df["movieId"].isin(exclude_movie_ids)]

        records = []
        for _, row in df.head(top_k).iterrows():
            records.append({
                "movieId": int(row["movieId"]),
                "title": str(row["title"]),
                "genres": str(row["genres"]),
                "predicted_score": round(float(row["bayesian_score"]), 2),
                "rating_count": int(row["rating_count"]),
                "method": "popular_fallback"
            })
        return records

    def predict_rating_item_based(self, user_id: int, movie_id: int) -> Optional[float]:
        """Predicts user's rating for a movie using Item-Based Collaborative Filtering.

        Formula:
            r_hat(u, i) = sum_{j in R(u)} (s_ij * r_uj) / sum_{j in R(u)} (|s_ij|)

        Args:
            user_id: Target userId.
            movie_id: Target movieId.

        Returns:
            Predicted rating in [0.5, 5.0], or user mean / None if no similarity overlap.
        """
        if movie_id not in self.movie_to_idx or user_id not in self.user_to_idx:
            return self.user_means.get(user_id, self.popular_movies_df["bayesian_score"].mean() if self.popular_movies_df is not None else 3.5)

        target_movie_idx = self.movie_to_idx[movie_id]
        user_idx = self.user_to_idx[user_id]

        # Extract ratings by this user from sparse matrix
        user_row = self.sparse_matrix[user_idx]
        rated_movie_indices = user_row.indices
        user_ratings = user_row.data

        if len(rated_movie_indices) == 0:
            return self.user_means.get(user_id, 3.5)

        # Similarities between target movie and all movies rated by this user
        similarities = self.item_similarity[target_movie_idx, rated_movie_indices]

        # Filter to positive similarities
        pos_mask = similarities > 0.0
        if not np.any(pos_mask):
            return self.user_means.get(user_id, 3.5)

        valid_sims = similarities[pos_mask]
        valid_ratings = user_ratings[pos_mask]

        sim_sum = np.sum(valid_sims)
        if sim_sum == 0.0:
            return self.user_means.get(user_id, 3.5)

        pred = np.sum(valid_sims * valid_ratings) / sim_sum
        return float(np.clip(pred, 0.5, 5.0))

    def predict_rating_user_based(
        self,
        user_id: int,
        movie_id: int,
        k_neighbors: int = 20
    ) -> Optional[float]:
        """Predicts user's rating for a movie using User-Based Collaborative Filtering.

        Formula:
            r_hat(u, i) = r_bar_u + sum_{v in N_i(u)} s_uv * (r_vi - r_bar_v) / sum_{v in N_i(u)} |s_uv|

        Args:
            user_id: Target userId.
            movie_id: Target movieId.
            k_neighbors: Number of nearest neighbor users to consider.

        Returns:
            Predicted rating in [0.5, 5.0].
        """
        if self.user_similarity is None:
            raise ValueError("User similarity matrix not computed.")

        if user_id not in self.user_to_idx or movie_id not in self.movie_to_idx:
            return self.user_means.get(user_id, 3.5)

        target_user_idx = self.user_to_idx[user_id]
        movie_idx = self.movie_to_idx[movie_id]

        # Users who rated movie_id
        col = self.sparse_matrix[:, movie_idx]
        user_indices = col.indices
        ratings = col.data

        # Exclude target user themselves
        other_mask = user_indices != target_user_idx
        user_indices = user_indices[other_mask]
        ratings = ratings[other_mask]

        if len(user_indices) == 0:
            return self.user_means.get(user_id, 3.5)

        # Get similarities with target user
        sims = self.user_similarity[target_user_idx, user_indices]
        pos_mask = sims > 0.0

        if not np.any(pos_mask):
            return self.user_means.get(user_id, 3.5)

        sims = sims[pos_mask]
        ratings = ratings[pos_mask]
        user_indices = user_indices[pos_mask]

        # Top k neighbors
        if len(sims) > k_neighbors:
            top_k_idx = np.argsort(sims)[::-1][:k_neighbors]
            sims = sims[top_k_idx]
            ratings = ratings[top_k_idx]
            user_indices = user_indices[top_k_idx]

        sim_sum = np.sum(np.abs(sims))
        if sim_sum == 0.0:
            return self.user_means.get(user_id, 3.5)

        target_mean = self.user_means.get(user_id, 3.5)
        # Neighbor means
        neighbor_means = np.array([self.user_means.get(self.idx_to_user[u], 3.5) for u in user_indices])
        normalized_ratings = ratings - neighbor_means

        pred = target_mean + (np.sum(sims * normalized_ratings) / sim_sum)
        return float(np.clip(pred, 0.5, 5.0))

    def recommend_item_based(
        self,
        user_id: int,
        top_k: int = 10,
        min_user_ratings: int = 3
    ) -> List[Dict[str, Union[int, str, float]]]:
        """Generates personalized recommendations using Item-Based Collaborative Filtering.

        1. Checks if user is known and has at least min_user_ratings.
           If cold start, falls back to Bayesian popular movies.
        2. Retrieves user's rated movies and their ratings.
        3. For all unrated movies, calculates weighted score:
           score(i) = sum_{j in Watched(u)} (Similarity(i, j) * Rating(u, j)) / sum Similarity(i, j)
        4. Excludes already-watched movies.
        5. Ranks unrated movies descending and returns top-K.

        Args:
            user_id: Target userId.
            top_k: Number of recommendations.
            min_user_ratings: Minimum ratings required before falling back to cold-start.

        Returns:
            List of recommended movie dictionaries.
        """
        # Cold start check: user unknown or insufficient ratings
        watched_set = self.user_watched.get(user_id, set())
        if len(watched_set) < min_user_ratings or user_id not in self.user_to_idx:
            return self.recommend_popular(top_k=top_k, exclude_movie_ids=watched_set)

        user_idx = self.user_to_idx[user_id]
        user_row = self.sparse_matrix[user_idx]
        user_rated_indices = user_row.indices
        user_ratings = user_row.data  # shape: (n_rated,)

        # Item similarity slice between all items and rated items: shape (M, n_rated)
        sim_slice = self.item_similarity[:, user_rated_indices]  # (num_movies, n_rated)

        # Weighted sum: (num_movies, n_rated) dot (n_rated,) -> (num_movies,)
        numerator = sim_slice.dot(user_ratings)
        denominator = np.sum(sim_slice, axis=1)

        # Predicted ratings across all items
        with np.errstate(divide="ignore", invalid="ignore"):
            predicted_scores = np.where(denominator > 0.0, numerator / denominator, 0.0)

        # Mask already watched movies so they are NEVER recommended
        predicted_scores[user_rated_indices] = -1.0

        # Rank descending
        candidate_indices = np.argsort(predicted_scores)[::-1]

        movie_title_map = dict(zip(self.movies_df["movieId"], self.movies_df["title"]))
        movie_genre_map = dict(zip(self.movies_df["movieId"], self.movies_df["genres"]))

        recommendations = []
        for idx in candidate_indices:
            if len(recommendations) >= top_k:
                break
            score = float(predicted_scores[idx])
            if score <= 0.0:
                break

            m_id = self.idx_to_movie[idx]
            recommendations.append({
                "movieId": m_id,
                "title": movie_title_map.get(m_id, f"Movie {m_id}"),
                "genres": movie_genre_map.get(m_id, "Unknown"),
                "predicted_score": round(score, 2),
                "method": "item_based_cf"
            })

        # If sparse overlap produced fewer than top_k, fill remainder with popular fallback
        if len(recommendations) < top_k:
            existing_ids = watched_set.union({r["movieId"] for r in recommendations})
            remaining = self.recommend_popular(
                top_k=top_k - len(recommendations),
                exclude_movie_ids=existing_ids
            )
            recommendations.extend(remaining)

        return recommendations

    def recommend_user_based(
        self,
        user_id: int,
        top_k: int = 10,
        k_neighbors: int = 20,
        min_user_ratings: int = 3
    ) -> List[Dict[str, Union[int, str, float]]]:
        """Generates personalized recommendations using User-Based Collaborative Filtering.

        1. Finds k nearest neighbor users based on user similarity.
        2. Aggregates unrated movies liked by these neighbor users.
        3. Excludes already-watched movies.
        4. Ranks recommendations descending and returns top-K.

        Args:
            user_id: Target userId.
            top_k: Number of recommendations.
            k_neighbors: Number of similar peers to examine.
            min_user_ratings: Minimum ratings threshold before cold-start fallback.

        Returns:
            List of recommended movie dictionaries.
        """
        watched_set = self.user_watched.get(user_id, set())
        if len(watched_set) < min_user_ratings or user_id not in self.user_to_idx or self.user_similarity is None:
            return self.recommend_popular(top_k=top_k, exclude_movie_ids=watched_set)

        target_user_idx = self.user_to_idx[user_id]
        user_sims = self.user_similarity[target_user_idx].copy()
        user_sims[target_user_idx] = -1.0  # Exclude self

        # Top-K neighbor indices
        neighbor_indices = np.argsort(user_sims)[::-1][:k_neighbors]
        neighbor_sims = user_sims[neighbor_indices]

        # Only retain positive similarities
        pos_mask = neighbor_sims > 0.0
        if not np.any(pos_mask):
            return self.recommend_popular(top_k=top_k, exclude_movie_ids=watched_set)

        neighbor_indices = neighbor_indices[pos_mask]
        neighbor_sims = neighbor_sims[pos_mask]

        # Matrix slice of neighbor ratings: shape (k_valid_neighbors, num_movies)
        neighbor_matrix = self.sparse_matrix[neighbor_indices].toarray()

        # Weighted score per movie
        # Only consider movies rated by at least one neighbor
        sim_weights = neighbor_sims[:, np.newaxis]  # shape (k, 1)
        weighted_ratings = neighbor_matrix * sim_weights  # shape (k, num_movies)

        # Denominator: sum of similarities for neighbors who actually rated each movie
        rated_mask = neighbor_matrix > 0
        denominators = np.sum(sim_weights * rated_mask, axis=0)
        numerators = np.sum(weighted_ratings, axis=0)

        with np.errstate(divide="ignore", invalid="ignore"):
            predicted_scores = np.where(denominators > 0.0, numerators / denominators, 0.0)

        # Mask watched movies
        for m_id in watched_set:
            if m_id in self.movie_to_idx:
                predicted_scores[self.movie_to_idx[m_id]] = -1.0

        candidate_indices = np.argsort(predicted_scores)[::-1]

        movie_title_map = dict(zip(self.movies_df["movieId"], self.movies_df["title"]))
        movie_genre_map = dict(zip(self.movies_df["movieId"], self.movies_df["genres"]))

        recommendations = []
        for idx in candidate_indices:
            if len(recommendations) >= top_k:
                break
            score = float(predicted_scores[idx])
            if score <= 0.0:
                break

            m_id = self.idx_to_movie[idx]
            recommendations.append({
                "movieId": m_id,
                "title": movie_title_map.get(m_id, f"Movie {m_id}"),
                "genres": movie_genre_map.get(m_id, "Unknown"),
                "predicted_score": round(score, 2),
                "method": "user_based_cf"
            })

        if len(recommendations) < top_k:
            existing_ids = watched_set.union({r["movieId"] for r in recommendations})
            remaining = self.recommend_popular(
                top_k=top_k - len(recommendations),
                exclude_movie_ids=existing_ids
            )
            recommendations.extend(remaining)

        return recommendations

    def recommend(
        self,
        user_id: int,
        method: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Union[int, str, float]]]:
        """Unified recommendation interface.

        Dispatches to 'item_based' or 'user_based', automatically handling
        cold start users.

        Args:
            user_id: Target userId.
            method: Strategy ('item_based' or 'user_based'). Defaults to self.method.
            top_k: Number of recommendations.

        Returns:
            List of recommended movies.
        """
        chosen_method = method or self.method
        if chosen_method == "user_based":
            return self.recommend_user_based(user_id=user_id, top_k=top_k)
        return self.recommend_item_based(user_id=user_id, top_k=top_k)

    def recommend_similar_movies(
        self,
        movie_id: int,
        top_k: int = 10
    ) -> List[Dict[str, Union[int, str, float]]]:
        """Finds movies most similar to a given target movie.

        Args:
            movie_id: Target movieId.
            top_k: Number of similar movies.

        Returns:
            List of similar movies with title, genres, and cosine similarity score.
        """
        if self.item_similarity is None:
            raise ValueError("Model is not fitted yet.")

        top_pairs = get_top_similar_items(
            movie_id=movie_id,
            item_similarity=self.item_similarity,
            movie_to_idx=self.movie_to_idx,
            idx_to_movie=self.idx_to_movie,
            top_k=top_k
        )

        movie_title_map = dict(zip(self.movies_df["movieId"], self.movies_df["title"]))
        movie_genre_map = dict(zip(self.movies_df["movieId"], self.movies_df["genres"]))

        results = []
        for m_id, sim in top_pairs:
            results.append({
                "movieId": m_id,
                "title": movie_title_map.get(m_id, f"Movie {m_id}"),
                "genres": movie_genre_map.get(m_id, "Unknown"),
                "similarity_score": round(sim, 4)
            })
        return results

    def search_movies(self, query: str, top_k: int = 10) -> List[Dict[str, Union[int, str]]]:
        """Searches movies catalog by title substring (case-insensitive).

        Args:
            query: Substring to search.
            top_k: Maximum matches to return.

        Returns:
            List of matching movie dictionaries.
        """
        if self.movies_df is None:
            return []

        q = query.strip().lower()
        matches = self.movies_df[self.movies_df["title"].str.lower().str.contains(q, na=False, regex=False)]
        records = []
        for _, row in matches.head(top_k).iterrows():
            records.append({
                "movieId": int(row["movieId"]),
                "title": str(row["title"]),
                "genres": str(row["genres"])
            })
        return records

    def save(self, filepath: str) -> None:
        """Saves model state and similarity artifacts to disk for fast serving.

        Args:
            filepath: Destination file path (e.g. 'models/recommender_model.joblib').
        """
        payload = {
            "method": self.method,
            "movies_df": self.movies_df,
            "user_to_idx": self.user_to_idx,
            "idx_to_user": self.idx_to_user,
            "movie_to_idx": self.movie_to_idx,
            "idx_to_movie": self.idx_to_movie,
            "sparse_matrix": self.sparse_matrix,
            "item_similarity": self.item_similarity,
            "user_similarity": self.user_similarity,
            "user_means": self.user_means,
            "user_watched": self.user_watched,
            "popular_movies_df": self.popular_movies_df,
        }
        joblib.dump(payload, filepath, compress=3)

    @classmethod
    def load(cls, filepath: str) -> "MovieRecommender":
        """Loads a pre-trained model artifact from disk without retraining.

        Args:
            filepath: Path to saved model file.

        Returns:
            Loaded MovieRecommender instance ready for inference.
        """
        payload = joblib.load(filepath)
        instance = cls(method=payload.get("method", "item_based"))
        instance.movies_df = payload["movies_df"]
        instance.user_to_idx = payload["user_to_idx"]
        instance.idx_to_user = payload["idx_to_user"]
        instance.movie_to_idx = payload["movie_to_idx"]
        instance.idx_to_movie = payload["idx_to_movie"]
        instance.sparse_matrix = payload["sparse_matrix"]
        instance.item_similarity = payload["item_similarity"]
        instance.user_similarity = payload.get("user_similarity")
        instance.user_means = payload["user_means"]
        instance.user_watched = payload["user_watched"]
        instance.popular_movies_df = payload["popular_movies_df"]
        return instance

