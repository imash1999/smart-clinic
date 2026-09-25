import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL","postgresql://clinic:clinic123@localhost:5432/clinic")


# clinic-пользователь, clinic123-пароль, localhost- PostgreSQL находится на компьютере, 5432-порт, clinic-название бызы 
engine = create_engine(DATABASE_URL) # создает объект, через который SQLAlchemy будет подключаться к PosqgreSQL

SessionLocal = sessionmaker(
    bind=engine,
    autoflush = False,
    autocommit = False
)

Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()