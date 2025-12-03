# last fm
import requests
import sqlite3
import time

API_KEY = 'c7ccd0d60d79ca261defce5a541879b1'
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

# ------------------------------------------------------------
# Create table to store Last.fm track stats
# ------------------------------------------------------------
def create_lastfm_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lastfm_track_stats (
    song_id INTEGER PRIMARY KEY,
    artist_id INTEGER,
    listeners INTEGER,
    playcount INTEGER,
    FOREIGN KEY(song_id) REFERENCES songs(song_id),
    FOREIGN KEY(artist_id) REFERENCES artists(artist_id)
    )
    """)
    conn.commit()

# ------------------------------------------------------------
# Fetch listeners + playcount from Last.fm (JSON)
# ------------------------------------------------------------
def fetch_lastfm_track_info(artist_name, track_title):
    params = {
        "method": "track.getInfo",
        "api_key": API_KEY,
        "artist": artist_name,
        "track": track_title,
        "format": "json"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "track" not in data:
            return None, None

        track = data["track"]

        listeners = track.get("listeners")
        playcount = track.get("playcount")

        if listeners is None or playcount is None:
            return None, None

        return int(listeners), int(playcount)

    except Exception as e:
        print(f"Error fetching data for {artist_name} - {track_title}: {e}")
        return None, None

# ------------------------------------------------------------
# Populate up to 25 new items into lastfm_track_stats
# ------------------------------------------------------------
def populate_lastfm_stats(db_path="final_project.db", limit=25):
    conn = sqlite3.connect(db_path)
    create_lastfm_table(conn)
    cur = conn.cursor()

    cur.execute("""
        SELECT s.song_id, s.artist_id, s.title, a.name
        FROM songs s
        JOIN artists a ON s.artist_id = a.artist_id
        LEFT JOIN lastfm_track_stats l ON s.song_id = l.song_id
        WHERE l.song_id IS NULL
        LIMIT ?;
    """, (limit,))

    rows = cur.fetchall()

    if not rows:
        print("All tracks already processed — no new items to add.")
        conn.close()
        return

    for song_id, artist_id, title, artist_name in rows:
        print(f"Fetching: {artist_name} — {title}")

        listeners, playcount = fetch_lastfm_track_info(artist_name, title)

        if listeners is None:
            print("   → No data returned. Skipping.")
            continue

        cur.execute("""
            INSERT INTO lastfm_track_stats (song_id, artist_id, listeners, playcount)
            VALUES (?, ?, ?, ?);
        """, (song_id, artist_id, listeners, playcount))

        conn.commit()

        print(f" --> Saved: listeners={listeners}, playcount={playcount}")

        time.sleep(0.3)

    conn.close()
    print("\nRun complete — up to 25 new Last.fm rows inserted.\n")

# ------------------------------------------------------------
# Run script
# ------------------------------------------------------------
if __name__ == "__main__":
    populate_lastfm_stats(limit=25)