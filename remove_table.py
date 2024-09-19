import sqlite3

def clear_database_contents():
    """
    Connects to the SQLite database 'dicom_series.db' and removes all records 
    from the 'series' table.
    """

    conn = sqlite3.connect('dicom_series.db')
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM series")
    conn.commit() 

    conn.close()

clear_database_contents()
