# spotipy
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time


# --------------------------------------------------------------------
# SPOTIFY AUTH
# --------------------------------------------------------------------
CLIENT_ID = "7b29483f671446338c3c3e20e12e58b0"
CLIENT_SECRET = "7a9132cf0e174cf883ec4370fae940fc"

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
)


# --------------------------------------------------------------------
# Ensure songs + albums tables have proper columns
# --------------------------------------------------------------------
def ensure_schema(cur):
    # ----- Simple albums table -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_album_id TEXT UNIQUE,
            album_name TEXT
        )
    """)

    # ----- Ensure songs table has Spotify columns -----
    cur.execute("PRAGMA table_info(songs)")
    existing_cols = {col[1] for col in cur.fetchall()}

    required = {
        "spotify_track_id TEXT",
        "spotify_track_popularity INTEGER",
        "spotify_duration_ms INTEGER",
        "album_id INTEGER",
        "spotify_explicit INTEGER",
        "spotify_release_year INTEGER"
    }

    for col_def in required:
        name = col_def.split()[0]
        if name not in existing_cols:
            print(f"Adding column to songs: {name}")
            cur.execute(f"ALTER TABLE songs ADD COLUMN {col_def}")


# --------------------------------------------------------------------
# Spotify Track Search
# --------------------------------------------------------------------
def fetch_spotify_track(title, artist):
    query = f"track:{title} artist:{artist}"
    try:
        result = sp.search(q=query, type="track", limit=1)
        items = result["tracks"]["items"]
        return items[0] if items else None
    except Exception as e:
        print(f"Error searching Spotify for {title} by {artist}: {e}")
        return None


# --------------------------------------------------------------------
# Insert album if needed, return album_id
# --------------------------------------------------------------------
def get_or_create_album(cur, album):
    spotify_album_id = album["id"]
    album_name = album["name"]

    # Insert only if not already present
    cur.execute("""
        INSERT OR IGNORE INTO albums (spotify_album_id, album_name)
        VALUES (?, ?)
    """, (spotify_album_id, album_name))

    # Retrieve album_id
    cur.execute("SELECT album_id FROM albums WHERE spotify_album_id = ?", (spotify_album_id,))
    row = cur.fetchone()
    return row[0]


# --------------------------------------------------------------------
# Update a song row with Spotify track & album info
# --------------------------------------------------------------------
def update_song(cur, song_id, track_info):
    if track_info is None:
        cur.execute("""
            UPDATE songs
            SET spotify_track_id = NULL,
                spotify_track_popularity = NULL,
                spotify_duration_ms = NULL,
                album_id = NULL,
                spotify_explicit = NULL,
                spotify_release_year = NULL
            WHERE song_id = ?
        """, (song_id,))
        return

    track_id = track_info["id"]
    popularity = track_info["popularity"]
    duration = track_info["duration_ms"]
    explicit_flag = 1 if track_info["explicit"] else 0

    # Minimal album info
    album_info = track_info["album"]
    album_id = get_or_create_album(cur, album_info)

    # Extract release year from album release date
    release_date = album_info.get("release_date")
    if release_date:
        release_year = int(release_date[:4])
    else:
        release_year = None

    cur.execute("""
        UPDATE songs
        SET spotify_track_id = ?,
            spotify_track_popularity = ?,
            spotify_duration_ms = ?,
            album_id = ?,
            spotify_explicit = ?,
            spotify_release_year = ?
        WHERE song_id = ?
    """, (
        track_id,
        popularity,
        duration,
        album_id,
        explicit_flag,
        release_year,
        song_id
    ))


# --------------------------------------------------------------------
# MAIN — Up to 25 songs per run
# --------------------------------------------------------------------
def enrich_songs(db_name="final_project.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    ensure_schema(cur)
    conn.commit()

    # Select 25 unenriched songs
    cur.execute("""
        SELECT s.song_id, s.title, a.name
        FROM songs s
        JOIN artists a ON s.artist_id = a.artist_id
        WHERE s.spotify_track_id IS NULL
        LIMIT 25
    """)

    rows = cur.fetchall()
    if not rows:
        print("All songs already enriched!")
        conn.close()
        return

    print(f"Processing {len(rows)} songs this run...")

    for song_id, title, artist in rows:
        print(f"\nSearching for track: {title} — {artist}")
        track = fetch_spotify_track(title, artist)

        if track:
            print(f" → Found: {track['name']} [{track['id']}]")
        else:
            print(" → No track found")

        update_song(cur, song_id, track)
        conn.commit()

        time.sleep(0.3)  # polite rate limiting

    conn.close()
    print("\nRun complete — run again for the next 25 songs.")

# --------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------
if __name__ == "__main__":
    enrich_songs("final_project.db")
