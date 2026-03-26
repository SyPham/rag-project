import pyodbc
import os

def get_connection():
    return pyodbc.connect(
        os.getenv("SQL_CONNECTION"),
        autocommit=True
    )