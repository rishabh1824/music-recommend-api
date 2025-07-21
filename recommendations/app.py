from flask import Flask, request, jsonify
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector

app = Flask(__name__)

# ─── Load Data on Startup ─────────────────────────────────────────────
def load_data():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="login"
    )
    df = pd.read_sql("SELECT user_id, song_id FROM listening_log", conn)
    conn.close()
    return df

df = load_data()

# ─── Build User-Song Matrix & Similarity ──────────────────────────────
user_song = df.groupby(["user_id", "song_id"]).size().unstack(fill_value=0)
sim_matrix = cosine_similarity(user_song)
user_ids = user_song.index.tolist()
user_sim = pd.DataFrame(sim_matrix, index=user_ids, columns=user_ids)

# ─── Fetch Song Details from DB ───────────────────────────────────────
def get_song_details(song_ids):
    if not song_ids:
        return []

    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="login"
    )
    placeholders = ','.join(['%s'] * len(song_ids))
    query = f"SELECT id, songName, subtitle FROM songs WHERE id IN ({placeholders})"
    cursor = conn.cursor()
    cursor.execute(query, tuple(song_ids))
    results = cursor.fetchall()
    conn.close()

    return [f"{name} by {artist}" for _, name, artist in results]

# ─── Recommend Songs ──────────────────────────────────────────────────
def recommend(user_id, top_n=5):
    song_ids = []

    if user_id in user_sim:
        sims = user_sim[user_id].drop(user_id)
        if not sims.empty:
            most_similar = sims.idxmax()
            peer_songs = set(user_song.columns[user_song.loc[most_similar] > 0])
            your_songs = set(user_song.columns[user_song.loc[user_id] > 0])
            song_ids = list(peer_songs - your_songs)

    # Fallback if no recommendations
    if not song_ids:
        song_ids = df['song_id'].value_counts().head(top_n).index.tolist()

    return get_song_details(song_ids[:top_n])

# ─── Flask API Route ──────────────────────────────────────────────────
@app.route("/recommend", methods=["GET"])
def get_recommendations():
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"error": "Missing user_id"}), 400

    recs = recommend(user_id)
    return jsonify(recs)

# ─── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
