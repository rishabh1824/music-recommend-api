# recommendations/recommend.py
import pandas as pd
import mysql.connector
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify

# ─── 1. Load play data ───────────────────────────────────────────────────────────
df = pd.read_csv("recommendations/listening_data.csv")



# ─── 2. Build user–song matrix ───────────────────────────────────────────────────
user_song = df.groupby(["user_id", "song_id"]).size().unstack(fill_value=0)

# ─── 3. Compute user–user similarity ─────────────────────────────────────────────
sim_matrix = cosine_similarity(user_song)
user_ids = user_song.index.tolist()
user_sim = pd.DataFrame(sim_matrix, index=user_ids, columns=user_ids)

# ─── 4. Fallback: Recommend most popular songs ───────────────────────────────────
def most_popular_songs(top_n=5):
    song_counts = df['song_id'].value_counts()
    return song_counts.head(top_n).index.tolist()

# ─── 5. Recommendation function ──────────────────────────────────────────────────
def recommend(user_id, top_n=5):
    if user_id not in user_sim:
        return most_popular_songs(top_n)

    sims = user_sim[user_id].drop(user_id)
    if sims.empty:
        return most_popular_songs(top_n)

    most_similar = sims.idxmax()
    played_by_peer = set(user_song.columns[user_song.loc[most_similar] > 0])
    played_by_you  = set(user_song.columns[user_song.loc[user_id] > 0])
    rec_songs = list(played_by_peer - played_by_you)

    if not rec_songs:
        return most_popular_songs(top_n)

    return rec_songs[:top_n]

# ─── 6. Flask API Server ─────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route('/recommend')
def api_recommend():
    user_id = request.args.get('user_id', type=int)
    if user_id is None:
        return jsonify({'error': 'Missing user_id'}), 400

    recommendations = recommend(user_id)
    return jsonify({'user_id': user_id, 'recommendations': recommendations})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
