import duckdb
import os

DB_PATH = "data/processed/stocks.duckdb"


def get_connection():
    return duckdb.connect(DB_PATH)

def run_query(query, params=None):
    con = get_connection()

    try:
        if params is not None:
            df = con.execute(query, params).df()
        else:
            df = con.execute(query).df()
    finally:
        con.close()

    return df