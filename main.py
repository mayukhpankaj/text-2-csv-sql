from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import get_connection
from etl import run_etl
from LLM import generate_text2sql
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading ETL API",
    description="FastAPI app for CSV → SQLite ETL and analytics",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    try:
        conn = get_connection()
        result = run_etl(conn)
        conn.commit()
        print("ETL process completed successfully on server startup")
    except Exception as e:
        print(f"ETL process failed on startup: {str(e)}")
    finally:
        conn.close()


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Generate SQL from user query
        text2sql_result = generate_text2sql(request.query)
        
        if not text2sql_result["query_bool"]:
            return {"response": "I couldn't generate a valid SQL query for your request.", "type": "text"}
        
        sql_query = text2sql_result["sql_query"]
        
        # Execute the generated SQL query
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute(sql_query)
        rows = cur.fetchall()
        
        # Convert rows to dictionaries for JSON response
        columns = [description[0] for description in cur.description]
        logger.debug(f"DEBUG: Converting {len(rows)} rows to dictionaries with columns: {columns}")
        result = [dict(zip(columns, row)) for row in rows]
        # logger.debug(f"DEBUG: Converted result: {result}")
        
        conn.close()
        
        return {"response": result, "type": "dataframe"}
        
    except Exception as e:
        return {"response": f"Error executing query: {str(e)}", "type": "text"}





