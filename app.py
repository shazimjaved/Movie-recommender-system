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

def fetch_poster(movie_id):
    """Fetches a movie poster URL from the TMDB API and handles errors."""
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            return "https://via.placeholder.com/500x750.png?text=No+Poster"
    except requests.exceptions.RequestException:
        return "https://via.placeholder.com/500x750.png?text=API+Error"

# **MODIFIED RECOMMEND FUNCTION**
def recommend(movie_title, num_recommendations=5):
    """Recommends movies based on the selected movie and number requested."""
    try:
        movie_index = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        st.error("Movie not found in the dataset.")
        return [], []
        
    distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])
    
    recommended_movie_names = []
    recommended_movie_posters = []
    
    # **MODIFIED LOOP TO USE THE SLIDER VALUE**
    for i in distances[1:num_recommendations+1]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
        
    return recommended_movie_names, recommended_movie_posters

# --- UI LAYOUT ---
st.title('🎬 Movie Recommender System')
# st.markdown("Made with ❤️ by Shazim Javed")
# st.markdown("---")
st.markdown("### Find your next favorite movie!")
# st.markdown("Source: TMDB 5000 Movie Dataset")


selected_movie = st.selectbox(
    "Type or select a movie you like:",
    movies['title'].values
)

# SLIDER TO SELECT NUMBER OF RECOMMENDATIONS**
num_recommendations = st.slider(
    'How many recommendations would you like?',
    min_value=3, max_value=20, value=6, step=1
)

if st.button('Show Recommendations',type='primary',help='Click to see movie recommendations',use_container_width=True):
    with st.spinner(f'Finding movies similar to "{selected_movie}"...'):
        # **Pass the slider value to the function**
        recommended_names, recommended_posters = recommend(selected_movie, num_recommendations)
        
        if recommended_names:
            st.markdown("---")
            st.subheader("Here are some movies you might like:")
        
            cols_per_row = 5
            
            # Create rows and columns dynamically
            for i in range(0, len(recommended_names), cols_per_row):
                # Create a new row of columns
                cols = st.columns(cols_per_row)
                # Get the recommendations for the current row
                row_names = recommended_names[i : i + cols_per_row]
                row_posters = recommended_posters[i : i + cols_per_row]
                
                # Display each card in its column
                for j, col in enumerate(cols):
                    if j < len(row_names):
                        with col:
                            st.image(row_posters[j], use_container_width=True)
                            st.caption(row_names[j])
st.markdown("""
<hr style="margin-top: 50px;">
<div style="text-align: center;">
    <p>Made with ❤️ by Shazim Javed | Source: TMDB 5000 Movie Dataset</p>
</div>
""",unsafe_allow_html=True)