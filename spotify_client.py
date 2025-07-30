import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import requests
from PIL import Image
from io import BytesIO
import random

class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing Spotify API credentials in .env file")
            
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        ))
        self.cache_dir = "C:\\Users\\Mcs\\Desktop\\music_recommender\\data\\user_profiles\\spotify_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Popular fallback tracks across genres
        self.fallback_tracks = [
            {"id": "06AKEBrKUckW0KREUWRnvT", "name": "Blinding Lights", "artist": "The Weeknd"},
            {"id": "7tFiyTwD0nx5a1eklYtX2J", "name": "Bohemian Rhapsody", "artist": "Queen"},
            {"id": "5Z9KJZvQzH6PFmb8SNkxuk", "name": "Stay", "artist": "The Kid LAROI, Justin Bieber"},
            {"id": "0GjEhVFGZW8afUYGChu3Rr", "name": "Dancing Queen", "artist": "ABBA"},
            {"id": "4PTG3Z6ehGkBFwjybzWkR8", "name": "Shape of You", "artist": "Ed Sheeran"}
        ]

    def search_song(self, query):
        """Search for a track with enhanced error handling"""
        cache_file = f"{self.cache_dir}/search_{query.lower()[:50]}.json"
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
                    
            results = self.sp.search(q=query, limit=1, type='track', market='US')
            
            if not results['tracks']['items']:
                return None
                
            track = results['tracks']['items'][0]
            data = {
                'id': track['id'],
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'preview_url': track['preview_url'],
                'features': self._get_track_features(track['id'])
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
            
        except Exception as e:
            print(f"Search error: {e}")
            return None

    def get_recommendations(self, seed_tracks, limit=10):
        """Get recommendations with robust error handling"""
        if not seed_tracks:
            return self._get_fallback_recommendations(limit)
            
        cache_file = f"{self.cache_dir}/recs_{'_'.join(sorted(seed_tracks)[:3])}.json"
        
        try:
            # Try cache first
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    if cached:  # Only return cached if not empty
                        return cached
            
            # Get fresh recommendations
            recs = self.sp.recommendations(
                seed_tracks=seed_tracks[:5],  # Spotify's max
                limit=limit,
                market='US'
            )
            
            tracks = []
            for track in recs['tracks']:
                try:
                    if not track['preview_url']:
                        continue
                        
                    tracks.append({
                        'id': track['id'],
                        'title': track['name'],
                        'artist': track['artists'][0]['name'],
                        'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                        'preview_url': track['preview_url'],
                        'features': self._get_track_features(track['id'])
                    })
                except Exception as e:
                    print(f"Skipping track {track.get('id')}: {e}")
                    continue
            
            # Cache results if we got any
            if tracks:
                with open(cache_file, 'w') as f:
                    json.dump(tracks, f)
                return tracks
                
        except Exception as e:
            print(f"Recommendation error: {e}")
            
        return self._get_fallback_recommendations(limit)

    def _get_track_features(self, track_id):
        """Get audio features with fallback defaults"""
        try:
            features = self.sp.audio_features(track_id)[0] or {}
            return {
                'danceability': features.get('danceability', 0.5),
                'energy': features.get('energy', 0.5),
                'valence': features.get('valence', 0.5),
                'tempo': features.get('tempo', 120)
            }
        except:
            return {
                'danceability': 0.5,
                'energy': 0.5,
                'valence': 0.5,
                'tempo': 120
            }

    def _get_fallback_recommendations(self, limit):
        """Provide quality fallback recommendations"""
        fallback = random.sample(self.fallback_tracks, min(limit, len(self.fallback_tracks)))
        return [{
            'id': track['id'],
            'title': track['name'],
            'artist': track['artist'],
            'image_url': None,
            'preview_url': None,
            'features': self._get_track_features(track['id'])
        } for track in fallback]

    def get_track_image(self, url):
        """Safe image loading"""
        try:
            response = requests.get(url, timeout=3)
            return Image.open(BytesIO(response.content))
        except:
            return None