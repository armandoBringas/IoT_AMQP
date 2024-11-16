# Proyecto AMQP con Python y RabbitMQ

Este proyecto implementa un sistema de mensajería utilizando el protocolo AMQP (Advanced Message Queuing Protocol) con Python y RabbitMQ. Incluye implementaciones de productores y consumidores tanto para uso general como para pruebas.

## 📋 Requisitos Previos

- Python 3.4 o superior
- Docker Desktop
- pip (gestor de paquetes de Python)
- Git (opcional, para control de versiones)

## 🚀 Estructura del Proyecto

```
proyecto-amqp/
├── src/
│   ├── __init__.py
│   ├── producer.py          # Productor principal
│   ├── consumer.py          # Consumidor principal
│   └── tests/              # Código de pruebas
│       ├── __init__.py
│       ├── test_producer.py  # Productor para pruebas
│       └── test_consumer.py  # Consumidor para pruebas
├── .env                    # Variables de entorno (no subir a git)
├── .env.example           # Ejemplo de variables de entorno
├── requirements.txt       # Dependencias del proyecto
└── README.md             # Este archivo
```

## ⚙️ Configuración del Entorno

1. **Clonar el repositorio** (si estás usando git):
   ```batch
   git clone <url-del-repositorio>
   cd proyecto-amqp
   ```

2. **Crear y activar entorno virtual**:
   ```batch
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```batch
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   ```batch
   copy .env.example .env
   ```
   Editar `.env` con tus configuraciones:
   ```env
   RABBITMQ_URL=amqp://guest:guest@localhost:5672/
   PRODUCER_ID=my_producer
   ```

5. **Iniciar RabbitMQ con Docker**:
   ```batch
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
   ```

## 💻 Uso

### Sistema Principal

1. **Iniciar el Consumidor**:
   ```batch
   python src/consumer.py
   ```

2. **Iniciar el Productor**:
   ```batch
   python src/producer.py
   ```

### Sistema de Pruebas

1. **Iniciar el Consumidor de Pruebas**:
   ```batch
   python src/tests/test_consumer.py
   ```

2. **Iniciar el Productor de Pruebas**:
   ```batch
   python src/tests/test_producer.py
   ```

## 🔍 Monitoreo

1. **Interfaz Web de RabbitMQ**:
   - URL: http://localhost:15672
   - Usuario: guest
   - Contraseña: guest

2. **Características Monitoreables**:
   - Estado de las colas
   - Mensajes en tránsito
   - Conexiones activas
   - Estadísticas de rendimiento

## 📝 Detalles de Implementación

### Sistema Principal
- Implementa un sistema básico de mensajería
- Mensajes persistentes
- Manejo de reconocimientos (ACK)
- Logging básico

### Sistema de Pruebas
- TTL configurable por mensaje
- Diferentes tipos de mensajes de prueba
- Logging mejorado con emojis
- Visualización detallada de mensajes
- Manejo específico por tipo de mensaje

## 🛠️ Características de los Mensajes

### Mensajes de Prueba
1. **User Action**:
   - Información de login
   - TTL: 60 segundos

2. **Notification**:
   - Mensajes de notificación
   - TTL: 45 segundos

3. **System Status**:
   - Estado del sistema
   - TTL: 30 segundos

## 🔧 Mantenimiento

### Logs
- Los logs se guardan en:
  - `producer.log`
  - `consumer.log`
  - Salida estándar (stdout)

### Limpieza
```batch
# Detener contenedor de RabbitMQ
docker stop rabbitmq
docker rm rabbitmq

# Limpiar archivos de log
del *.log
```

## 🚨 Solución de Problemas

1. **Error de Conexión a RabbitMQ**:
   - Verificar que Docker está corriendo
   - Verificar puertos 5672 y 15672
   - Comprobar credenciales en .env

2. **Error en Python**:
   - Verificar entorno virtual activo
   - Reinstalar dependencias
   - Verificar versión de Python

## 👥 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.