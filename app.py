#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor CPU: Temperatura Real vs Tendencia Teórica
Versión mejorada con calibración automática de k y visualización en tiempo real
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import time
import threading
from datetime import datetime
from math import log, isfinite
import warnings
from collections import deque

# Configurar matplotlib para evitar warnings
matplotlib.use('TkAgg')  # Backend estable
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
plt.rcParams.update({'font.size': 10, 'figure.autolayout': True})

# ================= CONFIGURACIÓN =================
API_KEY = "81a4eddaa79f14641e7fb8f9038b9cce"
CITY = "Lima,PE"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
LHM_URL = "http://localhost:8085/data.json"

REFRESH_INTERVAL = 1.0    # segundos entre lecturas
CALIBRATION_TIME = 20     # tiempo para calibrar k (segundos)
MAX_TEMP_REAL = 90.0      # temperatura máxima realista
MIN_TEMP_REAL = 20.0      # temperatura mínima realista
MAX_POINTS = 300          # máximo de puntos en memoria
TIMEOUT_API = 2.0         # timeout para requests
# ==================================================

class CPUMonitor:
    """Clase principal para el monitor de CPU"""
    
    def __init__(self):
        # Datos compartidos (thread-safe con deque)
        self.tiempos = deque(maxlen=MAX_POINTS)
        self.temps_cpu_reales = deque(maxlen=MAX_POINTS)
        self.temps_modelo = deque(maxlen=MAX_POINTS)
        
        # Parámetros del modelo
        self.T_amb = 25.0
        self.k_coeff = None
        self.T_inicial_modelo = None
        self.tiempo_inicio = None
        
        # Control de threads
        self.running = False
        self.lock = threading.RLock()
        
        # Elementos del gráfico
        self.fig = None
        self.ax = None
        self.lines = {}
        self.text_info = None
        
    def _parse_temp_value(self, value):
        """Parsea y valida un valor de temperatura"""
        if value is None:
            return None
        try:
            temp = float(str(value).replace("°C", "").strip())
            # Validar rango realista
            if MIN_TEMP_REAL <= temp <= MAX_TEMP_REAL:
                return temp
            return None
        except (ValueError, TypeError):
            return None
    
    def leer_cpu_temp(self):
        """Lee temperatura de CPU desde LibreHardwareMonitor"""
        try:
            response = requests.get(LHM_URL, timeout=TIMEOUT_API)
            response.raise_for_status()
            data = response.json()
            
            temperatures = []
            
            def extract_temps(node):
                """Extrae temperaturas recursivamente"""
                if isinstance(node, dict):
                    # Buscar valores de temperatura
                    value = self._parse_temp_value(node.get("Value"))
                    text = str(node.get("Text", "")).lower()
                    
                    if value is not None and any(keyword in text for keyword in 
                                               ["cpu", "package", "core", "processor"]):
                        temperatures.append(value)
                    
                    # Recursión en children
                    for key, val in node.items():
                        if isinstance(val, (dict, list)):
                            extract_temps(val)
                            
                elif isinstance(node, list):
                    for item in node:
                        extract_temps(item)
            
            extract_temps(data)
            
            # Retornar la temperatura más alta encontrada
            return max(temperatures) if temperatures else None
            
        except Exception as e:
            print(f"⚠️  Error leyendo CPU temp: {e}")
            return None
    
    def leer_temp_ambiente(self):
        try:
            response = requests.get(URL, timeout=TIMEOUT_API)
            response.raise_for_status()
            temp = float(response.json()["main"]["temp"])
            return temp   # quitar validación de rango
        except Exception as e:
            print(f"⚠️  Error leyendo temp ambiente: {e}")
            return 25.0

    
    def calibrar_coeficiente_k(self):
        """Calibra el coeficiente k durante período de estrés"""
        print(f"\n🔧 CALIBRACIÓN AUTOMÁTICA ({CALIBRATION_TIME}s)")
        print("💡 INSTRUCCIONES: Ejecuta un stress test ahora (CPU-Z, Prime95, etc.)")
        print("=" * 60)
        
        # Leer temperatura ambiente
        self.T_amb = self.leer_temp_ambiente()
        
        # Primera lectura
        T1 = self.leer_cpu_temp()
        if T1 is None:
            print("❌ No se pudo leer temperatura inicial. Usando valor por defecto.")
            T1 = 60.0
        
        print(f"📊 Temperatura inicial: {T1:.2f}°C")
        print(f"🌡️  Temperatura ambiente: {self.T_amb:.2f}°C")
        print("\n⏱️  Iniciando calibración...")
        
        # Recopilar temperaturas durante calibración
        temperaturas_calibracion = []
        
        for i in range(CALIBRATION_TIME, 0, -1):
            temp_actual = self.leer_cpu_temp()
            
            # Usar última temperatura válida si falla la lectura
            if temp_actual is None:
                if temperaturas_calibracion:
                    temp_actual = temperaturas_calibracion[-1]
                else:
                    temp_actual = T1
            
            temperaturas_calibracion.append(temp_actual)
            
            # Mostrar progreso
            if i % 5 == 0 or i <= 3:
                print(f"   ⏰ {i:2d}s restantes | CPU: {temp_actual:.2f}°C")
            
            time.sleep(1)
        
        # Calcular T2 promediando las últimas mediciones
        T2 = np.mean(temperaturas_calibracion[-5:]) if temperaturas_calibracion else T1
        
        print(f"\n📈 Temperatura final: {T2:.2f}°C")
        print(f"📊 Delta total: {T2-T1:.2f}°C")
        
        # Calcular coeficiente k usando ley de enfriamiento de Newton
        try:
            if abs(T1 - self.T_amb) < 0.1 or abs(T2 - self.T_amb) < 0.1:
                # Evitar división por cero
                self.k_coeff = 0.05
                print("⚠️  Diferencia de temperatura muy pequeña. Usando k por defecto.")
            else:
                ratio = (T2 - self.T_amb) / (T1 - self.T_amb)
                if ratio <= 0:
                    ratio = 0.01
                
                k_raw = -(1 / CALIBRATION_TIME) * log(ratio)
                # Limitar k a valores razonables
                self.k_coeff = max(0.001, min(0.8, k_raw))
                
        except (ValueError, ZeroDivisionError):
            self.k_coeff = 0.05
            print("⚠️  Error en cálculo de k. Usando valor por defecto.")
        
        # Establecer temperatura inicial del modelo
        self.T_inicial_modelo = T2
        
        print(f"✅ CALIBRACIÓN COMPLETADA")
        print(f"   • Coeficiente k: {self.k_coeff:.6f} [1/s]")
        print(f"   • T inicial modelo: {self.T_inicial_modelo:.2f}°C")
        print(f"   • Tiempo de equilibrio: {3/self.k_coeff:.0f}s")
        print("=" * 60)
        
        return self.T_inicial_modelo
    
    def calcular_temp_modelo(self, tiempo_actual):
        """Calcula temperatura del modelo teórico en un tiempo dado"""
        if self.T_inicial_modelo is None or self.k_coeff is None:
            return self.T_amb
        
        # Ley de enfriamiento de Newton: T(t) = T_amb + (T0 - T_amb) * e^(-kt)
        try:
            temp_modelo = self.T_amb + (self.T_inicial_modelo - self.T_amb) * \
                         np.exp(-self.k_coeff * tiempo_actual)
            return temp_modelo if isfinite(temp_modelo) else self.T_amb
        except:
            return self.T_amb
    
    def actualizar_datos(self):
        """Hilo para actualizar datos continuamente"""
        print("🔄 Iniciando hilo de actualización de datos...")
        
        while self.running:
            try:
                tiempo_actual = time.time() - self.tiempo_inicio
                
                # Leer temperatura real de CPU
                temp_cpu = self.leer_cpu_temp()
                if temp_cpu is None:
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                # Calcular temperatura del modelo
                temp_modelo = self.calcular_temp_modelo(tiempo_actual)
                
                # Actualizar datos de forma thread-safe
                with self.lock:
                    self.tiempos.append(tiempo_actual)
                    self.temps_cpu_reales.append(temp_cpu)
                    self.temps_modelo.append(temp_modelo)
                
                time.sleep(REFRESH_INTERVAL)
                
            except Exception as e:
                print(f"⚠️  Error en hilo de datos: {e}")
                time.sleep(REFRESH_INTERVAL)
    
    def animar_grafico(self, frame):
        """Función de animación para actualizar el gráfico"""
        try:
            with self.lock:
                if len(self.tiempos) == 0:
                    return list(self.lines.values()) + [self.text_info]
                
                # Convertir deques a listas para matplotlib
                tiempos_list = list(self.tiempos)
                temps_cpu_list = list(self.temps_cpu_reales)
                temps_modelo_list = list(self.temps_modelo)
                
                # Actualizar líneas
                self.lines['cpu'].set_data(tiempos_list, temps_cpu_list)
                self.lines['modelo'].set_data(tiempos_list, temps_modelo_list)
                
                # Línea de temperatura ambiente
                if len(tiempos_list) >= 2:
                    self.lines['ambiente'].set_data(
                        [tiempos_list[0], tiempos_list[-1]], 
                        [self.T_amb, self.T_amb]
                    )
                
                # Actualizar información
                if len(temps_cpu_list) > 0:
                    temp_real = temps_cpu_list[-1]
                    temp_teorica = temps_modelo_list[-1]
                    delta = temp_real - temp_teorica
                    
                    info_text = (
                        f"🖥️  CPU Real: {temp_real:.1f}°C  |  📊 Modelo: {temp_teorica:.1f}°C\n"
                        f"🏠 Ambiente: {self.T_amb:.1f}°C  |  📈 Δ = {delta:+.2f}°C  |  "
                        f"⚙️ k = {self.k_coeff:.4f}\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}  |  "
                        f"📊 Puntos: {len(tiempos_list)}"
                    )
                    self.text_info.set_text(info_text)
                
                # Ajustar límites del gráfico
                if len(tiempos_list) > 1:
                    self.ax.set_xlim(tiempos_list[0], tiempos_list[-1] + 2)
                    
                    all_temps = temps_cpu_list + temps_modelo_list + [self.T_amb]
                    temp_min, temp_max = min(all_temps), max(all_temps)
                    margen = max(2.0, (temp_max - temp_min) * 0.15)
                    self.ax.set_ylim(temp_min - margen, temp_max + margen)
            
            return list(self.lines.values()) + [self.text_info]
            
        except Exception as e:
            print(f"⚠️  Error en animación: {e}")
            return list(self.lines.values()) + [self.text_info]
    
    def configurar_grafico(self):
        """Configura la interfaz gráfica"""
        # Crear figura con tema moderno
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.fig.suptitle('🖥️ Monitor CPU: Temperatura Real vs Tendencia Teórica', 
                         fontsize=16, fontweight='bold')
        
        # Configurar colores y estilos
        colors = {
            'cpu': '#ff4757',      # rojo vibrante
            'modelo': '#2ed573',   # verde agua
            'ambiente': '#1e90ff'  # azul
        }
        
        # Crear líneas del gráfico
        self.lines['cpu'], = self.ax.plot([], [], 'o-', color=colors['cpu'], 
                                         linewidth=2.5, markersize=4, 
                                         label='🔥 CPU Real', alpha=0.9)
        
        self.lines['modelo'], = self.ax.plot([], [], '-', color=colors['modelo'], 
                                            linewidth=2, label='📈 Tendencia Teórica', 
                                            alpha=0.8)
        
        self.lines['ambiente'], = self.ax.plot([], [], '--', color=colors['ambiente'], 
                                              linewidth=2, label='🏠 T. Ambiente', 
                                              alpha=0.7)
        
        # Configurar ejes y leyenda
        self.ax.set_xlabel('⏰ Tiempo [segundos]', fontsize=12)
        self.ax.set_ylabel('🌡️ Temperatura [°C]', fontsize=12)
        self.ax.legend(loc='upper right', fontsize=11)
        self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Cuadro de información
        self.text_info = self.ax.text(0.02, 0.98, "", transform=self.ax.transAxes,
                                     fontsize=10, verticalalignment='top',
                                     bbox=dict(boxstyle='round,pad=0.8', 
                                             facecolor='black', alpha=0.8, 
                                             edgecolor='gray'),
                                     color='white', family='monospace')
        
        # Configurar estilo de la figura
        self.fig.patch.set_facecolor('#f8f9fa')
        self.ax.set_facecolor('#ffffff')
    
    def iniciar_monitor(self):
        """Función principal para iniciar el monitor"""
        print("🚀 INICIANDO MONITOR DE TEMPERATURA CPU")
        print("=" * 50)
        
        try:
            # Calibrar coeficiente k
            self.calibrar_coeficiente_k()
            
            # Configurar gráfico
            print("\n🎨 Configurando interfaz gráfica...")
            self.configurar_grafico()
            
            # Iniciar sistema
            print("🔄 Iniciando sistema de monitoreo...")
            self.running = True
            self.tiempo_inicio = time.time()
            
            # Iniciar hilo de actualización de datos
            hilo_datos = threading.Thread(target=self.actualizar_datos, daemon=True)
            hilo_datos.start()
            
            # Iniciar animación
            from matplotlib.animation import FuncAnimation
            ani = FuncAnimation(self.fig, self.animar_grafico, interval=1000, 
                              blit=False, cache_frame_data=False)
            
            print("✅ Monitor iniciado correctamente!")
            print("💡 El gráfico se actualiza cada segundo")
            print("🔧 Usa stress tests para ver cambios en tiempo real")
            print("❌ Cierra la ventana para terminar")
            print("=" * 50)
            
            # Mostrar gráfico
            plt.tight_layout()
            plt.show()
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.running = False
            print("🔚 Monitor terminado")

def main():
    """Función principal"""
    monitor = CPUMonitor()
    monitor.iniciar_monitor()

if __name__ == "__main__":
    main()