"""Similarity Module for Collaborative Filtering.

This module computes item-to-item and user-to-user cosine similarities using
SciPy sparse matrix operations and Scikit-learn pairwise metrics.
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def compute_item_similarity(user_item_matrix: csr_matrix) -> np.ndarray:
    """Computes pairwise cosine similarity between all items (movies).

    Mathematical Formula:
        cos(i, j) = (r_i . r_j) / (||r_i||_2 * ||r_j||_2)
        where r_i and r_j are the rating column vectors of item i and item j across all users.

    In SciPy CSR representation, items are columns. Transposing user_item_matrix (shape N x M)
    yields shape M x N, where each row is an item vector.

    Args:
        user_item_matrix: SciPy csr_matrix of shape (num_users, num_items).

    Returns:
        Dense NumPy float32 array of shape (num_items, num_items) with values in [0.0, 1.0].
    """
    # Transpose so rows are items (movies)
    item_user_matrix = user_item_matrix.T.tocsr()

    # Compute cosine similarity using optimized BLAS routines
    similarity = cosine_similarity(item_user_matrix, dense_output=True).astype(np.float32)

    # Ensure diagonal values are strictly 1.0 and numerical rounding artifacts are bounded [0, 1]
    np.fill_diagonal(similarity, 1.0)
    similarity = np.clip(similarity, 0.0, 1.0)

    return similarity


def compute_user_similarity(
    user_item_matrix: csr_matrix,
    mean_center: bool = False
) -> np.ndarray:
    """Computes pairwise similarity between all users.

    Mathematical Concept:
        When mean_center is False: standard Cosine Similarity.
        When mean_center is True: Pearson Correlation Coefficient.
        Subtracting each user's mean rating accounts for user rating bias
        (e.g., tough critics who give 3s vs generous users who give 5s).

    Args:
        user_item_matrix: SciPy csr_matrix of shape (num_users, num_items).
        mean_center: Whether to subtract each user's mean non-zero rating.

    Returns:
        Dense NumPy float32 array of shape (num_users, num_users).
    """
    if not mean_center:
        similarity = cosine_similarity(user_item_matrix, dense_output=True).astype(np.float32)
    else:
        # Mean center non-zero ratings per user
        dense_matrix = user_item_matrix.toarray().astype(np.float32)
        mask = dense_matrix > 0

        # Calculate mean for each user only across observed ratings
        user_sums = np.sum(dense_matrix, axis=1)
        user_counts = np.sum(mask, axis=1)
        # Avoid division by zero for users with no ratings
        user_means = np.divide(user_sums, user_counts, out=np.zeros_like(user_sums), where=user_counts > 0)

        # Subtract user mean from rated items
        centered = np.zeros_like(dense_matrix)
        for i in range(len(dense_matrix)):
            if user_counts[i] > 0:
                centered[i, mask[i]] = dense_matrix[i, mask[i]] - user_means[i]

        similarity = cosine_similarity(centered, dense_output=True).astype(np.float32)

    np.fill_diagonal(similarity, 1.0)
    return similarity


def get_top_similar_items(
    movie_id: int,
    item_similarity: np.ndarray,
    movie_to_idx: Dict[int, int],
    idx_to_movie: Dict[int, int],
    top_k: int = 10
) -> List[Tuple[int, float]]:
    """Retrieves top-K most similar movies for a given target movie.

    Args:
        movie_id: Target movieId.
        item_similarity: Item similarity square matrix.
        movie_to_idx: Mapping from movieId to matrix column index.
        idx_to_movie: Mapping from index back to movieId.
        top_k: Number of most similar items to return.

    Returns:
        List of tuples: [(similar_movie_id, similarity_score), ...]
    """
    if movie_id not in movie_to_idx:
        return []

    target_idx = movie_to_idx[movie_id]
    scores = item_similarity[target_idx].copy()

    # Exclude the target item itself by masking its self-similarity
    scores[target_idx] = -1.0

    # Get indices of highest scores
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score > 0.0:  # Only return items with positive similarity
            results.append((idx_to_movie[idx], round(score, 4)))

    return results


def get_top_similar_users(
    user_id: int,
    user_similarity: np.ndarray,
    user_to_idx: Dict[int, int],
    idx_to_user: Dict[int, int],
    top_k: int = 10
) -> List[Tuple[int, float]]:
    """Retrieves top-K nearest neighbor users for a given target user.

    Args:
        user_id: Target userId.
        user_similarity: User similarity square matrix.
        user_to_idx: Mapping from userId to matrix row index.
        idx_to_user: Mapping from index back to userId.
        top_k: Number of nearest neighbor users to return.

    Returns:
        List of tuples: [(neighbor_user_id, similarity_score), ...]
    """
    if user_id not in user_to_idx:
        return []

    target_idx = user_to_idx[user_id]
    scores = user_similarity[target_idx].copy()

    # Exclude target user themselves
    scores[target_idx] = -1.0

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score > 0.0:
            results.append((idx_to_user[idx], round(score, 4)))

    return results

