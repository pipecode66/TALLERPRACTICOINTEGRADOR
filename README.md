# Sistema de Reservas de Hotel 🏨

## Descripción
Sistema completo de gestión de reservas hoteleras desarrollado en Python con Flask. Incluye funcionalidades de reserva, gestión de habitaciones, autenticación de usuarios y un sistema completo de métricas y análisis de calidad.

## Características Principales 🌟

### Módulo de Reservas
- Búsqueda de habitaciones por fecha y tipo
- Validación de disponibilidad en tiempo real
- Tres categorías de habitaciones: Simple, Doble y Suite
- Sistema de precios dinámicos

### Sistema de Usuarios
- Registro e inicio de sesión seguros
- Gestión de perfiles de usuario
- Historial de reservas
- Autenticación mediante tokens

### Panel de Métricas
- Dashboard visual con indicadores clave
- Análisis de tendencias
- Métricas de calidad y rendimiento
- Generación de reportes diarios

## Tecnologías Utilizadas 💻

- **Backend**: Python 3.13+ con Flask
- **Base de Datos**: SQLite con SQLAlchemy
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **JavaScript**: ES6+ para interacciones dinámicas
- **Testing**: Pytest para pruebas automatizadas
- **Análisis**: Pandas y Matplotlib para métricas

## Requisitos del Sistema 📋

```
Python 3.13 o superior
pip (gestor de paquetes de Python)
Git
```

## Instalación 🚀

1. Clonar el repositorio:
```bash
git clone https://github.com/pipecode66/TALLERPRACTICOINTEGRADOR.git
cd TALLERPRACTICOINTEGRADOR
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Unix/macOS
.\venv\Scripts\activate   # En Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Inicializar la base de datos:
```bash
flask --app app.py init-db
```

5. Ejecutar la aplicación:
```bash
flask --app app.py run --debug
```

## Estructura del Proyecto 📁

```
HELYNOTA/
├── app.py                  # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── helynota/              # Módulo principal
│   ├── __init__.py        # Configuración de Flask
│   ├── models.py          # Modelos de la base de datos
│   ├── routes.py          # Rutas de la API
│   └── seed.py            # Datos iniciales
├── templates/             # Plantillas HTML
├── static/               # Archivos estáticos
├── dashboards/           # Dashboards de métricas
├── tests/               # Pruebas automatizadas
└── metrics/             # Sistema de métricas
```

## Módulos Principales 📊

### Sistema de Reservas
- Gestión completa del ciclo de reserva
- Validación automática de disponibilidad
- Confirmación por correo electrónico
- Sistema de pagos simulado

### Panel de Control
- Visualización de métricas en tiempo real
- Seguimiento de ocupación
- Análisis de satisfacción del cliente
- Reportes personalizables

### Sistema de Métricas
- 8 indicadores clave de rendimiento
- Análisis de tendencias
- Detección temprana de problemas
- Generación automática de informes

## Testing y Calidad 🧪

El proyecto incluye:
- Pruebas unitarias completas
- Análisis de código estático
- Matriz de trazabilidad
- Plan de pruebas IEEE 829
- Cálculo de métricas RPN

## Contribuciones 🤝

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia 📄

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.

## Contacto 📧

Brayan Osorio - [https://github.com/pipecode66](https://github.com/pipecode66)

Link del Proyecto: [https://github.com/pipecode66/TALLERPRACTICOINTEGRADOR](https://github.com/pipecode66/TALLERPRACTICOINTEGRADOR)