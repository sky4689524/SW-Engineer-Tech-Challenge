from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Define the schema for the incoming request
class SeriesData(BaseModel):
    PatientID: str
    PatientName: str
    StudyInstanceUID: str
    SeriesInstanceUID: str
    InstanceInSeries: int

# Create the SQLite database and table (if not already existing)
def init_db():
    conn = sqlite3.connect('dicom_series.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series (
            SeriesInstanceUID TEXT PRIMARY KEY,
            PatientID TEXT,
            PatientName TEXT,
            StudyInstanceUID TEXT,
            InstanceInSeries INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.post("/series")
async def receive_series(data: SeriesData):
    """Endpoint to receive DICOM series data and store it in the database."""
    try:
        conn = sqlite3.connect('dicom_series.db')
        cursor = conn.cursor()

        # Check if the series with the given SeriesInstanceUID already exists
        cursor.execute('SELECT * FROM series WHERE SeriesInstanceUID = ?', (data.SeriesInstanceUID,))
        existing_series = cursor.fetchone()

        if existing_series:
            existing_instances = existing_series[4]  # InstanceInSeries
            if data.InstanceInSeries != existing_instances:
                 # Update the series information if the instance count has changed
                cursor.execute('''
                    UPDATE series
                    SET PatientID = ?, PatientName = ?, StudyInstanceUID = ?, InstanceInSeries = ?
                    WHERE SeriesInstanceUID = ?
                ''', (data.PatientID, data.PatientName, data.StudyInstanceUID, data.InstanceInSeries, data.SeriesInstanceUID))
                conn.commit()
                message = f"Updated series {data.SeriesInstanceUID} with new instance count."
            else:
                message = f"Series {data.SeriesInstanceUID} already exists with the same instance count. No update needed."
        else:
            # Insert the new series into the database if it doesn't exist
            cursor.execute('''
                INSERT INTO series (SeriesInstanceUID, PatientID, PatientName, StudyInstanceUID, InstanceInSeries)
                VALUES (?, ?, ?, ?, ?)
            ''', (data.SeriesInstanceUID, data.PatientID, data.PatientName, data.StudyInstanceUID, data.InstanceInSeries))
            conn.commit()
            message = f"Inserted new series {data.SeriesInstanceUID}."

        conn.close()

        return {"status": "success", "message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store data: {e}")
