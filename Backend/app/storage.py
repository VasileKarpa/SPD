# backend/app/storage.py
import os
import time
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

class Storage:
    def __init__(self):
        # Tenta múltiplas vezes ligar ao Postgres antes de desistir
        attempts = 0
        while True:
            try:
                self.conn = psycopg2.connect(
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT", 5432),
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
        # Garante que a tabela existe
        self._ensure_table()

    def _ensure_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kv_store (
                  key          TEXT      PRIMARY KEY,
                  value        TEXT      NOT NULL,
                  last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """ )

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

    def close(self):
        self.conn.close()
