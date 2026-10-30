from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import os

# Ingurune-aldagaia erabiliz alda daiteke (probak egiteko oso erabilgarria da)
URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/powerbank_erreserba",
)

engine = create_engine(
    URL,
    echo=True,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_session():
    with SessionLocal() as session:
        yield session