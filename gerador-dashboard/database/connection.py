from sqlalchemy import create_engine
import pandas as pd

DB_CONFIG = {
    "usuario": "postgres",
    "senha": "postgres",
    "host": "localhost",
    "porta": "5432",
    "banco": "jojo",
}

connection_url = (
    f"postgresql+psycopg2://{DB_CONFIG['usuario']}:{DB_CONFIG['senha']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['porta']}/{DB_CONFIG['banco']}"
)

engine = create_engine(connection_url)

query = "SELECT * FROM usuario"

df = pd.read_sql_query(query, engine)