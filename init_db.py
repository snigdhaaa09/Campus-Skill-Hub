from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

from app import app
from config import Config
from extensions import db
import models


def create_database_if_needed():
    host = Config.MYSQL_HOST
    port = Config.MYSQL_PORT
    user = Config.MYSQL_USER
    password = quote_plus(Config.MYSQL_PASSWORD or "")
    database = Config.MYSQL_DATABASE

    if not all([host, port, user, database]):
        raise RuntimeError(
            "Missing MySQL settings. Copy .env.example to .env and fill in "
            "MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE."
        )

    server_uri = f"mysql+mysqldb://{user}:{password}@{host}:{port}/"
    engine = create_engine(server_uri)

    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database}`"))
        connection.commit()

    print(f"Database '{database}' is ready.")


def create_tables():
    with app.app_context():
        db.create_all()
        print("Database tables created.")


if __name__ == "__main__":
    create_database_if_needed()
    create_tables()
