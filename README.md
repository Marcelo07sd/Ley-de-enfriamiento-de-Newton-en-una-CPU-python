# Ley-de-enfriamiento-de-Newton-en-una-CPU-python
# 🖥️ Monitor de Temperatura CPU: Modelo Teórico vs Real

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Graphing-orange)
![OpenWeather](https://img.shields.io/badge/OpenWeather-API-lightblue)
![LibreHardwareMonitor](https://img.shields.io/badge/LibreHardwareMonitor-Integration-green)

Una aplicación en Python que monitorea la temperatura de la CPU en tiempo real y compara los datos reales con un modelo teórico basado en la **Ley de Enfriamiento de Newton**.

## 🌟 Características

- **📊 Monitoreo en Tiempo Real**: Lectura continua de temperatura desde LibreHardwareMonitor
- **🔬 Modelo Matemático**: Implementación de la Ley de Enfriamiento de Newton
- **🎯 Calibración Automática**: Calcula automáticamente el coeficiente de enfriamiento `k`
- **📈 Visualización Avanzada**: Gráficos en tiempo real con matplotlib
- **🌡️ Datos Meteorológicos**: Integración con OpenWeather API para temperatura ambiente
- **⚡ Alta Precisión**: Actualizaciones cada segundo con validación de datos

## 🧮 Fundamentos Matemáticos

El proyecto implementa la **Ley de Enfriamiento de Newton**:

\[
\frac{dT}{dt} = k(T(t) - T_a)
\]

**Solución general:**
\[
T(t) = (T_0 - T_a)e^{kt} + T_a
\]

**Cálculo del coeficiente k:**
\[
k = \frac{1}{t} \ln\left( \frac{T(t) - T_a}{T_0 - T_a} \right)
\]

## 🚀 Instalación

### Prerrequisitos
- Python 3.8 o superior
- LibreHardwareMonitor ejecutándose en `http://localhost:8085`
- API Key de [OpenWeatherMap](https://openweathermap.org/api)

### 1. Clonar el repositorio
git clone https://github.com/tu-usuario/cpu-temperature-monitor.git
cd cpu-temperature-monitor}}]


2. Instalar dependencias
bash
pip install -r requirements.txt
3. Configurar API Key
Edita el archivo monitor.py y reemplaza:

python
API_KEY = "tu_api_key_aqui"
CITY = "TuCiudad,PE"  # Ejemplo: "Lima,PE"
4. Configurar LibreHardwareMonitor
Descarga LibreHardwareMonitor

Ejecuta y habilita el servidor web en el puerto 8085

Verifica que http://localhost:8085/data.json esté accesible

🎮 Uso
Ejecución básica
bash
python monitor.py
Proceso de calibración
La aplicación inicia con 20 segundos de calibración

Ejecuta un stress test (CPU-Z, Prime95, etc.) durante este período

El sistema calculará automáticamente el coeficiente k

Comienza el monitoreo en tiempo real

Interpretación del gráfico
🔴 Línea Roja: Temperatura real de la CPU

🟢 Línea Verde: Predicción del modelo teórico

🔵 Línea Azul: Temperatura ambiente

📊 Panel superior: Métricas en tiempo real

📁 Estructura del Proyecto
text
cpu-temperature-monitor/
├── monitor.py              # Aplicación principal
├── requirements.txt        # Dependencias
├── README.md              # Documentación
└── images/                # Capturas de pantalla
    ├── calibration.png
    ├── realtime_graph.png
    └── comparison.png
🛠️ Dependencias
txt
requests>=2.28.0
numpy>=1.21.0
matplotlib>=3.5.0
Instalar todas las dependencias:

bash
pip install requests numpy matplotlib
🔧 Configuración
Parámetros ajustables en el código:
python
REFRESH_INTERVAL = 1.0     # Segundos entre lecturas
CALIBRATION_TIME = 20      # Tiempo de calibración (segundos)
MAX_POINTS = 300           # Puntos máximos en gráfico
MAX_TEMP_REAL = 90.0       # Temperatura máxima realista
Variables del modelo:
k_coeff: Coeficiente de enfriamiento [1/s]

T_amb: Temperatura ambiente [°C]

T_inicial_modelo: Temperatura inicial del modelo [°C]

📊 Ejemplo de Salida
text
🚀 INICIANDO MONITOR DE TEMPERATURA CPU
==================================================

🔧 CALIBRACIÓN AUTOMÁTICA (20s)
💡 INSTRUCCIONES: Ejecuta un stress test ahora (CPU-Z, Prime95, etc.)
==================================================
📊 Temperatura inicial: 45.20°C
🌡️ Temperatura ambiente: 25.50°C

⏱️ Iniciando calibración...
   ⏰ 20s restantes | CPU: 45.20°C
   ⏰ 15s restantes | CPU: 68.35°C
   ...
   
📈 Temperatura final: 72.15°C
📊 Delta total: 26.95°C

✅ CALIBRACIÓN COMPLETADA
   • Coeficiente k: 0.045200 [1/s]
   • T inicial modelo: 72.15°C
   • Tiempo de equilibrio: 66s
==================================================
🎯 Aplicaciones
🔬 Investigación: Validación de modelos térmicos

🎓 Educación: Enseñanza de ecuaciones diferenciales aplicadas

💻 Overclocking: Monitoreo avanzado de temperaturas

🛠️ Diagnóstico: Detección de problemas de refrigeración

🤝 Contribuciones
¡Las contribuciones son bienvenidas! Por favor:

Haz fork del proyecto

Crea una rama para tu feature (git checkout -b feature/AmazingFeature)

Commit tus cambios (git commit -m 'Add AmazingFeature')

Push a la rama (git push origin feature/AmazingFeature)

Abre un Pull Request

📝 Licencia
Distribuido bajo la Licencia MIT. Ver LICENSE para más información.

⚠️ Limitaciones
Requiere LibreHardwareMonitor ejecutándose

La precisión depende de la calibración inicial

Sensible a cambios bruscos en carga de CPU

Temperatura ambiente debe ser estable para mejores resultados

📞 Soporte
Si encuentras algún problema:

Verifica que LibreHardwareMonitor esté ejecutándose

Confirma tu API Key de OpenWeather

Revisa que Python 3.8+ esté instalado

Abre un issue en el repositorio
