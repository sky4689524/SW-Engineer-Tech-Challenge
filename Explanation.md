# Floy Software Challenge

This document briefly explains the scripts and instructions how to run them.

## Scripts
1. client.py
* This script simulates a DICOM client that processes and sends DICOM metadata to the StoreSCP server. It handles the extraction of metadata and communicates with the server using HTTP.
2. scp.py
* The StoreSCP server receives DICOM files from the client using the DICOM protocol (C-STORE). The received DICOM metadata is added to a queue for processing and further transmission to the FastAPI server.
3. server.py
* The FastAPI server receives DICOM metadata from the StoreSCP server and stores it in an SQLite database. It exposes an API endpoint to handle the metadata using POST requests.
4. view_database.py
* This script reads the SQLite database and displays its content (DICOM metadata) using Pandas. Use this to verify the correct storage of data.
5. test_client.py
* Unit tests for the client-side logic. This includes tests for sending DICOM metadata and ensuring correct processing.
6. test_server.py
* Unit tests for the FastAPI server. This verifies that the server processes incoming metadata and stores it correctly in the database.

## How to Use

1. Install Dependencies

Make sure to install all required libraries by running:
``` bash
pip install -r requirements.txt
```

2. Start the FastAPI Server

Launch the FastAPI server to handle metadata storage:

```bash
uvicorn server:app --reload
```

3. Run the Client

Execute the client to send DICOM data to the StoreSCP server:

```bash
python client.py
```

4. View the Database

After running the client, view the stored DICOM metadata in the SQLite database:
```bash
python view_database.py
```

5. Run Unit Tests

* To test the client:
```bash
python -m unittest -v test_client.py
```

* To test the server:
```bash
python -m unittest -v test_server.py
```

6. Generate Diagrams

To view the system architecture and communication diagrams, check the PlantUML files inside the diagrams directory.