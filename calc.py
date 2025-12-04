# calculations
import sqlite3
import csv

def calculate_avg_duration(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(spotify_duration_ms)
        FROM songs
    """)

    # Get the average
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
# Write output into a file
# ------------------------------------------------------------
def write_all_outputs(avg_ms, avg_plays, avg_listeners, artist_playcounts, avg_artist_ranks, artist_freq, album_freq, filename="all_results.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write headers
        writer.writerow(["Metric", "Value"])

        # Single-value metrics
        writer.writerow(["average_track_duration_ms", avg_ms])
        writer.writerow(["average_playcount", avg_plays])
        writer.writerow(["average_lisenters", avg_listeners])

        # Artist Playcounts (Top 15)
        writer.writerow([])
        writer.writerow(["Top Artists by Total Playcount"])
        writer.writerow(["artist", "total_playcount"])
        writer.writerows(artist_playcounts)

        # Average Rank
        writer.writerow([])
        writer.writerow(["Top Artists by Average Rank"])
        writer.writerow(["artist", "avg_rank"])
        writer.writerows(avg_artist_ranks)

        # Artist Frequency
        writer.writerow([])
        writer.writerow(["Artist Frequency in Hot 100"])
        writer.writerow(["artist", "frequency"])
        writer.writerows(artist_freq)

        # Album Frequency
        writer.writerow([])
        writer.writerow(["Album Frequency in Hot 100"])
        writer.writerow(["album", "frequency"])
        writer.writerows(album_freq)

    print(f"Saved results to {filename}")

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
    write_all_outputs(avg_ms, avg_plays, avg_listeners, artist_playcounts, avg_artist_ranks, artist_freq, album_freq, filename="all_results.csv")
    