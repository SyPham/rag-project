import pandas as pd
import pyodbc
import os

def load_data():
    conn = pyodbc.connect(os.getenv("SQL_CONNECTION"))

    query = """
    SELECT Id, Title, Content, Department
    FROM Documents
    """

    df = pd.read_sql(query, conn)

    return df