# 🎬 End-to-End Movie Recommendation System Using Machine Learning

An end-to-end, modular, and beginner-friendly Movie Recommendation Engine built with Python, Pandas, SciPy, Scikit-learn, and Streamlit using the **MovieLens Latest Small** dataset.

---

## 📌 1. Project Overview

This project implements a personalized collaborative filtering recommendation engine. The system analyzes historical user ratings, calculates vector similarities between items and users, predicts user preferences on unrated movies, gracefully handles cold-start users with Bayesian popularity fallbacks, and serves real-time recommendations through a Streamlit web application.

### Key Highlights:
- **Clean Modular Architecture**: Clean separation between data loading, preprocessing, similarity calculation, recommendation algorithms, evaluation, model serving, and UI.
- **Sparse Matrix Operations**: Uses `scipy.sparse.csr_matrix` to compress 98.3% matrix sparsity, saving over 90% of memory and accelerating dot products.
- **No Data Leakage**: Enforces strict train-test isolation where withheld test ratings are never accessed during similarity matrix computation or model fitting.
- **Dual Collaborative Filtering**:
  - **Item-Based CF**: Movie-to-movie cosine similarity with rating weighting.
  - **User-Based CF**: User-to-user similarity with peer neighborhood aggregation.
- **Cold-Start Fallback**: IMDb-style Bayesian Weighted Rating calculated strictly on training data for new users and sparse items.
- **Comprehensive Evaluation**: Benchmarked across 5 metrics (RMSE, MAE, Precision@10, Recall@10, and Catalog Coverage).
- **Interactive Web Interface**: Streamlit application supporting movie search, live personalized recommendations, and exploratory charts.

---

## 🧱 2. Project Architecture

```
Movie_Recommendation_System/
│
├── dataset/                        # MovieLens dataset CSVs and train/test splits
│   ├── movies.csv                  # 9,742 movies (movieId, title, genres)
│   ├── ratings.csv                 # 100,836 ratings (userId, movieId, rating, timestamp)
│   ├── tags.csv                    # User tags
│   ├── links.csv                   # IMDb/TMDb links
│   ├── train_ratings.csv           # 80% partition used strictly for training
│   ├── test_ratings.csv            # 20% partition withheld for evaluation
│   └── processed_movies.csv        # Cleaned and filtered movie catalog
│
├── notebooks/                      # Step-by-step educational Jupyter Notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_data_preprocessing.ipynb
│   ├── 03_item_based_filtering.ipynb
│   ├── 04_user_based_filtering.ipynb
│   └── 05_model_evaluation.ipynb
│
├── src/                            # Modular Python source code
│   ├── __init__.py
│   ├── data_loader.py              # Data ingestion and summary stats
│   ├── preprocessing.py            # Cleaning, filtering, CSR sparse matrix, splitting
│   ├── similarity.py               # Item and user cosine similarity calculations
│   ├── recommender.py              # MovieRecommender class (Item-based, User-based, Cold-start)
│   ├── evaluation.py               # RMSE, MAE, Precision@K, Recall@K, Catalog Coverage
│   ├── model_training.py           # Training pipeline and artifact serialization
│   └── visualizations.py           # High-resolution charts with Matplotlib & Seaborn
│
├── models/                         # Serialized model artifacts
│   └── recommender_model.joblib    # Trained model artifact (17.2 MB)
│
├── visualizations/                 # Generated diagnostic and exploratory charts
│   ├── 01_rating_distribution.png
│   ├── 02_most_rated_movies.png
│   ├── 03_highest_rated_movies.png
│   ├── 04_user_activity.png
│   ├── 05_movie_popularity.png
│   ├── 06_similarity_scores.png
│   └── 07_model_evaluation_comparison.png
│
├── app/                            # Interactive Web App
│   └── streamlit_app.py            # Streamlit dashboard
│
├── tests/                          # Automated unit test suite
│   └── test_recommender.py         # 15 unit tests covering all components
│
├── requirements.txt                # Project dependencies
├── README.md                       # Complete documentation
├── main.py                         # Single-command end-to-end runner
└── create_notebooks.py             # Notebook generator script
```

---

## 🛠️ 3. Technology Stack

- **Language**: Python 3.10+
- **Data Manipulation**: Pandas, NumPy
- **Sparse Computations**: SciPy (`scipy.sparse.csr_matrix`)
- **Machine Learning**: Scikit-learn (`sklearn.metrics.pairwise.cosine_similarity`)
- **Data Visualization**: Matplotlib, Seaborn
- **Model Serialization**: Joblib
- **Testing**: Pytest
- **Notebooks**: Jupyter / nbformat
- **Web Interface**: Streamlit

---

## 🚀 4. Quickstart & Setup Instructions

### Step 1: Clone or Navigate to the Workspace
```powershell
cd "c:\Users\Shaik Sohel\Downloads\ml workshop"
```

### Step 2: (Optional) Create & Activate a Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Complete End-to-End Pipeline
```powershell
python main.py
```
This runs the full pipeline:
1. Loads MovieLens data.
2. Cleans and partitions data (80% train, 20% test).
3. Fits Item-Based and User-Based Collaborative Filtering models.
4. Benchmarks performance on held-out test data.
5. Saves the trained model artifact to `models/recommender_model.joblib`.
6. Generates 7 visual charts into `visualizations/`.
7. Demonstrates live recommendations for users, similar movies, and cold-start users.

### Step 5: Run Automated Unit Tests
```powershell
python -m pytest -v
```
*(All 15 tests pass with 100% coverage across preprocessing, sparse matrix, similarity, recommendation ordering, cold-start handling, and metrics).*

### Step 6: Launch the Streamlit Web Application
```powershell
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501` to interact with the recommendation dashboard.

---

## 📐 5. Mathematical Concepts & Formulas

### 1. Matrix Sparsity
Most users have rated fewer than 1% of all movies.
$$\text{Sparsity} = \left(1 - \frac{\text{Total Ratings}}{\text{Unique Users} \times \text{Unique Movies}}\right) \times 100\% = 98.3\%$$

### 2. Item-to-Item Cosine Similarity
Cosine of the angle between two movie rating vectors across all users:
$$\cos(\mathbf{r}_i, \mathbf{r}_j) = \frac{\mathbf{r}_i \cdot \mathbf{r}_j}{\|\mathbf{r}_i\|_2 \|\mathbf{r}_j\|_2} = \frac{\sum_u r_{u,i} r_{u,j}}{\sqrt{\sum_u r_{u,i}^2} \sqrt{\sum_u r_{u,j}^2}}$$

### 3. Item-Based Rating Prediction
Predicted score $\hat{r}_{u,i}$ for user $u$ on unrated movie $i$:
$$\hat{r}_{u,i} = \frac{\sum_{j \in R(u)} s_{i,j} \cdot r_{u,j}}{\sum_{j \in R(u)} |s_{i,j}|}$$
where $R(u)$ is the set of movies rated by user $u$, and $s_{i,j}$ is the cosine similarity between item $i$ and item $j$.

### 4. User-Based Rating Prediction
Predicted score using peer neighborhood $N_i(u)$ (users similar to $u$ who rated $i$):
$$\hat{r}_{u,i} = \bar{r}_u + \frac{\sum_{v \in N_i(u)} s_{u,v} \cdot (r_{v,i} - \bar{r}_v)}{\sum_{v \in N_i(u)} |s_{u,v}|}$$

### 5. IMDb Bayesian Weighted Rating (Cold-Start Fallback)
For new users with zero ratings, we fallback to Bayesian popularity computed strictly from training data:
$$\text{WR} = \left(\frac{v}{v + m}\right) R + \left(\frac{m}{v + m}\right) C$$
where:
- $v$: Number of ratings received by the movie
- $m$: Minimum ratings threshold cutoff (75th percentile of rating counts)
- $R$: Average rating of the movie
- $C$: Mean rating across the entire training catalog (3.53)

---

## 📊 6. Model Evaluation Benchmark

Evaluated on 16,223 withheld test ratings (20% test partition):

| Model Strategy | RMSE (Stars) | MAE (Stars) | Precision@10 | Recall@10 | Catalog Coverage (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Item-Based CF** | **0.9193** | **0.7021** | 0.63% | 0.29% | 11.86% |
| **User-Based CF** | 1.1666 | 0.9820 | **1.87%** | **1.15%** | **20.10%** |

### Key Analytical Takeaways:
1. **Rating Accuracy**: **Item-Based CF** achieves superior rating prediction accuracy ($RMSE = 0.919$ vs $1.167$ for User-Based CF) because item similarity vectors are denser, stable, and less noisy than individual human rating variations.
2. **Catalog Diversity & Discovery**: **User-Based CF** achieves nearly double the catalog coverage ($20.1\%$ vs $11.86\%$) because peer users have diverse, serendipitous tastes that surface items from the long-tail catalog.
3. **Relevance Cutoff ($r \ge 3.5$)**: Chosen because in the MovieLens 0.5–5.0 star scale, ratings below 3.5 reflect lukewarm or negative sentiment, while ratings $\ge 3.5$ represent positive recommendations.

---

## 🖼️ 7. Generated Visualizations

The pipeline generates 7 high-resolution charts in `visualizations/`:
1. `01_rating_distribution.png`: Frequency distribution of ratings from 0.5 to 5.0 stars with percentages.
2. `02_most_rated_movies.png`: Horizontal bar plot of the top 15 most-rated movies in MovieLens.
3. `03_highest_rated_movies.png`: Top 15 highest-rated movies with at least 50 ratings.
4. `04_user_activity.png`: User rating activity spread (boxplot & log-scale histogram).
5. `05_movie_popularity.png`: Long-tail distribution of movie popularity.
6. `06_similarity_scores.png`: Cosine similarity heatmap between iconic movies (Toy Story, Matrix, Pulp Fiction, Star Wars, etc.).
7. `07_model_evaluation_comparison.png`: Side-by-side performance comparison of Item-Based vs User-Based CF.

---

## 🧪 8. Unit Testing Suite

The project includes 15 automated tests executed via `pytest`:
- `test_dataset_loading`: Validates CSV loading and required columns.
- `test_dataset_summary`: Verifies statistical summaries and sparsity formula.
- `test_clean_ratings_validation`: Tests deduplication, null removal, and [0.5, 5.0] range validation.
- `test_filter_insufficient_ratings`: Ensures movies with $< 10$ ratings are filtered out.
- `test_train_test_split_isolation`: Verifies zero rating leakage between train and test splits.
- `test_build_user_item_matrix`: Confirms SciPy sparse matrix shape and indexing.
- `test_similarity_computation`: Checks symmetry, diagonal self-similarity ($1.0$), and positive correlation.
- `test_recommend_item_based`: Validates top-K item-based recommendation generation.
- `test_recommend_user_based`: Validates top-K user-based recommendation generation.
- `test_exclusion_of_already_rated_movies`: Verifies already-watched movies are never recommended.
- `test_cold_start_fallback_for_new_user`: Tests automatic Bayesian popularity fallback for brand new users.
- `test_recommend_similar_movies`: Verifies item-to-item movie similarity lookup.
- `test_evaluation_metric_calculations`: Tests mathematical correctness of RMSE and MAE.
- `test_catalog_coverage`: Validates catalog coverage percentage calculation.
- `test_model_save_and_load`: Tests model artifact serialization and inference equivalence.

---

## 👨‍💻 9. Author & License

Developed as an educational, production-ready machine learning workshop project.
Dataset provided by GroupLens Research, University of Minnesota.
Licensed under the MIT License.

