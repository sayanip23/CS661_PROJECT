"""
utils/database.py

Database connection manager for DuckDB.
Automatically initializes the database from CSV if it doesn't exist,
and provides read-only connections for safe concurrent Dash callbacks.
"""

import os
import duckdb
import pandas as pd
from utils.config import DB_PATH, CSV_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def init_db():
    """
    Self-healing trigger: Checks if the database table exists.
    If missing (e.g., right after a fresh 'git pull'), it automatically 
    creates the database and imports the CSV file in read-write mode.
    """
    # Ensure the data/processed/ folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Open temporarily in read-write mode (read_only=False) just to initialize
    con = duckdb.connect(DB_PATH, read_only=False)
    try:
        # Check if table already exists to avoid redundant imports
        tables = con.execute("SHOW TABLES;").fetchall()
        table_names = [t[0] for t in tables]

        if "clean_stock_data" not in table_names:
            logger.info("Database table missing! Auto-importing CSV into DuckDB...")
            if not os.path.exists(CSV_PATH):
                logger.error(f"Cannot initialize database: Missing source file '{CSV_PATH}'.")
                raise FileNotFoundError(
                    f"Cannot initialize database: Missing source file '{CSV_PATH}'."
                )
            
            con.execute(f"""
                CREATE TABLE clean_stock_data AS 
                SELECT * FROM '{CSV_PATH}';
            """)
            logger.info("DuckDB database successfully built and ready!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        con.close()


# Run initialization immediately the moment this module is imported!
init_db()


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a connection to the DuckDB database.
    Uses read_only=True to allow concurrent read access across multiple Dash 
    callbacks without throwing file-lock exceptions.
    """
    try:
        return duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        logger.error(f"Failed to connect to DuckDB: {e}")
        raise


def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """
    Executes a SQL query against the DuckDB database and returns a Pandas DataFrame.
    Automatically closes the connection when execution completes.
    Returns an empty DataFrame if the query fails.
    """
    try:
        con = get_connection()
    except Exception:
        return pd.DataFrame()
        
    try:
        if params is not None:
            df = con.execute(query, params).df()
        else:
            df = con.execute(query).df()
        return df
    except Exception as e:
        logger.error(f"Query execution failed: {e}\nQuery: {query}")
        return pd.DataFrame()
    finally:
        con.close()