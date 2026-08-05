

# Cursor Auto Accept

Una herramienta para aceptar automáticamente las sugerencias de IA de Cursor.

## Nota Importante

El script `analyze_hover_results.py` es la versión funcional actual para analizar posiciones de botones y coincidencias. Este script:
- Captura una imagen completa de la pantalla
- Analiza posibles coincidencias de botones utilizando coincidencia de plantillas
- Agrupa las coincidencias por posición en el eje X
- Prioriza las coincidencias por confianza y posición en el eje Y
- Genera una visualización que muestra los puntos de calibración y las coincidencias
- Utiliza códigos de colores para distinguir entre diferentes botones (verde, amarillo, rojo)

Otros scripts de calibración se han movido al directorio `_archive`.

## Características

- Compatibilidad con múltiples monitores con calibración por monitor
- Limitación de velocidad (máximo 8 clics por minuto)
- Restauración de la posición del cursor después de los clics
- Calibración automática
- Gestión de procesos (scripts de inicio/parada)
- Registro detallado

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/yourusername/cursor-auto-accept
cd cursor-auto-accept
```

2. Ejecuta el script de configuración:
```bash
./setup.sh
```
Esto hará lo siguiente:
- Creará los directorios necesarios
- Configurar los permisos
- Crear un entorno virtual de Python
- Instalar los paquetes requeridos

## Calibración

Antes del primer uso, debes calibrar el bot para cada monitor donde utilices Cursor:

1. Detén el bot si está en ejecución:
```bash
./stop_clickbot.sh
```

2. Ejecuta el modo de calibración:

   Para todos los monitores:
   ```bash
   source venv/bin/activate
   python cursor_auto_accept.py --capture
   ```

   Para un monitor específico (índice basado en 0):
   ```bash
   python cursor_auto_accept.py --capture --monitor 0  # Primer monitor
   python cursor_auto_accept.py --capture --monitor 1  # Segundo monitor
   ```

3. Sigue los pasos de calibración para cada monitor:
   - Mueve Cursor al monitor objetivo
   - Activa un prompt de IA (para que puedas ver el botón de aceptar)
   - Mueve el mouse sobre el botón de aceptar
   - Mantén el mouse quieto durante 5 segundos
   - Espera el mensaje de confirmación
   - Presiona Enter para continuar al siguiente monitor (si estás calibrando todos)

El bot guardará imágenes separadas del botón de aceptar para cada monitor en:
```
assets/monitor_0/accept_button.png
assets/monitor_1/accept_button.png
...
```

## Uso

### Iniciar el Bot

```bash
./start_clickbot.sh
```

El bot hará lo siguiente:
- Verificará si otra instancia está en ejecución
- Cargará las imágenes de calibración para todos los monitores
- Comenzará a monitorear todas las pantallas
- Comenzará a aceptar los prompts automáticamente

### Detener el Bot

```bash
./stop_clickbot.sh
```

### Monitoreo

El bot registra toda la actividad en `temp/logs/clickbot.log`. Puedes monitorearlo con:
```bash
tail -f temp/logs/clickbot.log
```

## Configuración

El bot tiene varios ajustes integrados:
- Límite de velocidad: 8 clics por minuto
- Umbral de confianza: 0.8 (se requiere una coincidencia del 80%)
- Intervalo de búsqueda: 0.2 segundos
- Intervalo de actualización del registro: 5 segundos

## Solución de Problemas

1. Si el bot no hace clic en un monitor específico:
   - Vuelve a calibrar ese monitor: `python cursor_auto_accept.py --capture --monitor X`
   - Revisa los registros en busca de errores específicos del monitor
   - Asegúrate de que el botón de aceptar de Cursor sea visible en ese monitor

2. Si los clics no son precisos:
   - Vuelve a calibrar con una vista más clara del botón de aceptar
   - Asegúrate de que el botón no esté parcialmente oculto
   - Intenta calibrar en diferentes condiciones de iluminación

3. Si el bot no se inicia:
   - Verifica si otra instancia está en ejecución
   - Comprueba el archivo PID en `temp/clickbot.pid`
   - Asegúrate de que el entorno de Python esté activado

## Estructura de Directorios

```
.
├── assets/                    # Imágenes de calibración
│   ├── monitor_0/            # Primer monitor
│   │   └── accept_button.png
│   └── monitor_1/            # Segundo monitor
│       └── accept_button.png
├── temp/                     # Archivos de ejecución
│   ├── clickbot.pid          # ID del proceso
│   └── logs/                # Archivos de registro
├── cursor_auto_accept.py     # Script principal del bot
├── setup.sh                  # Script de instalación
├── start_clickbot.sh         # Script de inicio
└── stop_clickbot.sh          # Script de parada
```

## Requisitos

- Python 3.8+
- OpenCV
- PyAutoGUI
- MSS (Multi-Screen Shot)
- NumPy
- Pillow

## Licencia

Licencia MIT
