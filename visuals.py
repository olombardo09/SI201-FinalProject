import csv
import matplotlib.pyplot as plt
import sqlite3
import numpy as np

colors = ["#e8d8e0","#aebbdb","#dbc4bc","#ecd8d7","#f4a29d",
              "#cad69e","#cbaedb","#d6bf9f","#b4cbe9","#ece6a2"]

def load_csv_data(filename):
    with open(filename) as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        data = list(csv_reader)
        return data
    
# ------------------------------------------------------------
# Generate Plots
# ------------------------------------------------------------
def top_15_artist(filename):
    top_artists = load_csv_data('artist_frequency.csv')
    
    top_artists_sorted = sorted(top_artists, key=lambda x: x[1], reverse=False)[:15]
    artists, counts = zip(*top_artists_sorted)
    counts = [int(c) for c in counts]   # ensure numeric

    plt.barh(artists, counts, color=colors)
    plt.xlim(0, max(counts) + 1)
    plt.xlabel("Artist Count")
    plt.ylabel("Artist Name")
    plt.title("Number of Appearances for an Artist in the Billboard Hot 100")
    plt.tight_layout()
    plt.show()

def artist_playcount_pie(filename):
    plays = load_csv_data('artist_playcounts.csv')

    plays_sorted = sorted(plays, key=lambda x: x[1], reverse=True)[:10]
    name, plays = zip(*plays_sorted)
 
    fig, ax1 = plt.subplots(figsize=(10,5))

    ax1.pie(plays, labels=name, autopct='%1.1f%%', colors=colors, textprops={'fontsize': 6})
    ax1.set_title('Plays per Artist Percent')
    plt.show()

def listeners_v_playcount(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT listeners, playcount
        FROM lastfm_track_stats
    """)
    result = cur.fetchall()
    listeners, playcount = zip(*result)

    # Convert to arrays for filtering/log regression
    x = np.array(listeners)
    y = np.array(playcount)

    # Filter zeros (log scale can't plot them)
    mask = (x > 0) & (y > 0)
    x = x[mask]
    y = y[mask]

    plt.figure(figsize=(8, 6))
    
    # Scatter with transparency
    plt.scatter(x, y, s=15, alpha=0.5)
    plt.xscale("log")
    plt.yscale("log")

    # Trendline in log-space
    m, b = np.polyfit(np.log10(x), np.log10(y), 1)
    plt.plot(x, 10**(m*np.log10(x) + b))

    plt.title("Track Popularity: Last.fm Listeners vs Playcount")
    plt.xlabel("Listeners (log scale)")
    plt.ylabel("Playcount (log scale)")
    plt.tight_layout()
    plt.show()

def explicit_popularity(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT spotify_explicit, AVG(spotify_track_popularity)
        FROM songs
        GROUP BY spotify_explicit
    """)
    result = cur.fetchall()
    explicit, popularity = zip(*result)
    # Convert 0/1 to labels
    labels = ["Non-Explicit" if e == 0 else "Explicit" for e in explicit]

    plt.bar(labels, popularity, color=['skyblue', 'salmon'])
    plt.ylabel("Average Spotify Popularity")
    plt.title("Average Spotify Popularity Score by Explicit Flag")
    plt.show()

def songs_per_year(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT spotify_release_year, COUNT(*)
        FROM songs
        WHERE spotify_release_year IS NOT NULL
        GROUP BY spotify_release_year
        ORDER BY spotify_release_year
     """)
    result = cur.fetchall()
    years, counts = zip(*result)

    # Convert years to decades
    decades = [(year // 10) * 10 for year in years]

    # Aggregate counts per decade
    unique_decades = sorted(set(decades))
    counts_by_decade = [sum(count for y, count in zip(years, counts) if (y // 10) * 10 == decade) 
                        for decade in unique_decades]

    # Plot
    plt.figure(figsize=(10,6))
    plt.bar(unique_decades, counts_by_decade, width=10, color=colors, edgecolor='black')
    plt.xlabel("Decade")
    plt.ylabel("Number of Songs")
    plt.title("Number of Songs Released per Decade in the Hot 100")
    plt.show()

# ------------------------------------------------------------
# Run script
# ------------------------------------------------------------
if __name__ == "__main__":
    conn = sqlite3.connect("final_project.db")
    top = top_15_artist('artist_frequency.csv')
    plays = artist_playcount_pie('artist_playcounts.csv')
    print(listeners_v_playcount(conn))
    print(explicit_popularity(conn))
    print(songs_per_year(conn))
