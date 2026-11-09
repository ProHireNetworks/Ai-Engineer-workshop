"""Script to generate all 5 educational Jupyter Notebooks for the Movie Recommendation System."""

import os
import nbformat as nbf


def make_cell(cell_type, text):
    if cell_type == "markdown":
        return nbf.v4.new_markdown_cell(text)
    elif cell_type == "code":
        return nbf.v4.new_code_cell(text)


def create_all_notebooks(output_dir="notebooks"):
    os.makedirs(output_dir, exist_ok=True)

    # =========================================================================
    # NOTEBOOK 1: DATA EXPLORATION
    # =========================================================================
    nb1 = nbf.v4.new_notebook()
    nb1.cells = [
        make_cell("markdown", """# 📊 Module 2: MovieLens Dataset Exploration & EDA
**Movie Recommendation System Using Machine Learning**

---

### 🎯 Objectives
1. Understand the structure and schema of the **MovieLens Latest Small** dataset.
2. Load and inspect `movies.csv`, `ratings.csv`, `tags.csv`, and `links.csv` using Pandas.
3. Compute statistical summaries and understand **Matrix Sparsity**.
4. Visualize rating distributions, user activity patterns, and movie popularity curves.
5. Practice beginner exercises to reinforce your learning.
"""),
        make_cell("code", """import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set clean aesthetic styling
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (9, 5)

print("Environment ready!")
"""),
        make_cell("markdown", """## 1. Loading the Dataset
We load the raw CSV files stored in the `dataset/` directory.
- `movies.csv`: Maps each `movieId` to its `title` and pipe-separated `genres`.
- `ratings.csv`: Contains historical user interactions `(userId, movieId, rating, timestamp)`.
- `tags.csv`: Free-form user tags applied to movies.
- `links.csv`: Identifiers linking to IMDb and TMDb.
"""),
        make_cell("code", """data_dir = "../dataset"

movies_df = pd.read_csv(os.path.join(data_dir, "movies.csv"))
ratings_df = pd.read_csv(os.path.join(data_dir, "ratings.csv"))
tags_df = pd.read_csv(os.path.join(data_dir, "tags.csv"))
links_df = pd.read_csv(os.path.join(data_dir, "links.csv"))

print(f"Movies Shape:  {movies_df.shape}")
print(f"Ratings Shape: {ratings_df.shape}")
print(f"Tags Shape:    {tags_df.shape}")
print(f"Links Shape:   {links_df.shape}")
"""),
        make_cell("markdown", """## 2. Inspecting First Records and Data Types"""),
        make_cell("code", """print("--- MOVIES HEAD ---")
display(movies_df.head(5))

print("\\n--- RATINGS HEAD ---")
display(ratings_df.head(5))
"""),
        make_cell("code", """print("--- MOVIES INFO ---")
movies_df.info()

print("\\n--- RATINGS INFO ---")
ratings_df.info()
"""),
        make_cell("markdown", """## 3. Statistical Summaries & Catalog Sparsity

### What is Matrix Sparsity?
In collaborative filtering, users only rate a tiny fraction of available movies.
$$\\text{Sparsity (\\%)} = \\left(1 - \\frac{\\text{Total Observed Ratings}}{\\text{Unique Users} \\times \\text{Unique Movies}}\\right) \\times 100$$
"""),
        make_cell("code", """num_users = ratings_df["userId"].nunique()
num_movies = movies_df["movieId"].nunique()
num_ratings = len(ratings_df)

total_possible = num_users * num_movies
sparsity = (1.0 - (num_ratings / total_possible)) * 100.0

print(f"Unique Users:           {num_users:,}")
print(f"Unique Movies:          {num_movies:,}")
print(f"Total Observed Ratings: {num_ratings:,}")
print(f"Total Possible Cells:   {total_possible:,}")
print(f"Matrix Sparsity:        {sparsity:.2f}%")
print(f"\\nRating Scale: min={ratings_df['rating'].min()}, max={ratings_df['rating'].max()}, mean={ratings_df['rating'].mean():.2f}")
"""),
        make_cell("markdown", """## 4. Visualizing Rating Distributions
Let's see how users distribute their scores (0.5 to 5.0).
"""),
        make_cell("code", """rating_counts = ratings_df["rating"].value_counts().sort_index()

plt.figure(figsize=(9, 5))
ax = sns.barplot(x=rating_counts.index.astype(str), y=rating_counts.values, palette="Blues_d")
plt.title("Distribution of Ratings in MovieLens (100,836 ratings)", fontsize=14, fontweight="bold")
plt.xlabel("Rating Score (Stars)")
plt.ylabel("Frequency")

for p in ax.patches:
    h = p.get_height()
    pct = (h / num_ratings) * 100
    ax.annotate(f"{pct:.1f}%", (p.get_x() + p.get_width() / 2, h + 800), ha="center", fontsize=9, fontweight="bold")

plt.show()
"""),
        make_cell("markdown", """## 5. Identifying the Most-Rated Movies"""),
        make_cell("code", """top_movies = ratings_df["movieId"].value_counts().head(10).reset_index()
top_movies.columns = ["movieId", "rating_count"]
top_movies = top_movies.merge(movies_df, on="movieId")

plt.figure(figsize=(10, 5))
sns.barplot(data=top_movies, y="title", x="rating_count", palette="viridis")
plt.title("Top 10 Most-Rated Movies", fontsize=14, fontweight="bold")
plt.xlabel("Number of Ratings")
plt.ylabel("Movie Title")
plt.show()
"""),
        make_cell("markdown", """## 6. Beginner Exercises & Common Pitfalls

### 📝 Exercises
1. Find the user who has rated the largest number of movies. How many ratings did they submit?
2. Calculate the average rating for movies in the `Animation` genre versus `Action` genre.
3. Why are half-star ratings (e.g. 0.5, 1.5, 2.5) less common than integer ratings (e.g. 3.0, 4.0)?

### ⚠️ Common Errors & Fixes
- **Error:** `KeyError: 'title'` when merging `ratings_df` and `movies_df`.
  - **Fix:** Ensure merge is done using `on='movieId'` and that column names match casing.
- **Error:** Memory crash when computing `ratings_df.pivot(...)` on massive datasets.
  - **Fix:** Never pivot uncompressed millions of entries into dense matrices without sparse representation!
"""),
    ]

    with open(os.path.join(output_dir, "01_data_exploration.ipynb"), "w", encoding="utf-8") as f:
        nbf.write(nb1, f)

    # =========================================================================
    # NOTEBOOK 2: DATA PREPROCESSING
    # =========================================================================
    nb2 = nbf.v4.new_notebook()
    nb2.cells = [
        make_cell("markdown", """# 🧹 Module 3, 4 & 5: Data Preprocessing, Sparse Matrices, and Train-Test Splitting
**Movie Recommendation System Using Machine Learning**

---

### 🎯 Objectives
1. Clean data: Remove null values, duplicates, and validate rating ranges $[0.5, 5.0]$.
2. Filter movies with insufficient ratings to eliminate statistical noise.
3. Perform a reproducible **Train-Test Split** and learn how to **prevent data leakage**.
4. Construct a User-Item interaction matrix and convert it into a **SciPy CSR sparse matrix**.
5. Understand the memory and computational benefits of sparse representations.
"""),
        make_cell("code", """import os
import sys
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

sys.path.insert(0, "..")
from src.preprocessing import (
    clean_movies,
    clean_ratings,
    filter_insufficient_ratings,
    train_test_split_ratings,
    build_user_item_matrix
)

print("Modules imported successfully!")
"""),
        make_cell("markdown", """## 1. Cleaning Raw Data
We validate that:
- No IDs or ratings are null.
- Duplicate user ratings for the same movie are resolved.
- Ratings fall strictly within $[0.5, 5.0]$.
"""),
        make_cell("code", """raw_movies = pd.read_csv("../dataset/movies.csv")
raw_ratings = pd.read_csv("../dataset/ratings.csv")

cleaned_movies = clean_movies(raw_movies)
cleaned_ratings = clean_ratings(raw_ratings)

print(f"Cleaned Movies:  {len(cleaned_movies):,}")
print(f"Cleaned Ratings: {len(cleaned_ratings):,}")
"""),
        make_cell("markdown", """## 2. Filtering Insufficient Ratings (Noise Reduction)
Movies with only 1 or 2 ratings provide almost zero co-occurrence overlap, creating noise.
We retain movies with at least 10 ratings.
"""),
        make_cell("code", """filtered_ratings, filtered_movies = filter_insufficient_ratings(
    cleaned_ratings,
    cleaned_movies,
    min_movie_ratings=10,
    min_user_ratings=5
)

print(f"Retained Movies:  {len(filtered_movies):,}")
print(f"Retained Ratings: {len(filtered_ratings):,}")
print(f"Retained Users:   {filtered_ratings['userId'].nunique():,}")
"""),
        make_cell("markdown", """## 3. Train-Test Splitting & Preventing Data Leakage

### 🛡️ Why Data Leakage Prevention is Critical
In recommendation systems, data leakage occurs if the test ratings are visible when building
the interaction matrix or calculating similarity scores.
To prevent leakage:
1. Split ratings randomly (80% train, 20% test) using a fixed seed (`random_state=42`).
2. Train similarity matrices and popular lists **strictly on train ratings**.
3. Use test ratings **solely** to benchmark prediction accuracy.
"""),
        make_cell("code", """train_ratings, test_ratings = train_test_split_ratings(
    filtered_ratings, test_size=0.20, random_state=42
)

print(f"Training ratings: {len(train_ratings):,} ({len(train_ratings)/len(filtered_ratings)*100:.1f}%)")
print(f"Testing ratings:  {len(test_ratings):,} ({len(test_ratings)/len(filtered_ratings)*100:.1f}%)")

# Verify zero overlap
train_pairs = set(zip(train_ratings["userId"], train_ratings["movieId"]))
test_pairs = set(zip(test_ratings["userId"], test_ratings["movieId"]))
leakage = train_pairs.intersection(test_pairs)
print(f"Overlapping interaction pairs: {len(leakage)} (Zero indicates NO data leakage!)")
"""),
        make_cell("markdown", """## 4. Building the User-Item Sparse Interaction Matrix

### Why SciPy CSR Matrix?
A dense matrix of 610 users $\times$ 2,269 movies = 1.38 million cells, 98% of which are zeroes.
Compressed Sparse Row (`csr_matrix`) stores:
- Non-zero values (`data`)
- Column indices (`indices`)
- Row pointers (`indptr`)
"""),
        make_cell("code", """sparse_mat, u2idx, idx2u, m2idx, idx2m, pivot_df = build_user_item_matrix(
    train_ratings, filtered_movies
)

dense_size_bytes = sparse_mat.shape[0] * sparse_mat.shape[1] * 4  # float32 = 4 bytes
sparse_size_bytes = (sparse_mat.data.nbytes + sparse_mat.indices.nbytes + sparse_mat.indptr.nbytes)

print(f"Matrix Shape:               {sparse_mat.shape} (Users x Movies)")
print(f"Non-zero ratings stored:    {sparse_mat.nnz:,}")
print(f"Dense matrix memory:        {dense_size_bytes / 1024:.2f} KB")
print(f"Sparse CSR matrix memory:   {sparse_size_bytes / 1024:.2f} KB")
print(f"Memory reduction ratio:     {dense_size_bytes / sparse_size_bytes:.1f}x smaller!")
"""),
        make_cell("markdown", """## 5. Beginner Exercises & Common Errors

### 📝 Exercises
1. Inspect the row in `sparse_mat` for user 1. How many movies did user 1 rate in the training set?
2. What happens if you try to index a movie that was filtered out? How does the mapping dictionary protect against index errors?

### ⚠️ Common Errors & Fixes
- **Error:** MemoryError when calling `sparse_matrix.toarray()`.
  - **Fix:** Never convert massive sparse matrices to dense arrays in memory; keep them as CSR/CSC matrices.
"""),
    ]

    with open(os.path.join(output_dir, "02_data_preprocessing.ipynb"), "w", encoding="utf-8") as f:
        nbf.write(nb2, f)

    # =========================================================================
    # NOTEBOOK 3: ITEM-BASED FILTERING
    # =========================================================================
    nb3 = nbf.v4.new_notebook()
    nb3.cells = [
        make_cell("markdown", """# 🎬 Module 6: Item-Based Collaborative Filtering
**Movie Recommendation System Using Machine Learning**

---

### 🎯 Objectives
1. Understand the intuition and mathematical formula for **Item-to-Item Cosine Similarity**.
2. Compute cosine similarity efficiently using transposed SciPy sparse matrices.
3. Find movies most similar to any selected movie.
4. Predict user ratings for unseen movies:
   $$\\hat{r}_{u,i} = \\frac{\\sum_{j \\in R(u)} s_{i,j} \\cdot r_{u,j}}{\\sum_{j \\in R(u)} |s_{i,j}|}$$
5. Exclude already-watched movies and rank the top-K recommendations.
"""),
        make_cell("code", """import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, "..")
from src.data_loader import load_dataset
from src.preprocessing import clean_movies, clean_ratings, filter_insufficient_ratings, train_test_split_ratings, build_user_item_matrix
from src.similarity import compute_item_similarity, get_top_similar_items
from src.recommender import MovieRecommender

print("Imports ready!")
"""),
        make_cell("markdown", """## 1. Mathematical Concept: Item-Item Cosine Similarity

Given two items $i$ and $j$, represented as rating vectors across all users $\\mathbf{r}_i, \\mathbf{r}_j$:
$$\\text{similarity}(i, j) = \\cos(\\mathbf{r}_i, \\mathbf{r}_j) = \\frac{\\sum_u r_{u,i} \\cdot r_{u,j}}{\\sqrt{\\sum_u r_{u,i}^2} \\cdot \\sqrt{\\sum_u r_{u,j}^2}}$$
- $1.0$ indicates identical co-rating profiles.
- $0.0$ indicates completely orthogonal (no shared users or zero overlap).
"""),
        make_cell("code", """# Load pre-trained model or train pipeline
model = MovieRecommender.load("../models/recommender_model.joblib")
print(f"Loaded model with {len(model.movie_to_idx):,} movies and {len(model.user_to_idx):,} users.")
"""),
        make_cell("markdown", """## 2. Finding Movies Similar to a Target Movie"""),
        make_cell("code", """def show_similar(movie_title, top_k=5):
    matches = model.search_movies(movie_title, top_k=1)
    if not matches:
        print("Movie not found!")
        return
    m_id = matches[0]["movieId"]
    print(f"🎯 Target Movie: {matches[0]['title']} ({matches[0]['genres']})")
    sims = model.recommend_similar_movies(m_id, top_k=top_k)
    return pd.DataFrame(sims)

display(show_similar("Toy Story", top_k=5))
"""),
        make_cell("code", """display(show_similar("Matrix, The", top_k=5))
"""),
        make_cell("markdown", """## 3. Generating Personalized Recommendations for a User
We predict ratings for unrated movies and strictly exclude already-watched films.
"""),
        make_cell("code", """user_id = 1
user_watched = model.user_watched.get(user_id, set())
print(f"User {user_id} has watched {len(user_watched)} movies in training set.")

recs = model.recommend_item_based(user_id=user_id, top_k=5)
rec_df = pd.DataFrame(recs)
display(rec_df)

# Check exclusion of watched movies
overlaps = set(rec_df["movieId"]).intersection(user_watched)
print(f"Watched movies in recommendation list: {len(overlaps)} (Must be 0)")
"""),
        make_cell("markdown", """## 4. Beginner Exercises
1. Pick your favorite movie from the catalog. What are its top 5 most similar movies according to the cosine similarity matrix?
2. Why is Item-Based Collaborative Filtering generally more stable over time than User-Based CF in large streaming systems like Netflix?
   *(Hint: Item profiles change slowly as new ratings come in; user tastes change dynamically.)*
"""),
    ]

    with open(os.path.join(output_dir, "03_item_based_filtering.ipynb"), "w", encoding="utf-8") as f:
        nbf.write(nb3, f)

    # =========================================================================
    # NOTEBOOK 4: USER-BASED FILTERING & COLD START
    # =========================================================================
    nb4 = nbf.v4.new_notebook()
    nb4.cells = [
        make_cell("markdown", """# 👥 Module 7, 8 & 9: User-Based CF, Ranking, and the Cold-Start Problem
**Movie Recommendation System Using Machine Learning**

---

### 🎯 Objectives
1. Understand **User-to-User Collaborative Filtering** (finding peer neighbors).
2. Compare Item-Based CF vs User-Based CF (strengths, weaknesses, catalog coverage).
3. Understand the **Cold-Start Problem** (new users with zero ratings).
4. Implement the **IMDb Bayesian Weighted Rating** fallback strictly on training data.
"""),
        make_cell("code", """import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, "..")
from src.recommender import MovieRecommender

model = MovieRecommender.load("../models/recommender_model.joblib")
print("Model ready!")
"""),
        make_cell("markdown", """## 1. Finding Similar Users (Nearest Neighbors)
We compute similarity across users based on their rating overlap:
$$\\text{sim}(u, v) = \\frac{\\mathbf{r}_u \\cdot \\mathbf{r}_v}{\\|\\mathbf{r}_u\\| \\|\\mathbf{r}_v\\|}$$
"""),
        make_cell("code", """from src.similarity import get_top_similar_users

target_user = 1
similar_users = get_top_similar_users(
    user_id=target_user,
    user_similarity=model.user_similarity,
    user_to_idx=model.user_to_idx,
    idx_to_user=model.idx_to_user,
    top_k=5
)

print(f"Top 5 users most similar to User {target_user}:")
for u, s in similar_users:
    print(f"  • User {u}: Similarity = {s:.4f}")
"""),
        make_cell("markdown", """## 2. Generating User-Based Recommendations"""),
        make_cell("code", """user_recs = model.recommend_user_based(user_id=1, top_k=5)
display(pd.DataFrame(user_recs))
"""),
        make_cell("markdown", """## 3. The Cold-Start Problem & Bayesian Popularity Fallback

### What is the Cold-Start Problem?
When a new user joins, they have rated zero movies.
The similarity dot products are zero, so collaborative filtering fails!

### Solution: IMDb Bayesian Weighted Rating (WR)
$$\\text{WR} = \\left(\\frac{v}{v + m}\\right) R + \\left(\\frac{m}{v + m}\\right) C$$
- $v$: Number of ratings the movie received in training data
- $m$: Minimum ratings threshold (confidence parameter)
- $R$: Average rating of the movie
- $C$: Mean rating across the entire training catalog
"""),
        make_cell("code", """# Test brand new user with ID 88888
new_user_id = 88888
cold_start_recs = model.recommend(user_id=new_user_id, top_k=5)
print(f"Recommendations for Cold-Start User {new_user_id}:")
display(pd.DataFrame(cold_start_recs))
"""),
        make_cell("markdown", """## 4. Beginner Exercises
1. Compare the top 5 recommendations for User 1 between Item-Based CF and User-Based CF. Do they overlap?
2. Why is the Bayesian Weighted Rating superior to simple average rating for ranking popular movies?
"""),
    ]

    with open(os.path.join(output_dir, "04_user_based_filtering.ipynb"), "w", encoding="utf-8") as f:
        nbf.write(nb4, f)

    # =========================================================================
    # NOTEBOOK 5: MODEL EVALUATION
    # =========================================================================
    nb5 = nbf.v4.new_notebook()
    nb5.cells = [
        make_cell("markdown", """# 📊 Module 10: Model Evaluation & Benchmarking
**Movie Recommendation System Using Machine Learning**

---

### 🎯 Objectives
1. Understand why recommender system evaluation requires both **Rating Accuracy** and **Ranking Quality** metrics.
2. Calculate and explain **RMSE** (Root Mean Squared Error) and **MAE** (Mean Absolute Error).
3. Calculate and explain **Precision@K** and **Recall@K** using a relevance threshold ($r \\ge 3.5$).
4. Calculate **Catalog Coverage** to measure recommendation diversity.
5. Benchmark Item-Based CF against User-Based CF.
"""),
        make_cell("code", """import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, "..")
from src.recommender import MovieRecommender
from src.evaluation import run_full_evaluation

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 5)

print("Environment ready!")
"""),
        make_cell("markdown", """## 1. Mathematical Formulas for Metrics

### 1. Root Mean Squared Error (RMSE)
$$\\text{RMSE} = \\sqrt{\\frac{1}{|T|} \\sum_{(u,i) \\in T} (r_{u,i} - \\hat{r}_{u,i})^2}$$
Penalizes large errors heavily.

### 2. Mean Absolute Error (MAE)
$$\\text{MAE} = \\frac{1}{|T|} \\sum_{(u,i) \\in T} |r_{u,i} - \\hat{r}_{u,i}|$$
Linear, interpretable average star error.

### 3. Precision@K and Recall@K
- Item is *Relevant* if actual rating $\\ge 3.5$.
$$\\text{Precision@K} = \\frac{|\\text{Recommended}_K \\cap \\text{Relevant}|}{K}$$
$$\\text{Recall@K} = \\frac{|\\text{Recommended}_K \\cap \\text{Relevant}|}{|\\text{Relevant}|}$$

### 4. Catalog Coverage
$$\\text{Coverage} = \\frac{|\\bigcup_u \\text{Recommended}_u|}{|\\text{Catalog Items}|} \\times 100\\%$$
"""),
        make_cell("code", """# Load model and test ratings
model = MovieRecommender.load("../models/recommender_model.joblib")
test_ratings = pd.read_csv("../dataset/test_ratings.csv")

print(f"Loaded {len(test_ratings):,} held-out test ratings.")
"""),
        make_cell("code", """# Run complete benchmark
results = run_full_evaluation(
    recommender=model,
    test_ratings_df=test_ratings,
    k=10,
    relevance_threshold=3.5,
    num_eval_users=80,
    max_rating_pairs=2000
)

results_df = pd.DataFrame(results).T
display(results_df)
"""),
        make_cell("markdown", """## 2. Visualization of Evaluation Benchmark"""),
        make_cell("code", """fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# RMSE & MAE
models = ["Item-Based CF", "User-Based CF"]
rmse = [results["item_based"]["RMSE"], results["user_based"]["RMSE"]]
mae = [results["item_based"]["MAE"], results["user_based"]["MAE"]]

x = np.arange(len(models))
w = 0.35
ax1.bar(x - w/2, rmse, w, label="RMSE", color="#4C72B0")
ax1.bar(x + w/2, mae, w, label="MAE", color="#55A868")
ax1.set_title("Rating Prediction Error (Lower is Better)")
ax1.set_ylabel("Error (Stars)")
ax1.set_xticks(x)
ax1.set_xticklabels(models)
ax1.legend()

# Coverage
cov = [results["item_based"]["Coverage@10 (%)"], results["user_based"]["Coverage@10 (%)"]]
ax2.bar(models, cov, color=["#C44E52", "#8172B2"])
ax2.set_title("Catalog Coverage @ 10 (Higher is Better)")
ax2.set_ylabel("Catalog Coverage (%)")

plt.tight_layout()
plt.show()
"""),
        make_cell("markdown", """## 3. Summary & Takeaways
- **Item-Based CF** achieves significantly lower prediction error (lower RMSE and MAE) because item similarity patterns are dense and robust across users.
- **User-Based CF** exhibits higher catalog coverage because users possess diverse idiosyncratic tastes that surface a wider variety of recommendations.
"""),
    ]

    with open(os.path.join(output_dir, "05_model_evaluation.ipynb"), "w", encoding="utf-8") as f:
        nbf.write(nb5, f)

    print(f"✅ All 5 Jupyter Notebooks created successfully in '{output_dir}/'!")


if __name__ == "__main__":
    create_all_notebooks()

