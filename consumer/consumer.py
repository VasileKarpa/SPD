# consumer/consumer.py
import os, json, time
import pika, psycopg2, redis
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Conexões
pg = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT")
)
pg.autocommit = True

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT"))
)

def handle_add(ch, method, properties, body):
    msg = json.loads(body)
    key, val, ts = msg['key_name'], msg['key_value'], msg['timestamp']
    with pg.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kv_store(key, value, last_updated)
            VALUES (%s, %s, %s)
            ON CONFLICT(key) DO UPDATE
              SET value = EXCLUDED.value,
                  last_updated = EXCLUDED.last_updated
              WHERE kv_store.last_updated <= EXCLUDED.last_updated;
            """,
            (key, val, ts)
        )
    if r.get(key) is not None:
        r.set(key, val)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def handle_del(ch, method, properties, body):
    msg = json.loads(body)
    key = msg['key_name']
    ts_str = msg['timestamp']                 # <-- define ts_str
    try:
        ts = datetime.fromisoformat(ts_str)
    except Exception as e:
        print(f"[DEL] timestamp parse error: {ts_str!r} → {e}")
        ts = None

    with pg.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT last_updated FROM kv_store WHERE key=%s', (key,))
        row = cur.fetchone()

    print(f"[DEL] Received delete for {key!r} at {ts!r}; row in DB: {row!r}")

    if ts is not None and row and row['last_updated'] <= ts:
        with pg.cursor() as cur:
            cur.execute('DELETE FROM kv_store WHERE key=%s', (key,))
        # agora elimina também do Redis, fora do cursor
        r.delete(key)
        print(f"[DEL] {key!r} removido de Postgres e Redis")
    else:
        print(f"[DEL] NOT deleted: row is None ou row['last_updated'] > ts")

    ch.basic_ack(delivery_tag=method.delivery_tag)

conn = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        heartbeat=600,
        blocked_connection_timeout=300
    )
)


ch = conn.channel()
ch.queue_declare(queue='add_key', durable=True)
ch.queue_declare(queue='del_key', durable=True)
ch.basic_qos(prefetch_count=50)
ch.basic_consume(queue='add_key', on_message_callback=handle_add)
ch.basic_consume(queue='del_key', on_message_callback=handle_del)

print("[Consumer] Waiting for messages...")
ch.start_consuming()
