#!/usr/bin/env python
import pika
import json
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TestConsumer:
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
        self.message_count = 0

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

            # Declarar cola
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    'x-max-length': 1000,
                    'x-overflow': 'reject-publish'
                }
            )

            # Binding
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=self.routing_key
            )

            # Configurar QoS
            self.channel.basic_qos(prefetch_count=1)

            logger.info("✅ Exchange y Cola configurados correctamente")

        except Exception as e:
            logger.error(f"❌ Error al conectar con RabbitMQ: {str(e)}")
            sys.exit(1)

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Procesar mensaje recibido

        Args:
            message: Mensaje a procesar
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            self.message_count += 1

            # Extraer información del mensaje
            message_id = message.get('message_id', 'N/A')
            message_type = message.get('type', 'N/A')
            content = message.get('content', {})
            timestamp = message.get('timestamp', 'N/A')
            test_info = message.get('test_info', {})

            # Registrar información del mensaje
            logger.info(f"""
📨 Mensaje #{self.message_count} recibido:
├── ID: {message_id}
├── Tipo: {message_type}
├── Timestamp: {timestamp}
├── Test Info:
│   ├── Producer: {test_info.get('producer_id', 'N/A')}
│   ├── Environment: {test_info.get('environment', 'N/A')}
│   └── Version: {test_info.get('version', 'N/A')}
└── Contenido: {json.dumps(content, indent=2)}
            """)

            # Procesamiento específico según el tipo de mensaje
            if message_type == "user_action":
                logger.info(f"👤 Procesando acción de usuario: {content.get('action')}")
            elif message_type == "notification":
                logger.info(f"🔔 Procesando notificación: {content.get('title')}")
            elif message_type == "system_status":
                logger.info(f"🖥️ Procesando estado del sistema: {content.get('status')}")
            else:
                logger.info(f"📝 Procesando mensaje genérico tipo: {message_type}")

            return True

        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {str(e)}")
            return False

    def handle_message(self, ch, method, properties, body):
        """Callback para procesar mensajes recibidos"""
        try:
            # Decodificar mensaje
            message = json.loads(body.decode())

            # Mostrar propiedades del mensaje
            logger.debug(f"""
📦 Propiedades del mensaje:
├── Exchange: {method.exchange}
├── Routing Key: {method.routing_key}
├── Priority: {getattr(properties, 'priority', 0)}
└── Headers: {getattr(properties, 'headers', {})}
            """)

            # Procesar mensaje
            if self.process_message(message):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug("✅ Mensaje procesado y confirmado")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning("⚠️ Error en procesamiento, mensaje reencolado")

        except json.JSONDecodeError:
            logger.error("❌ Error decodificando mensaje JSON")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"❌ Error en callback: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Iniciar el consumo de mensajes"""
        try:
            # Establecer conexión
            self.connect()

            # Configurar el consumo
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.handle_message
            )

            logger.info(f"""
🚀 Iniciando consumo de mensajes:
├── Cola: {self.queue_name}
├── Exchange: {self.exchange_name}
└── Routing Key: {self.routing_key}
            """)
            logger.info("⌛ Esperando mensajes. Presiona CTRL+C para salir")

            # Iniciar consumo
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("\n⚠️ Deteniendo el consumidor...")
            self.stop_consuming()

        except Exception as e:
            logger.error(f"❌ Error en el consumidor: {str(e)}")
            self.stop_consuming()

    def stop_consuming(self):
        """Detener el consumo de mensajes y cerrar conexiones"""
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection:
                self.connection.close()
            logger.info("✅ Consumidor detenido correctamente")

        except Exception as e:
            logger.error(f"❌ Error al detener el consumidor: {str(e)}")


def main():
    consumer = TestConsumer()
    consumer.start_consuming()


if __name__ == "__main__":
    main()
