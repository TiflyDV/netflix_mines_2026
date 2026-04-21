from fastapi import FastAPI, HTTPException  # Ajout de HTTPException
from pydantic import BaseModel
from db import get_connection
import sqlite3

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
async def createFilm(film: Film):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Film (Nom, Note, DateSortie, Image, Video, Genre_ID)  
            VALUES (?, ?, ?, ?, ?, ?) RETURNING *
            """, (film.nom, film.note, film.dateSortie, film.image, film.video, film.genreId))
        
        res = cursor.fetchone()
        return dict(res) 


@app.get("/films/{id}")
def get_one_film(id: int):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Film WHERE ID = ?", (id,))   
        res = cursor.fetchone()
        
        if res is None:
            raise HTTPException(status_code=404, detail="Film not found")
            
        return dict(res)


@app.get("/films")
def get_films(page: int = 1, per_page: int = 20, genre_id: int | None = None):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        offset = (page - 1) * per_page
        
        count_query = "SELECT COUNT(*) FROM Film"
        count_params = []
        if genre_id is not None:
            count_query += " WHERE Genre_ID = ?"
            count_params.append(genre_id)
            
        cursor.execute(count_query, count_params)
        total_films = cursor.fetchone()[0]

        query = "SELECT * FROM Film"
        params = []
        
        if genre_id is not None:
            query += " WHERE Genre_ID = ?"
            params.append(genre_id)
            
        query += " ORDER BY DateSortie DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)   
        res = cursor.fetchall()
        
        return {
            "data": [dict(row) for row in res],
            "page": page,
            "per_page": per_page,
            "total": total_films
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)