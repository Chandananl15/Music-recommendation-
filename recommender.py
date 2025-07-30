import numpy as np
from collections import defaultdict
import json
import os

class MusicRecommender:
    def __init__(self):
        self.user_profiles = {}
        self.q_values = defaultdict(lambda: defaultdict(float))
        self.alpha = 0.1  # Learning rate
        self.epsilon = 0.2  # Exploration rate
        self.profile_dir = "C:\\Users\\Mcs\\Desktop\\music_recommender\\data\\user_profiles"
        os.makedirs(self.profile_dir, exist_ok=True)

    def update_model(self, user_id, song_id, features, feedback):
        """Update RL model with robust error handling"""
        try:
            if user_id not in self.user_profiles:
                self._init_user_profile(user_id)
            
            reward = 1 if feedback == 'like' else -1
            context = self._get_user_context(user_id)
            
            # Update Q-values
            current_q = self.q_values[context].get(song_id, 0)
            self.q_values[context][song_id] = current_q + self.alpha * (reward - current_q)
            
            # Update user profile
            self._update_user_features(user_id, features, feedback)
            self._save_user_profile(user_id)
            
        except Exception as e:
            print(f"Model update error: {e}")

    def recommend(self, user_id, candidate_songs):
        """Recommend songs with exploration-exploitation"""
        try:
            if not candidate_songs:
                return None
                
            if user_id not in self.user_profiles or np.random.random() < self.epsilon:
                return random.choice(candidate_songs)
            
            context = self._get_user_context(user_id)
            q_scores = [self.q_values[context].get(song['id'], 0) for song in candidate_songs]
            return candidate_songs[np.argmax(q_scores)]
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            return random.choice(candidate_songs) if candidate_songs else None

    def _init_user_profile(self, user_id):
        self.user_profiles[user_id] = {
            'preferred_features': {
                'danceability': 0.5,
                'energy': 0.5,
                'valence': 0.5
            },
            'feedback_history': []
        }

    def _get_user_context(self, user_id):
        pf = self.user_profiles[user_id]['preferred_features']
        return f"d{int(pf['danceability']*10)}_e{int(pf['energy']*10)}_v{int(pf['valence']*10)}"

    def _update_user_features(self, user_id, features, feedback):
        weight = 0.1 if feedback == 'like' else -0.05
        for feat in ['danceability', 'energy', 'valence']:
            current = self.user_profiles[user_id]['preferred_features'][feat]
            new_val = current + weight * features.get(feat, current)
            self.user_profiles[user_id]['preferred_features'][feat] = np.clip(new_val, 0, 1)

    def _save_user_profile(self, user_id):
        try:
            with open(f"{self.profile_dir}/{user_id}.json", 'w') as f:
                json.dump(self.user_profiles[user_id], f)
        except Exception as e:
            print(f"Failed to save profile: {e}")

    def load_user_profile(self, user_id):
        try:
            with open(f"{self.profile_dir}/{user_id}.json", 'r') as f:
                self.user_profiles[user_id] = json.load(f)
            return True
        except:
            return False