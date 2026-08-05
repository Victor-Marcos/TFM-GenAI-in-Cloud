import os
from dotenv import load_dotenv
from google import genai
import psycopg2
from pgvector.psycopg2 import register_vector

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def get_gemini_client():
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    conn.autocommit = True
    register_vector(conn)
    return conn