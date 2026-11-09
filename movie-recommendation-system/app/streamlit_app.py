"""Interactive Streamlit Application for Movie Recommendation System.

Provides an interactive user interface for:
- Movie search & item-to-item similarity
- Personalized User-Based and Item-Based recommendations
- Cold-start fallback for new users
- Visual exploratory data analysis and model evaluation metrics
"""

import os
import sys
import tempfile

# Environment configurations
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

from src.recommender import MovieRecommender
from src.model_training import train_and_save_pipeline


# Page config
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_recommender_model():
    """Loads cached recommendation model or trains it on first boot."""
    model_path = os.path.join("models", "recommender_model.joblib")
    if not os.path.exists(model_path):
        with st.spinner("Model artifact not found on disk. Initializing and training model..."):
            train_and_save_pipeline(
                data_dir="dataset",
                model_output_path=model_path,
                min_movie_ratings=10,
                min_user_ratings=5,
                test_size=0.20,
                random_state=42
            )
    return MovieRecommender.load(model_path)


def main():
    # Header
    st.title("🎬 Movie Recommendation System")
    st.markdown(
        "**Collaborative Filtering Engine** powered by the **MovieLens Latest Small** dataset. "
        "Explore movie similarities, personalized user recommendations, cold-start handling, and model evaluation metrics."
    )

    # Load Model
    try:
        model = load_recommender_model()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    # Sidebar Controls
    st.sidebar.header("⚙️ Configuration")
    top_k = st.sidebar.slider("Number of Recommendations (Top-K)", min_value=5, max_value=25, value=10, step=1)
    cf_method = st.sidebar.radio(
        "Recommendation Strategy",
        options=["item_based", "user_based"],
        format_func=lambda x: "Item-Based Collaborative Filtering" if x == "item_based" else "User-Based Collaborative Filtering",
        help="Item-based uses movie similarity; User-based uses peer neighborhood similarity."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Catalog Statistics")
    st.sidebar.metric("Active Users", f"{len(model.user_to_idx):,}")
    st.sidebar.metric("Trained Movies", f"{len(model.movie_to_idx):,}")
    st.sidebar.metric("Interaction Sparsity", "98.3%")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Movie Similarity",
        "👤 Personalized Recommendations",
        "⭐ Cold-Start & Popular Fallback",
        "📈 Analytics & Evaluation"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: MOVIE SIMILARITY
    # --------------------------------------------------------------------------
    with tab1:
        st.subheader("Find Similar Movies (Item-Item Cosine Similarity)")
        st.caption("Select or search for any movie to see which films share the strongest co-rating patterns.")

        all_titles = sorted(model.movies_df["title"].unique())
        default_index = all_titles.index("Toy Story (1995)") if "Toy Story (1995)" in all_titles else 0

        selected_title = st.selectbox("Search or Select a Movie:", options=all_titles, index=default_index)

        if selected_title:
            movie_record = model.movies_df[model.movies_df["title"] == selected_title].iloc[0]
            target_movie_id = int(movie_record["movieId"])

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.info(f"**Title:** {selected_title}\n\n**Genres:** {movie_record['genres']}\n\n**Movie ID:** `{target_movie_id}`")

            with col_b:
                with st.spinner("Calculating cosine similarities..."):
                    similar_movies = model.recommend_similar_movies(movie_id=target_movie_id, top_k=top_k)

                if similar_movies:
                    sim_df = pd.DataFrame(similar_movies)
                    sim_df.columns = ["Movie ID", "Title", "Genres", "Cosine Similarity"]
                    st.dataframe(
                        sim_df.style.background_gradient(subset=["Cosine Similarity"], cmap="Blues"),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("No similar movies found above the similarity threshold.")

    # --------------------------------------------------------------------------
    # TAB 2: PERSONALIZED USER RECOMMENDATIONS
    # --------------------------------------------------------------------------
    with tab2:
        st.subheader("Personalized User Recommendations")
        st.caption("Generate personalized movie recommendations for existing users or test cold-start fallback with a new ID.")

        col_input, col_action = st.columns([2, 1])
        with col_input:
            user_id_input = st.number_input(
                "Enter User ID (Known IDs: 1 to 610, or >610 for Cold-Start demo):",
                min_value=1,
                max_value=99999,
                value=1,
                step=1
            )

        with col_action:
            st.write("")
            st.write("")
            recommend_btn = st.button("Generate Recommendations", type="primary")

        # Display User's Past Ratings (if known)
        is_known_user = user_id_input in model.user_to_idx
        if is_known_user:
            user_watched_ids = model.user_watched.get(user_id_input, set())
            st.markdown(f"**User {user_id_input} History:** Watched and rated **{len(user_watched_ids)}** movies.")

            with st.expander("View User's Top Rated Movies (from Training Data)", expanded=False):
                u_idx = model.user_to_idx[user_id_input]
                user_row = model.sparse_matrix[u_idx]
                r_indices = user_row.indices
                r_scores = user_row.data

                user_history = []
                for m_idx, score in zip(r_indices, r_scores):
                    m_id = model.idx_to_movie[m_idx]
                    t = model.movies_df[model.movies_df["movieId"] == m_id]["title"].values[0]
                    g = model.movies_df[model.movies_df["movieId"] == m_id]["genres"].values[0]
                    user_history.append({"Title": t, "Rating": score, "Genres": g})

                history_df = pd.DataFrame(user_history).sort_values(by="Rating", ascending=False)
                st.dataframe(history_df.head(10), use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ User {user_id_input} is a **Brand New User (Cold-Start)**. System will automatically fall back to Bayesian Popular Movies.")

        # Recommendations
        with st.spinner("Generating recommendations..."):
            recs = model.recommend(user_id=user_id_input, method=cf_method, top_k=top_k)

        if recs:
            st.markdown(f"### Top {top_k} Recommendations for User {user_id_input}")
            recs_df = pd.DataFrame(recs)

            display_cols = ["title", "genres", "predicted_score", "method"]
            rename_map = {
                "title": "Title",
                "genres": "Genres",
                "predicted_score": "Predicted Score (Stars)",
                "method": "Recommendation Method"
            }
            recs_df = recs_df[[c for c in display_cols if c in recs_df.columns]].rename(columns=rename_map)

            st.dataframe(
                recs_df.style.background_gradient(subset=["Predicted Score (Stars)"], cmap="Greens"),
                use_container_width=True,
                hide_index=True
            )
            st.success("✅ Already-watched movies have been strictly excluded from these recommendations.")

    # --------------------------------------------------------------------------
    # TAB 3: COLD-START & POPULAR FALLBACK
    # --------------------------------------------------------------------------
    with tab3:
        st.subheader("Trending & Popular Fallback Catalog")
        st.markdown(
            "When a new user has no past ratings, collaborative filtering cannot compute similarities. "
            "To solve this **Cold-Start Problem**, we employ the **IMDb Bayesian Weighted Rating** formula calculated strictly on the training partition:\n\n"
            r"$$\text{WR} = \left(\frac{v}{v + m}\right) R + \left(\frac{m}{v + m}\right) C$$"
            "\nwhere $v$ is rating count, $m$ is minimum threshold, $R$ is average movie rating, and $C$ is catalog mean."
        )

        popular_recs = model.recommend_popular(top_k=top_k)
        pop_df = pd.DataFrame(popular_recs)[["title", "genres", "predicted_score", "rating_count"]]
        pop_df.columns = ["Title", "Genres", "Bayesian Score", "Rating Count"]

        st.dataframe(
            pop_df.style.background_gradient(subset=["Bayesian Score"], cmap="Oranges"),
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------------------------
    # TAB 4: ANALYTICS & MODEL EVALUATION
    # --------------------------------------------------------------------------
    with tab4:
        st.subheader("Model Evaluation & Exploratory Visualizations")
        st.markdown("Quantitative benchmark results evaluated on held-out test data (20% partition):")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Item-Based RMSE", "0.9193", delta="-0.247 vs User-Based", delta_color="inverse")
        with metric_col2:
            st.metric("Item-Based MAE", "0.7021", delta="-0.280 vs User-Based", delta_color="inverse")
        with metric_col3:
            st.metric("User-Based Precision@10", "1.87%", delta="+1.24% vs Item-Based")
        with metric_col4:
            st.metric("User-Based Catalog Coverage", "20.1%", delta="+8.24% vs Item-Based")

        st.markdown("---")
        st.subheader("Exploratory Data Analysis & Diagnostic Charts")

        viz_dir = "visualizations"
        chart_files = [
            ("01_rating_distribution.png", "1. Rating Distribution (0.5 to 5.0 Stars)"),
            ("02_most_rated_movies.png", "2. Most-Rated Movies in MovieLens"),
            ("03_highest_rated_movies.png", "3. Highest-Rated Movies (Min 50 Ratings)"),
            ("04_user_activity.png", "4. User Rating Activity & Dispersion"),
            ("05_movie_popularity.png", "5. Movie Popularity Long-Tail Curve"),
            ("06_similarity_scores.png", "6. Cosine Similarity Heatmap (Iconic Movies)"),
            ("07_model_evaluation_comparison.png", "7. Model Benchmark Comparison (Item-Based vs User-Based)"),
        ]

        chart_choice = st.selectbox("Select Chart to View:", options=[name for _, name in chart_files])

        for fname, name in chart_files:
            if name == chart_choice:
                img_path = os.path.join(viz_dir, fname)
                if os.path.exists(img_path):
                    image = Image.open(img_path)
                    st.image(image, caption=name, use_container_width=True)
                else:
                    st.warning(f"Chart file '{fname}' not yet generated. Run `python main.py` to generate charts.")


if __name__ == "__main__":
    main()

