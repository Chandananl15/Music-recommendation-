import streamlit as st
from spotify_client import SpotifyClient
from recommender import MusicRecommender
from dotenv import load_dotenv
import time
import random

# Initialize
load_dotenv()
spotify = SpotifyClient()
recommender = MusicRecommender()

# App Config
st.set_page_config(
    page_title="AI DJ - Music Recommender",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styles
st.markdown("""
<style>
.song-card {
    padding: 20px;
    border-radius: 10px;
    margin: 15px 0;
    background: linear-gradient(135deg, #2b2d42 0%, #1a1a2e 100%);
    color: white;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.audio-container {
    width: 100%;
    margin: 15px 0;
}
.feature-bar {
    height: 8px;
    background: linear-gradient(90deg, #ff4d4d 0%, #4CAF50 100%);
    border-radius: 4px;
    margin: 5px 0;
}
.feedback-btn {
    margin: 5px;
}
</style>
""", unsafe_allow_html=True)

def display_song(song, show_features=True):
    """Display interactive song card"""
    if not song:
        return
        
    col1, col2 = st.columns([1, 3])
    
    with col1:
        img = spotify.get_track_image(song.get('image_url'))
        st.image(img or "https://via.placeholder.com/200", width=200)
    
    with col2:
        st.markdown(f"""
        <div class="song-card">
            <h3>{song['title']}</h3>
            <p>{song['artist']}</p>
        """, unsafe_allow_html=True)
        
        if song.get('preview_url'):
            st.audio(song['preview_url'], format='audio/mp3')
        else:
            st.warning("Preview not available")
            
        if show_features and song.get('features'):
            st.markdown("**Audio Features:**")
            for feat, val in song['features'].items():
                if feat in ['danceability', 'energy', 'valence']:
                    st.markdown(f"""
                    {feat.capitalize()}: 
                    <div class="feature-bar" style="width: {val*100}%"></div>
                    """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.title("🎧 Music Discovery")
    st.markdown("Find similar songs using Spotify and reinforcement learning")
    
    # Initialize session state
    if 'current_recs' not in st.session_state:
        st.session_state.current_recs = []
    if 'seed_song' not in st.session_state:
        st.session_state.seed_song = None
    
    # User input
    with st.form("song_search"):
        query = st.text_input("Enter a song you like:", 
                            placeholder="e.g. Blinding Lights The Weeknd")
        submitted = st.form_submit_button("Find Similar Songs")
    
    if submitted and query:
        with st.spinner('Searching for your song...'):
            st.session_state.seed_song = spotify.search_song(query)
            
        if not st.session_state.seed_song:
            st.error("Song not found. Try another one!")
            return
            
        st.success("Found your song! Loading recommendations...")
        with st.spinner('Analyzing music patterns...'):
            st.session_state.current_recs = spotify.get_recommendations(
                [st.session_state.seed_song['id']]
            )
    
    # Display results
    if st.session_state.seed_song:
        st.subheader(f"Similar to: {st.session_state.seed_song['title']}")
        display_song(st.session_state.seed_song, show_features=False)
        
        if st.session_state.current_recs:
            st.subheader("Recommended Tracks")
            for i, song in enumerate(st.session_state.current_recs):
                display_song(song)
                
                # Feedback buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"👍 Like", key=f"like_{i}"):
                        recommender.update_model(
                            user_id="current_user",
                            song_id=song['id'],
                            features=song['features'],
                            feedback='like'
                        )
                        st.success("Added to your preferences!")
                        time.sleep(1)
                        st.experimental_rerun()
                
                with col2:
                    if st.button(f"👎 Dislike", key=f"dislike_{i}"):
                        recommender.update_model(
                            user_id="current_user",
                            song_id=song['id'],
                            features=song['features'],
                            feedback='dislike'
                        )
                        st.error("We'll avoid similar songs")
                        time.sleep(1)
                        st.experimental_rerun()
                
                st.write("---")
        else:
            st.warning("Couldn't generate recommendations. Try another song!")

if __name__ == "__main__":
    main()