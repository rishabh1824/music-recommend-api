import os
import pandas as pd
import mysql.connector

# ─── 1. Connect to MySQL ────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="login"
)

# ─── 2. Fetch listening history ─────────────────────────────────────
query = "SELECT user_id, song_id FROM listening_log"
df = pd.read_sql(query, conn)

# ─── 3. Compute output path in this script’s folder ─────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "listening_data.csv")

# ─── 4. Export to CSV in recommendations/ ───────────────────────────
df.to_csv(output_path, index=False)
print(f"Exported listening_data.csv to {output_path}")

# ─── 5. Close connection ────────────────────────────────────────────
conn.close()
