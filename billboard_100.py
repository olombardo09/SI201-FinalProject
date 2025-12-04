# Billboard
import sqlite3
from bs4 import BeautifulSoup
import requests
import re

STATUS_TOKENS = {"NEW", "RE-ENTRY", "REENTRY", "RE ENTRY", "RE-\nENTRY"}

# -------------------------------------------------------------------
# Cleaning function for artist names
# -------------------------------------------------------------------
def clean_artist_name(raw):
    """
    Normalize Billboard artist strings into clean main-artist names.
    Smart ungluing + colon handling.
    """

    if not raw:
        return raw

    s = raw.strip()

    # Remove everything after a colon (":")
    # Billboard often formats like: "Artist: Person1, Person2..."
    s = re.sub(r":.*$", "", s).strip()

    # Replace common collaboration separators with a single "&"
    separators = [
        r"[Ff]eaturing", r"[Ff]eat\.", r"[Ff]eat",
        r"[Ww]ith", r"&", r",", r"/"
    ]
    for sep in separators:
        s = re.sub(sep, " & ", s)

    # Smart ungluing for Billboard's glued words
    unglue_keywords = ("Featuring", "Feat", "With", "And")

    def smart_unglue(match):
        before = match.group(1)
        after = match.group(2)
        if any(after.startswith(k) for k in unglue_keywords):
            return f"{before} {after}"
        return before + after

    s = re.sub(r"([a-z])([A-Z][a-z]+)", smart_unglue, s)

    # Normalize spaces
    s = re.sub(r"\s*&\s*", " & ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Return only first (main) artist
    main_artist = s.split(" & ")[0].strip()

    return main_artist

# -------------------------------------------------------------------
# Scrape Billboard Hot 100
# -------------------------------------------------------------------
def scrape_billboard():
    url = "https://www.billboard.com/charts/hot-100/"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    rows = soup.find_all("div", class_="o-chart-results-list-row-container")

    songs = []

    for row in rows:

        # ---- GET TITLE ----
        title_tag = row.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else None

        # ---- GET RANK ----
        rank_span = row.find("span")
        rank_text = rank_span.get_text(strip=True) if rank_span else None
        rank = int(rank_text) if rank_text and rank_text.isdigit() else None

        # ---- GET ARTIST ----
        artist = None

        # Try parent first (Billboard changes layout often)
        if title_tag:
            parent = title_tag.find_parent()
            for span in parent.find_all("span", class_="c-label"):
                txt = span.get_text(strip=True)
                txt_up = txt.upper()
                if txt.isdigit() or txt_up in STATUS_TOKENS or len(txt) < 2:
                    continue
                artist = txt
                break

        # Fallback
        if not artist:
            for span in row.find_all("span", class_="c-label"):
                txt = span.get_text(strip=True)
                txt_up = txt.upper()
                if txt.isdigit() or txt_up in STATUS_TOKENS or len(txt) < 2:
                    continue
                artist = txt
                break

        if rank and title and artist:
            songs.append((rank, title, artist))

    return songs

# -------------------------------------------------------------------
# Store Billboard data in SQLite (normalized: artists + songs)
# -------------------------------------------------------------------
def store_billboard_data(db_name):
    all_songs = scrape_billboard()

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    # ---- CREATE TABLES ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            song_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            title TEXT,
            artist_id INTEGER,
            UNIQUE(title, artist_id),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)

    # ---- FETCH EXISTING ROWS ----
    cur.execute("""
        SELECT s.title, a.name
        FROM songs s JOIN artists a ON s.artist_id = a.artist_id
    """)
    existing = set(cur.fetchall())

    # ---- CLEAN + FILTER NEW SONGS ----
    new_songs = []
    for rank, title, raw_artist in all_songs:
        artist = clean_artist_name(raw_artist)
        if (title, artist) not in existing:
            new_songs.append((rank, title, artist))

    # Insert at most 25 new rows
    next_batch = new_songs[:25]

    # ---- INSERT INTO DATABASE ----
    for rank, title, artist in next_batch:

        cur.execute("INSERT OR IGNORE INTO artists (name) VALUES (?)", (artist,))
        cur.execute("SELECT artist_id FROM artists WHERE name = ?", (artist,))
        artist_id = cur.fetchone()[0]

        cur.execute("""
            INSERT OR IGNORE INTO songs (rank, title, artist_id)
            VALUES (?, ?, ?)
        """, (rank, title, artist_id))

    conn.commit()
    conn.close()

    print(f"Inserted {len(next_batch)} new songs.")

# -------------------------------------------------------------------
# RUN SCRIPT
# -------------------------------------------------------------------
if __name__ == "__main__":
    store_billboard_data("final_project.db")
    