import csv
import matplotlib.pyplot as plt

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

    fig, ax1 = plt.subplots(figsize=(10,5))
    
    ax1.barh(artists, counts, color=colors)
    ax1.set_xlabel("Artist Count")
    ax1.set_ylabel("Artist Name")
    ax1.set_title("Number of Appearances for an Artist in the Billboard Hot 100")
    
    ax1.set_xlim(left=0)

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


# ------------------------------------------------------------
# Run script
# ------------------------------------------------------------
if __name__ == "__main__":
    top = top_15_artist('artist_frequency.csv')
    plays = artist_playcount_pie('artist_playcounts.csv')