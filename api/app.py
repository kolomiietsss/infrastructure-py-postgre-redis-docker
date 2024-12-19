from fastapi import FastAPI, Query
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379)

conn = psycopg2.connect(
    host="db",
    database="app_db",
    user="postgres",
    password="postgres",
    cursor_factory=RealDictCursor
)

@app.get("/data/{key}")
def get_data(key: str):
    cached_data = redis_client.get(key)
    if cached_data:
        return {"source": "cache", "data": json.loads(cached_data)}

    cursor = conn.cursor()
    cursor.execute("SELECT value FROM data WHERE key = %s", (key,))
    result = cursor.fetchone()

    if result:
        redis_client.set(key, json.dumps(result))
        return {"source": "database", "data": result}
    else:
        return {"error": "Key not found"}

@app.post("/data/")
def save_data(key: str = Query(...), value: str = Query(...)):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (key, value) VALUES (%s, %s)", (key, value))
    conn.commit()

    redis_client.set(key, json.dumps({"key": key, "value": value}))
    return {"message": "Data saved successfully"}
