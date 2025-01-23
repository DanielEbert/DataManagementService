from __future__ import annotations

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, insert
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import HSTORE

app = FastAPI()

# to be replaced when we go to production
DATABASE_URL = "postgresql://admin:admin@localhost:5432" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# doesnt work
# needed to connec to DB and run: CREATE EXTENSION IF NOT EXISTS hstore;
# with engine.connect() as con:
#     con.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS hstore;')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Measurement(Base):
    __tablename__ = 'measurements'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    # collection_sha = Column(String, index=True)
    path = Column(String)

class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class MeasurementToCollectionLink(Base):
    __tablename__ = 'measurement_collection_links'
    id = Column(Integer, primary_key=True, index=True)
    measurement_name = Column(String, index=True)
    collection_name = Column(String)

class MeasurementMetadata(Base):
    __tablename__ = 'measurement_metadata'
    id = Column(Integer, primary_key=True, index=True)
    measurement_name = Column(String, unique=True, nullable=False)
    meta = Column(MutableDict.as_mutable(HSTORE))


class MeasurementSchema(BaseModel):
    name: str
    path: str

class CollectionSchema(BaseModel):
    name: str

class MeasurementToCollectionLinkSchema(BaseModel):
    measurement_name: str
    collection_name: str

class MeasurementMetadataSchema(BaseModel):
    measurement_name: str
    key: str
    value: str


@app.post('/add_measurement')
async def add_measurement(measurement: MeasurementSchema, db: Session = Depends(get_db)):
    db_measurement = Measurement(**measurement.model_dump())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement

@app.get('/measurement/{name}')
async def get_measurement(name: str, db: Session = Depends(get_db)):
    return db.query(Measurement).filter(Measurement.name == name).all()

@app.get('/add_collection')
async def add_collection(collection: CollectionSchema, db: Session = Depends(get_db)):
    db_collection = Collection(**collection.model_dump())
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return db_collection

@app.get("/collection/{name}")
async def get_collection(name: str, db: Session = Depends(get_db)):
    return db.query(Collection).filter(Collection.name == name).all()

@app.post('/add_measurement_metadata')
async def add_measurement_metadata(meta: MeasurementMetadataSchema, db: Session = Depends(get_db)):
    db_meta = db.query(MeasurementMetadata).filter(MeasurementMetadata.measurement_name == meta.measurement_name).first()
    if db_meta is None:
        db_meta = MeasurementMetadata(measurement_name=meta.measurement_name, meta={meta.key: meta.value})
        db.add(db_meta)
    else:
        db_meta.meta[meta.key] = meta.value

    db.commit()
    db.refresh(db_meta)
    return db_meta

@app.get("/measurement_metadata/{name}")
async def get_measurement_metadata(name: str, db: Session = Depends(get_db)):
    return db.query(MeasurementMetadata).filter(Collection.name == name).all()

# @app.get('/collection_measurements/{collection_name}')
# async def get_collection_measurements(collection_name: str):
#     with DB() as db:
#         collection_id = db.get(
#             f'SELECT * FROM collections WHERE name = :name',
#             {'name': collection_name}
#         )[0]['id']
# 
#         return db.get(
#             f'SELECT * FROM collection_measurements WHERE collection_id = :collection_id',
#             {'collection_id': collection_id}
#         )
# 
# @app.post("/link_measurement_to_collection")
# async def add_collection(link: MeasurementToCollectionLinkSchema):
#     with DB() as db:
#         measurement_id = db.get(
#             f'SELECT * FROM measurements WHERE name = :name',
#             {'name': link.measurement_name}
#         )[0]['id']
#         collection_id = db.get(
#             f'SELECT * FROM collections WHERE name = :name',
#             {'name': link.collection_name}
#         )[0]['id']
# 
#         db.run(
#             f'INSERT INTO collection_measurements (measurement_id, collection_id) VALUES (:measurement_id, :collection_id)',
#             {'measurement_id': measurement_id, 'collection_id': collection_id}
#         )
#     return 200
# 

Base.metadata.create_all(engine)
