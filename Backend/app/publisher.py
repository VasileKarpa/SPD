import os
import pika
from pika import BasicProperties

# 1) Inicializa ligação e canal UMA SÓ VEZ, quando o módulo é importado
_params = pika.ConnectionParameters(
    host=os.getenv("RABBITMQ_HOST"),
    port=int(os.getenv("RABBITMQ_PORT")),
    heartbeat=600,               # heartbeat alongado
    blocked_connection_timeout=300
)
_conn = pika.BlockingConnection(_params)
_channel = _conn.channel()

# 2) Declara as filas DURANTE O STARTUP (idempotente)
_channel.queue_declare(queue='add_key', durable=True)
_channel.queue_declare(queue='del_key', durable=True)

def publish(queue: str, payload: str):
    """
    Publica numa fila já declarada, usando o canal persistente.
    """
    _channel.basic_publish(
        exchange='',
        routing_key=queue,
        body=payload,
        properties=BasicProperties(delivery_mode=2)
    )
