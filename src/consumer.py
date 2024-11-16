#!/usr/bin/env python
# Modifica el inicio de consumer.py agregando estos prints de debug
import pika
import json
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

# Cargar variables de entorno y mostrar configuración
load_dotenv()
amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@127.0.0.1:5672/')
print(f"Intentando conectar a: {amqp_url}")
print(f"Directorio actual: {os.getcwd()}")
print(f"Variables de entorno cargadas: {dict(os.environ)}")

# Configurar logging con más detalle
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para más detalle
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('consumer_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('consumer.log')
    ]
)


class MessageConsumer:
    def __init__(self):
        """Inicializar el consumidor"""
        self.connection = None
        self.channel = None
        self.exchange_name = 'mi_exchange'
        self.queue_name = 'mi_cola'
        self.routing_key = 'mi_routing_key'
        self.message_count = 0

        # Obtener URL de conexión de variables de entorno
        self.amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

    def connect(self) -> None:
        """Establecer conexión con RabbitMQ"""
        try:
            # Crear conexión
            parameters = pika.URLParameters(self.amqp_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Conexión establecida con RabbitMQ")

            # Configurar exchange y cola
            self.setup_exchange()
            self.setup_queue()

        except Exception as e:
            logger.error(f"Error al conectar con RabbitMQ: {str(e)}")
            sys.exit(1)

    def setup_exchange(self) -> None:
        """Configurar el exchange"""
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='direct',
            durable=True
        )

    def setup_queue(self) -> None:
        """Configurar la cola y el binding"""
        # Declarar cola con configuraciones específicas
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 86400000,  # TTL: 24 horas
                'x-max-length': 10000  # Máximo 10000 mensajes
            }
        )

        # Crear binding entre exchange y cola
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key=self.routing_key
        )

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Procesar el mensaje recibido

        Args:
            message: Mensaje a procesar

        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            # Incrementar contador de mensajes
            self.message_count += 1

            # Obtener timestamp actual
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Registrar información del mensaje
            logger.info(f"""
            Mensaje #{self.message_count} procesado:
            Timestamp: {timestamp}
            ID: {message.get('message_id', 'N/A')}
            Contenido: {message.get('content', 'N/A')}
            Metadata: {message.get('metadata', {})}
            """)

            # Aquí puedes agregar tu lógica de procesamiento
            # Por ejemplo: guardar en base de datos, enviar notificaciones, etc.

            return True

        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return False

    def handle_message(self, channel: pika.channel.Channel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        """
        Manejar mensaje recibido de RabbitMQ

        Args:
            channel: Canal de comunicación
            method: Método de entrega
            properties: Propiedades del mensaje
            body: Contenido del mensaje
        """
        try:
            # Decodificar mensaje
            message = json.loads(body.decode())

            # Registrar recepción del mensaje
            logger.info(f"""
            Mensaje recibido:
            Exchange: {method.exchange}
            Routing Key: {method.routing_key}
            Priority: {getattr(properties, 'priority', 0)}
            """)

            # Procesar mensaje
            success = self.process_message(message)

            if success:
                # Confirmar procesamiento exitoso
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Mensaje procesado exitosamente")
            else:
                # Rechazar mensaje en caso de error de procesamiento
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning("Error en procesamiento, mensaje reencolado")

        except json.JSONDecodeError:
            logger.error("Error decodificando mensaje JSON")
            # Rechazar mensaje mal formateado
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error en callback: {str(e)}")
            # Rechazar mensaje y reencolar
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self) -> None:
        """Iniciar el consumo de mensajes"""
        try:
            # Establecer conexión
            self.connect()

            # Configurar QoS (Quality of Service)
            self.channel.basic_qos(prefetch_count=1)

            # Configurar el consumo
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.handle_message
            )

            logger.info(f"""
            Iniciando consumo de mensajes:
            Cola: {self.queue_name}
            Exchange: {self.exchange_name}
            Routing Key: {self.routing_key}
            """)
            logger.info("Presiona CTRL+C para detener el consumidor")

            # Iniciar consumo
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Deteniendo el consumidor...")
            self.stop_consuming()

        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
            self.stop_consuming()

    def stop_consuming(self) -> None:
        """Detener el consumo de mensajes y cerrar conexiones"""
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection:
                self.connection.close()
            logger.info("Consumidor detenido correctamente")

        except Exception as e:
            logger.error(f"Error al detener el consumidor: {str(e)}")


def main():
    """Función principal"""
    consumer = MessageConsumer()
    consumer.start_consuming()


if __name__ == "__main__":
    main()
