import streamlit as st
import pickle
import requests
import pandas as pd
import joblib

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# --- INJECT CUSTOM CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# --- DATA LOADING ---
with st.spinner('Loading movie data...'):
    movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = joblib.load('similarity_compressed.pkl')

# --- TMDB API CALL FUNCTION (details + poster) ---
def fetch_movie_details(movie_id):
    """Fetches movie details (poster + info) from TMDB API."""
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        poster_path = data.get('poster_path')
        poster_url = "https://image.tmdb.org/t/p/w500/" + poster_path if poster_path else "https://via.placeholder.com/500x750.png?text=No+Poster"
        
        details = {
            "title": data.get("title", "Unknown Title"),
            "overview": data.get("overview", "No overview available."),
            "rating": data.get("vote_average", "N/A"),
            "genres": ", ".join([g['name'] for g in data.get('genres', [])]),
            "poster": poster_url
        }
        return details
    except requests.exceptions.RequestException:
        return {
            "title": "Error",
            "overview": "Could not fetch details",
            "rating": "N/A",
            "genres": "N/A",
            "poster": "https://via.placeholder.com/500x750.png?text=API+Error"
        }

# --- RECOMMEND FUNCTION ---
def recommend(movie_title, num_recommendations=5):
    try:
        movie_index = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        st.error("Movie not found in the dataset.")
        return []
        
    distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])
    
    recommended_movies = []
    for i in distances[1:num_recommendations+1]:
        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_movie_details(movie_id)
        recommended_movies.append(details)
        
    return recommended_movies

# --- UI LAYOUT ---
st.title('🎬 Movie Recommender System')
st.markdown("### Find your next favorite movie!")

selected_movie = st.selectbox(
    "Type or select a movie you like:",
    movies['title'].values
)

# SLIDER TO SELECT NUMBER OF RECOMMENDATIONS
num_recommendations = st.slider(
    'How many recommendations would you like?',
    min_value=3, max_value=20, value=6, step=1
)

if st.button('Show Recommendations', type='primary', help='Click to see movie recommendations', use_container_width=True):
    with st.spinner(f'Finding movies similar to "{selected_movie}"...'):
        recommended_movies = recommend(selected_movie, num_recommendations)
        
        if recommended_movies:
            st.markdown("---")
            st.subheader("Here are some movies you might like:")
        
            cols_per_row = 5
            for i in range(0, len(recommended_movies), cols_per_row):
                cols = st.columns(cols_per_row)
                row_movies = recommended_movies[i : i + cols_per_row]
                
                for j, col in enumerate(cols):
                    if j < len(row_movies):
                        movie = row_movies[j]
                        with col:
                            st.markdown(f"""
                                <div class="movie-card" style="position: relative; display: inline-block; width:100%; margin-bottom:15px; border-radius:12px; overflow:hidden;">
                                    <img src="{movie['poster']}" style="width:100%; border-radius:12px; display:block;"/>
                                    <div class="overlay">
                                        <div style="padding:12px; color:#fff; text-align:left;">
                                            <b style="font-size:16px;">{movie['title']}</b><br>
                                            ⭐ {movie['rating']}/10<br>
                                            🎭 {movie['genres']}<br><br>
                                            <span style="font-size:13px; line-height:1.4;">{movie['overview'][:200]}...</span>
                                        </div>
                                    </div>
                                </div>

                                <style>
                                    .movie-card .overlay {{
                                        position: absolute;
                                        top: 0;
                                        left: 0;
                                        width: 100%;
                                        height: 100%;
                                        background: rgba(0, 0, 0, 0.65);
                                        backdrop-filter: blur(6px);
                                        opacity: 0;
                                        transition: opacity 0.4s ease-in-out;
                                        border-radius:12px;
                                    }}
                                    .movie-card:hover .overlay {{
                                        opacity: 1;
                                    }}
                                </style>
                            """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("""
<hr style="margin-top: 50px;">
<div style="text-align: center;">
    <p>Made with ❤ by Shazim Javed | Source: TMDB 5000 Movie Dataset</p>
</div>
""", unsafe_allow_html=True)
