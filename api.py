from __future__ import annotations

from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
import sqlite3

db_path = "api.db"

app = FastAPI()


class DB:
    def __init__(self, db_name: str = db_path):
        self.db_name = db_name

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def run(self, query: str, params: dict = None):
        if params is None:
            params = {}
        try:
            self.cursor.execute(query, params)
        except sqlite3.Error as e:
            raise HTTPException(status_code=400, detail=f"Database error: {e}")

    def get(self, query: str, params: dict = None):
        if params is None:
            params = {}
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise HTTPException(status_code=400, detail=f"Database error: {e}")


with DB() as db:
    db.run("""\
CREATE TABLE IF NOT EXISTS measurements(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    path TEXT
);
""")
    db.run("""\
CREATE TABLE IF NOT EXISTS sequences(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)           
""")

    db.run("""\
CREATE TABLE IF NOT EXISTS sequence_measurements(
    measurement_id INTEGER,
    sequence_id INTEGER,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id),
    FOREIGN KEY (sequence_id) REFERENCES sequence(id),
    PRIMARY KEY (measurement_id, sequence_id)
)""")
    db.run('CREATE INDEX IF NOT EXISTS idx_sequence_id ON sequence_measurements (sequence_id);')


class Measurement(BaseModel):
    name: str
    path: str

class Sequence(BaseModel):
    name: str

class MeasurementToSequenceLink(BaseModel):
    measurement_name: str
    sequence_name: str


@app.post("/add_measurement")
async def add_measurement(measurement: Measurement):
    with DB() as db:
        db.run(
            f'INSERT INTO measurements (name, path) VALUES (:name, :path)',
            {'name': measurement.name, 'path': measurement.path}
        )
    return 200

@app.get("/measurement/{name}")
async def get_measurement(name: str):
    with DB() as db:
        rows = db.get(
            f'SELECT * FROM measurements WHERE name = :name',
            {'name': name}
        )
        return rows

@app.post("/add_sequence")
async def add_sequence(sequence: Sequence):
    with DB() as db:
        db.run(
            f'INSERT INTO sequences (name) VALUES (:name)',
            {'name': sequence.name}
        )
    return 200

@app.get("/sequence/{name}")
async def get_sequence(name: str):
    with DB() as db:
        rows = db.get(
            f'SELECT * FROM sequences WHERE name = :name',
            {'name': name}
        )
        return rows


@app.get('/sequence_measurements/{sequence_name}')
async def get_sequence_measurements(sequence_name: str):
    with DB() as db:
        sequence_id = db.get(
            f'SELECT * FROM sequences WHERE name = :name',
            {'name': sequence_name}
        )[0]['id']

        return db.get(
            f'SELECT * FROM sequence_measurements WHERE sequence_id = :sequence_id',
            {'sequence_id': sequence_id}
        )

@app.post("/link_measurement_to_sequence")
async def add_sequence(link: MeasurementToSequenceLink):
    with DB() as db:
        measurement_id = db.get(
            f'SELECT * FROM measurements WHERE name = :name',
            {'name': link.measurement_name}
        )[0]['id']
        sequence_id = db.get(
            f'SELECT * FROM sequences WHERE name = :name',
            {'name': link.sequence_name}
        )[0]['id']

        db.run(
            f'INSERT INTO sequence_measurements (measurement_id, sequence_id) VALUES (:measurement_id, :sequence_id)',
            {'measurement_id': measurement_id, 'sequence_id': sequence_id}
        )
    return 200
