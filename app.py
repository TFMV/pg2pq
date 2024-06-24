from fastapi import FastAPI, HTTPException
import duckdb
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables from .env file if it exists (for local development)
if os.path.exists('.env'):
    load_dotenv()

# Configure environment variables for database connections and GCS
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
GCS_MOUNT_PATH = os.getenv("GCS_MOUNT_PATH", "/mnt/gcs")
EXPORT_DIR = os.path.join(GCS_MOUNT_PATH, "exported_data")

@app.post("/export")
async def export_data():
    try:
        # Create DuckDB connection
        duckdb_conn = duckdb.connect(database=':memory:')

        # Install and load PostgreSQL extension
        duckdb_conn.execute("INSTALL postgres;")
        duckdb_conn.execute("LOAD postgres;")
        
        # Define PostgreSQL connection string
        postgres_conn_str = f"dbname={POSTGRES_DB} user={POSTGRES_USER} host={POSTGRES_HOST} password={POSTGRES_PASSWORD} port={POSTGRES_PORT}"
        
        # Attach PostgreSQL database
        duckdb_conn.execute(f"ATTACH '{postgres_conn_str}' AS postgres_db (TYPE POSTGRES, READ_ONLY);")
        
        # Get the list of tables in the PostgreSQL database
        tables = duckdb_conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'").fetchall()

        # Export each table to Parquet format
        for table in tables:
            table_name = table[0]
            output_path = os.path.join(EXPORT_DIR, f"{table_name}.parquet")
            duckdb_conn.execute(f"COPY (SELECT * FROM postgres_db.{table_name}) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000);")

        return {"message": "Database exported successfully to GCS"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
