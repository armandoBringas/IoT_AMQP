#!/usr/bin/env python
import pika
import json
import logging
import sys
import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Any, Dict  # Agregamos las importaciones de typing

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TestProducer:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()

        # Configuración de RabbitMQ
        self.connection = None
        self.channel = None
        self.exchange_name = 'test_exchange'
        self.queue_name = 'test_queue'
        self.routing_key = 'test_routing'
        self.amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

    def connect(self):
        """Establecer conexión con RabbitMQ"""
        try:
            # Crear conexión
            parameters = pika.URLParameters(self.amqp_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("✅ Conexión establecida con RabbitMQ")

            # Configurar exchange y cola
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='direct',
                durable=True
            )

            # Declarar cola con TTL por mensaje
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    'x-max-length': 1000,  # Máximo número de mensajes
                    'x-overflow': 'reject-publish'  # Rechazar mensajes nuevos si la cola está llena
                }
            )

            # Binding
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=self.routing_key
            )

            logger.info("✅ Exchange y Cola configurados correctamente")

        except Exception as e:
            logger.error(f"❌ Error al conectar con RabbitMQ: {str(e)}")
            sys.exit(1)

    def send_test_message(self, message_type: str, content: Any, ttl: int = 30000) -> bool:
        """
        Enviar mensaje de prueba

        Args:
            message_type: Tipo de mensaje (ej: 'test', 'notification', etc)
            content: Contenido del mensaje
            ttl: Tiempo de vida del mensaje en milisegundos (default 30 segundos)
        """
        try:
            # Crear mensaje
            message = {
                "message_id": str(uuid.uuid4()),
                "type": message_type,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "test_info": {
                    "producer_id": "test_producer",
                    "environment": "testing",
                    "version": "1.0.0"
                }
            }

            # Propiedades del mensaje
            properties = pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
                content_type='application/json',
                expiration=str(ttl),  # TTL en milisegundos
                headers={
                    'message_type': message_type,
                    'environment': 'testing'
                },
                priority=5,
                timestamp=int(time.time())
            )

            # Publicar mensaje
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=json.dumps(message, indent=2),
                properties=properties
            )

            logger.info(f"✅ Mensaje enviado: {message['message_id']}")
            logger.info(f"📝 Contenido: {content}")
            logger.info(f"⏱️ TTL: {ttl / 1000} segundos")

            return True

        except Exception as e:
            logger.error(f"❌ Error al enviar mensaje: {str(e)}")
            return False

    def close(self):
        """Cerrar conexión"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("✅ Conexión cerrada correctamente")


def main():
    producer = TestProducer()

    try:
        # Conectar con RabbitMQ
        producer.connect()

        # Lista de mensajes de prueba
        test_messages = [
            {
                "type": "user_action",
                "content": {
                    "user_id": "test_user_1",
                    "action": "login",
                    "timestamp": datetime.now().isoformat()
                },
                "ttl": 60000  # 60 segundos
            },
            {
                "type": "notification",
                "content": {
                    "title": "Test Notification",
                    "body": "This is a test notification message",
                    "priority": "high"
                },
                "ttl": 45000  # 45 segundos
            },
            {
                "type": "system_status",
                "content": {
                    "status": "operational",
                    "memory_usage": "45%",
                    "cpu_usage": "30%"
                },
                "ttl": 30000  # 30 segundos
            }
        ]

        # Enviar mensajes
        logger.info("🚀 Iniciando envío de mensajes de prueba...")
        for msg in test_messages:
            producer.send_test_message(
                message_type=msg["type"],
                content=msg["content"],
                ttl=msg["ttl"]
            )
            time.sleep(1)  # Esperar 1 segundo entre mensajes

        logger.info("✅ Todos los mensajes de prueba han sido enviados")

    except KeyboardInterrupt:
        logger.info("⚠️ Proceso interrumpido por el usuario")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
