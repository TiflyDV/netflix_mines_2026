from fastapi import FastAPI
from pydantic import BaseModel
from db import get_connection
import requests
from faker import Faker

app = FastAPI()


@app.get("/ping")
def ping():
    return {"message": "pong"}

class Film(BaseModel):
    id: int | None = None
    nom: str
    note: float | None = None
    dateSortie: int
    image: str | None = None
    video: str | None = None
    genreId: int | None = None

@app.post("/films")
async def createFilm(film : Film):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO Film (Nom,Note,DateSortie,Image,Video)  
            VALUES('{film.nom}',{film.note},{film.dateSortie},'{film.image}','{film.video}') RETURNING *
            """)
        res = cursor.fetchone()
        print(res)
        return res


@app.get("/films/{id}")
def get_one_film(id: int):
    with get_connection() as conn:
        # Permet de récupérer les résultats sous forme de dictionnaire (clé/valeur)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Utilisation de '?' pour éviter les injections SQL
        cursor.execute("SELECT * FROM Film WHERE ID = ?", (id,))   
        res = cursor.fetchone()
        
        # Renvoie une erreur 404 si le film n'est pas trouvé
        if res is None:
            raise HTTPException(status_code=404, detail="Film not found")
            
        return dict(res)


@app.get("/films")
def get_films(page: int = 1, per_page: int = 20, genre_id: int | None = None):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        offset = (page - 1) * per_page
        
        # 1. Calculer le total réel dynamique
        count_query = "SELECT COUNT(*) FROM Film"
        count_params = []
        if genre_id is not None:
            count_query += " WHERE Genre_ID = ?"
            count_params.append(genre_id)
            
        cursor.execute(count_query, count_params)
        total_films = cursor.fetchone()[0]

        # 2. Récupérer les données avec tri et pagination
        query = "SELECT * FROM Film"
        params = []
        
        if genre_id is not None:
            query += " WHERE Genre_ID = ?"
            params.append(genre_id)
            
        # Ajout du tri par DateSortie décroissante (DESC) comme attendu par les tests
        query += " ORDER BY DateSortie DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)   
        res = cursor.fetchall()
        
        return {
            "data": [dict(row) for row in res], # Convertit les sqlite3.Row en dictionnaires classiques
            "page": page,
            "per_page": per_page,
            "total": total_films
        }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

fake = Faker()

for i in range(1000):
    payload = {
        "nom": fake.name(),
        "note" : fake.random_int(),
        "dataSortie" : fake.year(),
        'image' : fake.image_url(),
        'video' : fake.url()
    }
    res = requests.post('http://localhost:8000/film',json=payload)
    print(res.status_code)