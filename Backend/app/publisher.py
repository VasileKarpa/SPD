import pika
from pika import BasicProperties
import os

def publish(queue: str, payload: str):
    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        heartbeat=0            # desativa heartbeats do cliente
    )
    conn = pika.BlockingConnection(params)
    ch   = conn.channel()
    ch.queue_declare(queue=queue, durable=True)
    ch.basic_publish(
        exchange='',
        routing_key=queue,
        body=payload,
        properties=BasicProperties(delivery_mode=2)
    )
    conn.close()
