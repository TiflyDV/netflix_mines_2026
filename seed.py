import json
from db import get_connection, init_db

with open("movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# Extraire tous les genres uniques (premier genre de chaque film)
genres = set()
for movie in movies:
    genre_str = movie.get("Genre", "")
    if genre_str:
        first_genre = genre_str.split(",")[0].strip()
        if first_genre:
            genres.add(first_genre)

conn = get_connection()
init_db(conn)

# Vider les tables avant de seed (ordre respectant les FK)
conn.execute("DELETE FROM Film")
conn.execute("DELETE FROM Genre")
conn.execute("DELETE FROM Genre_Utilisateur")
conn.execute("DELETE FROM Utilisateur")
conn.execute("DELETE FROM sqlite_sequence")

# 1. Insérer les genres
print(f"Insertion de {len(genres)} genres...")
genre_map = {}  # nom -> id
for genre in sorted(genres):
    cursor = conn.execute("INSERT INTO Genre (Type) VALUES (?)", (genre,))
    genre_map[genre] = cursor.lastrowid

# 2. Insérer les films
print(f"Insertion de {len(movies)} films...")
for movie in movies:
    genre_str = movie.get("Genre", "")
    first_genre = genre_str.split(",")[0].strip() if genre_str else ""
    genre_id = genre_map.get(first_genre)

    release_date = movie.get("Release_Date", "")
    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    note_str = movie.get("Vote_Average", "")
    note = float(note_str) if note_str else None

    conn.execute(
        "INSERT INTO Film (Nom, Note, DateSortie, Image, Video, Genre_ID) VALUES (?, ?, ?, ?, ?, ?)",
        (
            movie.get("Title", ""),
            note,
            year,
            movie.get("Poster_Url", ""),
            None,
            genre_id,
        ),
    )

conn.commit()
conn.close()
print("Seed terminé.")
