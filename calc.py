# calculations
import sqlite3
import csv

def calculate_avg_duration(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(spotify_duration_ms)
        FROM songs
                """)
    result = cur.fetchone()[0]
    return result

def calculate_avg_plays(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(playcount)
        FROM lastfm_track_stats
                """)
    result = cur.fetchone()[0]
    return result

def calculate_avg_listeners(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(listeners)
        FROM lastfm_track_stats
                """)
    result = cur.fetchone()[0]
    return result

def artist_play_counts(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT artists.name, SUM(lastfm_track_stats.playcount) AS total_playcount
        FROM artists
        JOIN lastfm_track_stats 
        ON artists.artist_id = lastfm_track_stats.artist_id
        GROUP BY artists.name
        ORDER BY total_playcount DESC
        LIMIT 15
    """)
    result = cur.fetchall()
    return result

def avg_artist_rank(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT artists.name,
        AVG(songs.rank) AS avg_rank
        FROM artists
        JOIN songs ON artists.artist_id = songs.artist_id
        GROUP BY artists.name
        ORDER BY avg_rank
        LIMIT 15
    """)
    result = cur.fetchall()
    return result

def top_artist_frequency(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT artists.name,
        COUNT(*) AS frequency
        FROM songs
        JOIN artists
        ON songs.artist_id = artists.artist_id
        WHERE songs.rank <= 100
        GROUP BY artists.name
        ORDER BY frequency DESC
        LIMIT 15
    """)
    result = cur.fetchall()
    return result

def top_album_frequency(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT albums.album_name,
        COUNT(*) AS frequency
        FROM songs
        JOIN albums
        ON songs.album_id = albums.album_id
        WHERE songs.rank <= 100
        GROUP BY albums.album_name
        ORDER BY frequency DESC
        LIMIT 15
    """)
    result = cur.fetchall()
    return result

# ------------------------------------------------------------
# Write each output into individual files
# ------------------------------------------------------------
def write_artist_playcounts(results, filename="artist_playcounts.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["artist", "total_playcount"])
        writer.writerows(results)

def write_avg_artist_ranks(results, filename="avg_artist_ranks.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["artist", "avg_rank"])
        writer.writerows(results)

def write_artist_frequency(results, filename="artist_frequency.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["artist", "frequency"])
        writer.writerows(results)

def write_album_frequency(results, filename="album_frequency.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["album", "frequency"])
        writer.writerows(results)

def write_summary(avg_ms, avg_plays, avg_listeners, filename="summary_stats.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["average_track_duration_ms", avg_ms])
        writer.writerow(["average_playcount", avg_plays])
        writer.writerow(["average listeners", {avg_listeners}])

# ------------------------------------------------------------
# Run script
# ------------------------------------------------------------
if __name__ == "__main__":
    conn = sqlite3.connect("final_project.db")
    avg_ms = calculate_avg_duration(conn)
    avg_plays = calculate_avg_plays(conn)
    avg_listeners = calculate_avg_listeners(conn)
    artist_playcounts = artist_play_counts(conn)
    avg_artist_ranks = avg_artist_rank(conn)
    artist_freq = top_artist_frequency(conn)
    album_freq = top_album_frequency(conn)

    conn.close()

    # print(f"Average Spotify track duration: {avg_ms:.2f} ms")
    # print(f"\n Average Track Play Count: {avg_plays:.2f}")
    # print(f'\n Average Track Play Count Per Artist: {artist_playcounts}')
    # print(f'\n Average Billboard Rank Per Artist: {avg_artist_ranks}')
    # print(f'\n Artist Frequency in the Billboard Hot 100: {artist_freq}')
    # print(f'\n Album Frequency in the Billboard Hot 100: {album_freq}')
    
    write_summary(avg_ms, avg_plays, avg_listeners)
    write_artist_playcounts(artist_playcounts)
    write_avg_artist_ranks(avg_artist_ranks)
    write_artist_frequency(artist_freq)
    write_album_frequency(album_freq)