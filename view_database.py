import sqlite3
import pandas as pd


def display_database_contents():
    """
    Connects to the SQLite database 'dicom_series.db' and retrieves all records 
    from the 'series' table. It prints the contents of the table to validate that 
    the the extracted information is correctly stored in the database.
    """

    conn = sqlite3.connect('dicom_series.db')

    query = "SELECT * FROM series"

    df = pd.read_sql_query(query, conn)

    conn.close()

    print(df.to_string(index=False))


display_database_contents()
