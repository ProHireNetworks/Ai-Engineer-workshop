"""Visualization Module for Movie Recommendation System.

Generates and saves publication-quality charts using Matplotlib and Seaborn:
1. Rating distribution
2. Most-rated movies
3. Highest-rated movies (min 50 ratings)
4. User activity distribution
5. Movie popularity long-tail
6. Cosine similarity heatmap between popular movies
7. Model evaluation comparison (Item-Based vs User-Based)
"""

import os
import tempfile

# Ensure Matplotlib config directory is writable in all environments
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def set_plotting_style():
    """Sets a clean, modern aesthetic style for Seaborn & Matplotlib."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update({
        "figure.autolayout": True,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.labelweight": "semibold",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.titlesize": 16,
    })


def plot_rating_distribution(ratings_df: pd.DataFrame, output_dir: str = "visualizations") -> str:
    """Plots and saves the frequency distribution of ratings (0.5 to 5.0)."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "01_rating_distribution.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    rating_counts = ratings_df["rating"].value_counts().sort_index()

    palette = sns.color_palette("Blues_d", len(rating_counts))
    bars = ax.bar(rating_counts.index.astype(str), rating_counts.values, color=palette, edgecolor="black", linewidth=0.8)

    # Annotate percentage on top of each bar
    total_ratings = len(ratings_df)
    for bar in bars:
        height = bar.get_height()
        pct = (height / total_ratings) * 100
        ax.annotate(f"{pct:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_title("MovieLens Rating Distribution (100,836 Ratings)")
    ax.set_xlabel("Rating Score (Stars)")
    ax.set_ylabel("Total Number of Ratings")

    mean_rating = ratings_df["rating"].mean()
    median_rating = ratings_df["rating"].median()
    ax.text(0.03, 0.88, f"Mean Rating: {mean_rating:.2f} / 5.0\nMedian Rating: {median_rating:.1f} / 5.0",
            transform=ax.transAxes, fontsize=11, bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9))

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_most_rated_movies(ratings_df: pd.DataFrame, movies_df: pd.DataFrame, top_n: int = 15, output_dir: str = "visualizations") -> str:
    """Plots top N most-rated movies in the dataset."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "02_most_rated_movies.png")

    counts = ratings_df["movieId"].value_counts().head(top_n).reset_index()
    counts.columns = ["movieId", "rating_count"]
    merged = counts.merge(movies_df, on="movieId", how="left")

    # Shorten titles for cleaner axis display
    merged["short_title"] = merged["title"].apply(lambda t: t[:32] + "..." if len(t) > 35 else t)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=merged, y="short_title", x="rating_count", palette="viridis", ax=ax, edgecolor="black", linewidth=0.8)

    ax.set_title(f"Top {top_n} Most-Rated Movies in MovieLens")
    ax.set_xlabel("Number of Ratings")
    ax.set_ylabel("Movie Title")

    for p in ax.patches:
        width = p.get_width()
        ax.annotate(f"{int(width):,}",
                    xy=(width, p.get_y() + p.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_highest_rated_movies(ratings_df: pd.DataFrame, movies_df: pd.DataFrame, min_ratings: int = 50, top_n: int = 15, output_dir: str = "visualizations") -> str:
    """Plots top N highest-rated movies with at least min_ratings votes."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "03_highest_rated_movies.png")

    stats = ratings_df.groupby("movieId").agg(
        mean_rating=("rating", "mean"),
        count=("rating", "count")
    ).reset_index()

    qualified = stats[stats["count"] >= min_ratings].sort_values(by="mean_rating", ascending=False).head(top_n)
    merged = qualified.merge(movies_df, on="movieId", how="left")
    merged["short_title"] = merged["title"].apply(lambda t: t[:32] + "..." if len(t) > 35 else t)

    fig, ax = plt.subplots(figsize=(10, 6))
    palette = sns.color_palette("flare", top_n)
    bars = ax.barh(merged["short_title"][::-1], merged["mean_rating"][::-1], color=palette, edgecolor="black", linewidth=0.8)

    ax.set_xlim(3.5, 5.0)
    ax.set_title(f"Top {top_n} Highest-Rated Movies (Minimum {min_ratings} Ratings)")
    ax.set_xlabel("Mean Rating Score (Stars)")
    ax.set_ylabel("Movie Title")

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.2f}",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_user_activity(ratings_df: pd.DataFrame, output_dir: str = "visualizations") -> str:
    """Plots user activity distribution showing the power-law tail."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "04_user_activity.png")

    user_counts = ratings_df["userId"].value_counts()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Boxplot
    sns.boxplot(y=user_counts, ax=ax1, color="#4C72B0")
    ax1.set_title("User Ratings Count (Outlier Spread)")
    ax1.set_ylabel("Number of Ratings Contributed per User")

    # Histogram with KDE
    sns.histplot(user_counts, bins=40, kde=True, ax=ax2, color="#55A868", edgecolor="black")
    ax2.set_title("User Activity Distribution (Log-Scale X-axis)")
    ax2.set_xscale("log")
    ax2.set_xlabel("Number of Ratings per User (Log Scale)")
    ax2.set_ylabel("User Frequency")

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_movie_popularity_long_tail(ratings_df: pd.DataFrame, output_dir: str = "visualizations") -> str:
    """Plots the classic recommender long-tail curve of movie popularity."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "05_movie_popularity.png")

    movie_counts = ratings_df["movieId"].value_counts().values

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(range(len(movie_counts)), movie_counts, color="#C44E52", linewidth=2.5)
    ax.fill_between(range(len(movie_counts)), movie_counts, color="#C44E52", alpha=0.3)

    # Highlight popular vs long-tail boundary (top 20% items)
    cutoff_20 = int(len(movie_counts) * 0.2)
    ax.axvline(x=cutoff_20, color="black", linestyle="--", alpha=0.7, label=f"Top 20% Movies Cutoff ({cutoff_20} items)")

    ax.set_title("The Long-Tail Distribution of Movie Popularity")
    ax.set_xlabel("Movies Ranked by Rating Count (Most to Least Popular)")
    ax.set_ylabel("Number of Ratings Received")
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_similarity_heatmap(recommender, output_dir: str = "visualizations") -> str:
    """Plots a cosine similarity heatmap between iconic representative movies."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "06_similarity_scores.png")

    # Pick popular iconic movies across different genres
    target_titles = [
        "Toy Story (1995)",
        "Lion King, The (1994)",
        "Aladdin (1992)",
        "Jurassic Park (1993)",
        "Terminator 2: Judgment Day (1991)",
        "Matrix, The (1999)",
        "Star Wars: Episode IV - A New Hope (1977)",
        "Pulp Fiction (1994)",
        "Fight Club (1999)",
        "Shawshank Redemption, The (1994)",
        "Forrest Gump (1994)",
        "Silence of the Lambs, The (1991)"
    ]

    selected_movies = []
    selected_indices = []

    for title in target_titles:
        m = recommender.movies_df[recommender.movies_df["title"] == title]
        if not m.empty:
            m_id = m.iloc[0]["movieId"]
            if m_id in recommender.movie_to_idx:
                idx = recommender.movie_to_idx[m_id]
                # Shorten title
                short = title.split("(")[0].strip()
                selected_movies.append(short)
                selected_indices.append(idx)

    if len(selected_indices) < 4:
        # Fallback to top 10 movies in catalog
        top_ids = list(recommender.movie_to_idx.keys())[:10]
        selected_indices = [recommender.movie_to_idx[mid] for mid in top_ids]
        selected_movies = [f"Movie {mid}" for mid in top_ids]

    sim_submatrix = recommender.item_similarity[np.ix_(selected_indices, selected_indices)]

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        sim_submatrix,
        xticklabels=selected_movies,
        yticklabels=selected_movies,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        cbar_kws={"label": "Cosine Similarity"},
        ax=ax,
        linewidths=0.5,
        linecolor="gray"
    )
    ax.set_title("Item-to-Item Cosine Similarity Heatmap (Iconic Movies)")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def plot_model_evaluation_comparison(eval_results: dict, output_dir: str = "visualizations") -> str:
    """Plots comparative evaluation metrics between Item-Based and User-Based CF."""
    set_plotting_style()
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "07_model_evaluation_comparison.png")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    models = ["Item-Based CF", "User-Based CF"]
    rmse_vals = [eval_results["item_based"]["RMSE"], eval_results["user_based"]["RMSE"]]
    mae_vals = [eval_results["item_based"]["MAE"], eval_results["user_based"]["MAE"]]

    x = np.arange(len(models))
    width = 0.35

    # Subplot 1: Rating Error (RMSE & MAE) - Lower is better
    b1 = ax1.bar(x - width/2, rmse_vals, width, label="RMSE", color="#4C72B0", edgecolor="black")
    b2 = ax1.bar(x + width/2, mae_vals, width, label="MAE", color="#55A868", edgecolor="black")

    ax1.set_title("Rating Error (Lower is Better)")
    ax1.set_ylabel("Error (Stars)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.legend(loc="upper left")
    ax1.set_ylim(0, max(rmse_vals) * 1.25)

    for b in list(b1) + list(b2):
        h = b.get_height()
        ax1.annotate(f"{h:.3f}", xy=(b.get_x() + b.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Subplot 2: Ranking & Coverage
    p10_vals = [eval_results["item_based"]["Precision@10"] * 100, eval_results["user_based"]["Precision@10"] * 100]
    cov_vals = [eval_results["item_based"]["Coverage@10 (%)"], eval_results["user_based"]["Coverage@10 (%)"]]

    b3 = ax2.bar(x - width/2, p10_vals, width, label="Precision@10 (%)", color="#C44E52", edgecolor="black")
    b4 = ax2.bar(x + width/2, cov_vals, width, label="Catalog Coverage (%)", color="#8172B2", edgecolor="black")

    ax2.set_title("Ranking & Catalog Coverage (Higher is Better)")
    ax2.set_ylabel("Percentage (%)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(models)
    ax2.legend(loc="upper left")
    ax2.set_ylim(0, max(cov_vals) * 1.3)

    for b in list(b3) + list(b4):
        h = b.get_height()
        ax2.annotate(f"{h:.1f}%", xy=(b.get_x() + b.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
    return filepath


def generate_all_visualizations(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    recommender,
    eval_results: dict,
    output_dir: str = "visualizations"
) -> list:
    """Generates all 7 required visualization charts and saves them to disk."""
    print(f"\n🎨 Generating visual charts in '{output_dir}/'...")
    paths = []
    paths.append(plot_rating_distribution(ratings_df, output_dir))
    paths.append(plot_most_rated_movies(ratings_df, movies_df, top_n=15, output_dir=output_dir))
    paths.append(plot_highest_rated_movies(ratings_df, movies_df, min_ratings=50, top_n=15, output_dir=output_dir))
    paths.append(plot_user_activity(ratings_df, output_dir))
    paths.append(plot_movie_popularity_long_tail(ratings_df, output_dir))
    paths.append(plot_similarity_heatmap(recommender, output_dir))
    paths.append(plot_model_evaluation_comparison(eval_results, output_dir))

    for p in paths:
        print(f"  ✓ Saved: {p}")
    return paths
