# backend/app/storage.py
import os
import time
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2 import Error

class Storage:
    def __init__(self):
        # Tenta múltiplas vezes ligar ao Postgres antes de desistir
        attempts = 0
        while True:
            try:
                self.conn = psycopg2.connect(
                    dbname=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    host=os.getenv("POSTGRES_HOST"),
                    port=os.getenv("POSTGRES_PORT", 5432),
                )
                self.conn.autocommit = True
                break
            except OperationalError:
                attempts += 1
                if attempts >= 10:
                    # Depois de 10 falhas, levanta exceção
                    raise
                # Aguarda antes da próxima tentativa
                time.sleep(2)

    def put(self, k: bytes, v: bytes):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kv_store (key, value, last_updated)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key)
                DO UPDATE SET
                  value = EXCLUDED.value,
                  last_updated = CURRENT_TIMESTAMP;
                """,
                (k.decode(), v.decode())
            )

    def get(self, k: bytes):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT value FROM kv_store WHERE key = %s", (k.decode(),))
            row = cur.fetchone()
            return row["value"].encode() if row else None

    def delete(self, k: bytes):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM kv_store WHERE key = %s", (k.decode(),))

    def all(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT key, value, last_updated FROM kv_store ORDER BY key;")
            return cur.fetchall()

    def close(self):
        self.conn.close()
