#!/usr/bin/env python
import pika
import json
import logging
import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Cargar variables de entorno y mostrar configuración
load_dotenv()
amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@127.0.0.1:5672/')
print(f"Intentando conectar a: {amqp_url}")
print(f"Directorio actual: {os.getcwd()}")

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('producer_debug.log')
    ]
)
logger = logging.getLogger(__name__)


class MessageProducer:
    def __init__(self):
        """Inicializar el productor"""
        self.connection = None
        self.channel = None
        self.exchange_name = 'mi_exchange'
        self.queue_name = 'mi_cola'
        self.routing_key = 'mi_routing_key'
        self.message_count = 0
        self.amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@127.0.0.1:5672/')
        logger.debug(f"Inicializando productor con URL: {self.amqp_url}")

    def connect(self) -> None:
        """Establecer conexión con RabbitMQ"""
        try:
            logger.debug("Iniciando conexión con RabbitMQ...")
            parameters = pika.URLParameters(self.amqp_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Conexión establecida con RabbitMQ")

            self.setup_exchange()
            self.setup_queue()

        except Exception as e:
            logger.error(f"Error al conectar con RabbitMQ: {str(e)}", exc_info=True)
            sys.exit(1)

    def setup_exchange(self) -> None:
        """Configurar el exchange"""
        logger.debug(f"Declarando exchange: {self.exchange_name}")
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='direct',
            durable=True
        )
        logger.debug(f"Exchange {self.exchange_name} declarado exitosamente")

    def setup_queue(self) -> None:
        """Configurar la cola y el binding"""
        logger.debug(f"Declarando cola: {self.queue_name}")
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 86400000,
                'x-max-length': 10000
            }
        )

        logger.debug(f"Creando binding entre {self.exchange_name} y {self.queue_name}")
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key=self.routing_key
        )
        logger.debug("Binding creado exitosamente")

    def publish_message(self, content: Any, priority: Optional[int] = None) -> bool:
        """Publicar un mensaje en el exchange"""
        try:
            if not self.connection or self.connection.is_closed:
                logger.debug("Conexión cerrada, reconectando...")
                self.connect()

            message = {
                "id": str(uuid.uuid4()),
                "timestamp": int(datetime.now().timestamp()),
                "content": content,
                "producer_id": os.getenv('PRODUCER_ID', 'default_producer')
            }

            self.message_count += 1

            properties = pika.BasicProperties(
                delivery_mode=2,  # mensaje persistente
                content_type='application/json',
                message_id=str(uuid.uuid4()),
                timestamp=int(datetime.now().timestamp()),
                priority=priority if priority is not None else 0
            )

            logger.debug(f"Propiedades del mensaje: {properties}")

            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=json.dumps(message),
                properties=properties
            )

            logger.info(f"""
            Mensaje #{self.message_count} publicado:
            ID: {message['id']}
            Contenido: {content}
            """)

            return True

        except Exception as e:
            logger.error(f"Error al publicar mensaje: {str(e)}", exc_info=True)
            return False

    def close(self) -> None:
        """Cerrar conexiones"""
        try:
            if self.connection and not self.connection.is_closed:
                logger.debug("Cerrando conexión...")
                self.connection.close()
                logger.info("Conexión cerrada correctamente")

        except Exception as e:
            logger.error(f"Error al cerrar la conexión: {str(e)}", exc_info=True)


def main():
    """Función principal"""
    producer = MessageProducer()

    try:
        # Publicar mensaje simple
        producer.publish_message("¡Hola Mundo!")

        # Publicar mensaje con prioridad
        producer.publish_message("Mensaje urgente", priority=9)

        # Publicar batch de mensajes
        for i in range(5):
            mensaje = {
                "tipo": "notificacion",
                "usuario": f"usuario_{i}",
                "mensaje": f"Mensaje {i}"
            }
            producer.publish_message(mensaje)

    except KeyboardInterrupt:
        logger.info("Operación interrumpida por el usuario")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
