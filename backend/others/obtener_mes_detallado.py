import os
import sys
from egauge import webapi
from datetime import datetime
import csv
import traceback
from typing import List, Dict, Any


# ==============================================================================
# 1. CONFIGURACIÓN GLOBAL Y DINÁMICA
# ==============================================================================


# Credenciales ÚNICAS para todos los dispositivos
USER = os.getenv('EGUSR', 'evamexico')
PASSWORD = os.getenv('EGPWD', '12345678')


# Definir el rango de fechas (ejemplo: septiembre 2025)
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 9, 30, 23, 0, 0) # Incluir la última hora del día 30


# Granularidad de los datos (en segundos)
DELTA = 3600  # 3600 segundos = 1 hora


# Convertir a timestamps
START_TS = int(START_DATE.timestamp())
END_TS = int(END_DATE.timestamp())
TIME_PARAM = f"{START_TS}:{DELTA}:{END_TS}"


# ==============================================================================
# 2. FUNCIÓN PARA OBTENER URLs DEL USUARIO
# ==============================================================================


def get_urls_from_input() -> List[str]:
    """
    Solicita URLs al usuario de forma interactiva.
    Permite ingresar múltiples URLs, una por línea.
    """
    print("\n" + "=" * 80)
    print("INGRESO DE URLs DE DISPOSITIVOS eGauge")
    print("=" * 80)
    print("\nOpciones de ingreso:")
    print("  1. Ingresar URLs una por una")
    print("  2. Ingresar múltiples URLs separadas por comas")
    print("  3. Usar URLs por defecto de ejemplo")
    
    option = input("\nSelecciona una opción (1-3): ").strip()
    
    urls = []
    
    if option == "1":
        print("\n📝 Ingresa las URLs de los dispositivos (presiona Enter sin texto para terminar):")
        print("   Ejemplo: https://egauge90707.egaug.es\n")
        
        count = 1
        while True:
            url = input(f"  URL {count}: ").strip()
            if not url:
                break
            if url.startswith('http'):
                urls.append(url)
                print(f"    ✓ URL {count} agregada")
                count += 1
            else:
                print("    ⚠️  La URL debe comenzar con http:// o https://")
    
    elif option == "2":
        print("\n📝 Ingresa las URLs separadas por comas:")
        print("   Ejemplo: https://egauge90707.egaug.es, https://egauge86055.egaug.es\n")
        
        urls_input = input("  URLs: ").strip()
        urls = [url.strip() for url in urls_input.split(',') if url.strip().startswith('http')]
        
        if urls:
            print(f"\n  ✓ {len(urls)} URL(s) agregada(s)")
            for i, url in enumerate(urls, 1):
                print(f"    {i}. {url}")
    
    elif option == "3":
        urls = [
            'https://egauge90707.egaug.es',
            'https://egauge86055.egaug.es',
        ]
        print(f"\n  ✓ Usando {len(urls)} URL(s) por defecto")
        for i, url in enumerate(urls, 1):
            print(f"    {i}. {url}")
    
    else:
        print("  ⚠️  Opción no válida. Usando URLs por defecto.")
        urls = ['https://egauge90707.egaug.es']
    
    if not urls:
        print("\n  ⚠️  No se ingresaron URLs válidas. Usando URL por defecto.")
        urls = ['https://egauge90707.egaug.es']
    
    print(f"\n✅ Total de dispositivos a procesar: {len(urls)}")
    input("\nPresiona Enter para continuar...")
    
    return urls


# ==============================================================================
# 3. FUNCIÓN DE PROCESAMIENTO
# ==============================================================================


def process_egauge_data(url: str, user: str, password: str, time_param: str):
    """
    Conecta a un dispositivo eGauge, obtiene los datos, los imprime y los exporta a CSV.
    """
    # Usamos la última parte del URL como alias para el nombre del archivo
    alias = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1].split('.')[0]
    
    print("\n" + "#" * 80)
    print(f"[{alias}] - INICIANDO PROCESAMIENTO para URL: {url}")
    print("#" * 80)


    # 1. Conexión y Autenticación
    try:
        dev = webapi.device.Device(
            url, webapi.JWTAuth(user, password)
        )
        rights = dev.get("/auth/rights").get("rights", [])
        print(f"  ✓ Conectado exitosamente con usuario: {user}, Permisos: {rights}")
    except webapi.Error as e:
        print(f"  ❌ ERROR: Falló la conexión o autenticación a {url}: {e}")
        return


    # 2. Obtención de Datos
    try:
        delta_hours = DELTA // 3600
        print(f"  ... Solicitando datos por intervalos de {delta_hours} hora(s) desde {START_DATE} hasta {END_DATE}")
        
        ret = webapi.device.Register(dev, {"time": time_param})
        
        # Recolectar todas las filas
        rows = list(ret)
        total_intervals = len(rows) - 1
        
        print(f"  ✓ Filas de datos acumulados obtenidas: {len(rows)}")
        print(f"  ✓ Total de intervalos de datos a procesar: {total_intervals}")


    except Exception as e:
        print(f"  ❌ ERROR al obtener datos del API: {e}")
        return


    # 3. Procesamiento y Exportación a CSV
    if total_intervals > 0:
        
        csv_file = f"{alias}_datos_{START_DATE.strftime('%Y%m')}_por_{delta_hours}h.csv"
        print(f"  ... Exportando datos a: {csv_file}")
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Encabezados
                headers = ["Fecha", "Hora", "Timestamp"]
                for regname in ret.regs:
                    headers.append(f"{regname} (Delta)")
                writer.writerow(headers)
                
                # Datos (cada fila es el consumo/cambio desde la fila anterior)
                for i in range(len(rows)-1):
                    delta_row = rows[i] - rows[i+1]
                    timestamp = datetime.fromtimestamp(float(rows[i+1].ts))
                    
                    row_data = [
                        timestamp.strftime("%Y-%m-%d"),
                        timestamp.strftime("%H:%M:%S"),
                        float(rows[i+1].ts)
                    ]
                    
                    for regname in ret.regs:
                        accu = delta_row.pq_accu(regname)
                        # Añadir el valor de cambio (delta) o 0 si no existe
                        row_data.append(float(accu.value) if accu else 0)
                    
                    writer.writerow(row_data)
            
            print(f"  ✓ Datos exportados exitosamente. Total de {total_intervals} intervalos.")
            
        except Exception as e:
            print(f"  ❌ ERROR al escribir el archivo CSV: {e}")
            traceback.print_exc()


        # 4. Resumen del Período
        print("\n" + "=" * 80)
        print(f"[{alias}] RESUMEN TOTAL DEL PERÍODO")
        print("=" * 80)
        
        delta_total = rows[0] - rows[-1]
        
        first_time = datetime.fromtimestamp(float(rows[-1].ts))
        last_time = datetime.fromtimestamp(float(rows[0].ts))
        
        print(f"\nDesde: {first_time} | Hasta: {last_time}")
        
        print("\n{:<30} {:>20}".format("Registro", "Total Acumulado"))
        print("-" * 55)
        
        for regname in delta_total.regs:
            accu = delta_total.pq_accu(regname)
            
            if accu:
                print("{:<30} {:>15.2f} {:>4}".format(
                    regname,
                    float(accu.value), accu.unit
                ))
    else:
        print("  ⚠️ No se obtuvieron suficientes filas de datos para el período especificado.")
    
    print("\n" + "=" * 80)


# ==============================================================================
# 4. EJECUCIÓN PRINCIPAL
# ==============================================================================


if __name__ == "__main__":
    # Obtener URLs del usuario de forma interactiva
    EGDEV_URLS = get_urls_from_input()
    
    print(f"\nIniciando procesamiento de {len(EGDEV_URLS)} dispositivo(s) con usuario: {USER}")
    
    # Procesar cada URL en la lista
    for url in EGDEV_URLS:
        process_egauge_data(url, USER, PASSWORD, TIME_PARAM)


    print("\n✅ PROCESAMIENTO GLOBAL FINALIZADO.")
