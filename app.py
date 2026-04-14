import os
import json
from datetime import datetime

carpeta_dias = 'days'

def obtener_fecha(nombre_archivo):
    """
    Extrae la fecha del formato DD_MM.json (ej: '13_07.json').
    Busca el mes (segundo número) y luego el día (primer número) 
    para ordenarlos de más antiguo a más reciente.
    """
    try:
        # 1. Quitar el '.json' (queda '13_07')
        nombre_sin_ext = nombre_archivo.replace('.json', '')
        
        # 2. Separar por el guion bajo '_'
        partes = nombre_sin_ext.split('_')
        
        dia = int(partes[0])
        mes = int(partes[1])
        
        # 3. Crear fecha real (usamos 2026 como año base para que Python pueda ordenarlos)
        return datetime(2026, mes, dia)
    except:
        # Si un archivo se llama "copia.json" o algo inválido, lo ignora mandándolo al fondo
        return datetime.min 

# 1. Leer y ordenar archivos de la carpeta 'day'
archivos = [f for f in os.listdir(carpeta_dias) if f.endswith('.json')]
# Al ordenarlos, el último archivo de la lista siempre será el de mayor mes y mayor día
archivos_ordenados = sorted(archivos, key=obtener_fecha)

if not archivos_ordenados:
    print("❌ No hay archivos en la carpeta 'day'.")
    exit()

# 2. Generar datos_day.json (Normalizado con plantilla estricta)
ultimo_archivo = archivos_ordenados[-1]
ruta_ultimo = os.path.join(carpeta_dias, ultimo_archivo)

with open(ruta_ultimo, 'r', encoding='utf-8') as f:
    try:
        data_ultimo = json.load(f)
    except json.JSONDecodeError:
        data_ultimo = {} # Si el archivo está corrupto, usa el fallback de ceros

# Construimos la estructura exacta solicitada para el día
datos_day_plantilla = {
    "resumenDia": data_ultimo.get("resumenDia", {
        "ventas": 0, "ingresos": 0.0, "productos": 0
    }),
    "graficoEvolucion": data_ultimo.get("graficoEvolucion", {
        "categorias": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "23:59"],
        "ingresos": [0.0] * 9,
        "productos": [0] * 9,
        "ventas": [0] * 9
    }),
    "totalesPeriodo": data_ultimo.get("totalesPeriodo", {
        "ventas": 0, "ingresos": 0.0
    }),
    "mediosPago": data_ultimo.get("mediosPago", {
        "etiquetas": ["Posnet (Tarjeta/QR)", "Efectivo"],
        "valores": [0, 0]
    }),
    "cajas": data_ultimo.get("cajas", {
        "nombres": ["Caja 1", "Caja 2", "Caja 3", "Caja 4"],
        "metricas": [
            {"ventas": 0, "ingresos": 0.0}, {"ventas": 0, "ingresos": 0.0},
            {"ventas": 0, "ingresos": 0.0}, {"ventas": 0, "ingresos": 0.0}
        ],
        "graficos": {
            "ventas": [0, 0, 0, 0],
            "productos": [0, 0, 0, 0],
            "ingresos": [0.0, 0.0, 0.0, 0.0]
        }
    }),
    "productos": data_ultimo.get("productos", {
        "destacado": {
            "nombre": "Sin datos", "cantidad": 0
        },
        "listaCompleta": []
    })
}

with open('datos_day.json', 'w', encoding='utf-8') as f:
    json.dump(datos_day_plantilla, f, indent=2, ensure_ascii=False)
print(f"✅ 'datos_day.json' generado basado en {ultimo_archivo}")


# 3. Función consolidadora para Semana y Mes
def consolidar_datos(archivos_periodo, tipo_periodo):
    totales = {"ventas": 0, "ingresos": 0.0, "productos": 0}
    medios_pago_acum = [0, 0]
    cajas_metricas = [{"ventas": 0, "ingresos": 0.0} for _ in range(4)]
    cajas_productos = [0, 0, 0, 0]
    productos_acum = {}
    
    grafico_semana = {"categorias": [], "ingresos": [], "productos": [], "ventas": []}
    grafico_mes = {"categorias": [], "ingresos": [], "productos": [], "ventas": []}
    
    for archivo in archivos_periodo:
        ruta = os.path.join(carpeta_dias, archivo)
        with open(ruta, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                res = data.get("resumenDia", {})
                
                totales["ventas"] += res.get("ventas", 0)
                totales["ingresos"] += res.get("ingresos", 0.0)
                totales["productos"] += res.get("productos", 0)
                
                if tipo_periodo == 'semana':
                    fecha_obj = obtener_fecha(archivo)
                    # La etiqueta en el gráfico semanal se verá como "13/07"
                    etiqueta_fecha = fecha_obj.strftime("%d/%m") 
                    
                    grafico_semana["categorias"].append(etiqueta_fecha)
                    grafico_semana["ingresos"].append(res.get("ingresos", 0.0))
                    grafico_semana["productos"].append(res.get("productos", 0))
                    grafico_semana["ventas"].append(res.get("ventas", 0))
                    
                elif tipo_periodo == 'mes':
                    fecha_obj = obtener_fecha(archivo)
                    # La etiqueta se verá como "13/07". 
                    # Al ser 30 días, ApexCharts las espaciará automáticamente en la pantalla.
                    etiqueta_fecha = fecha_obj.strftime("%d/%m") 
                    
                    grafico_mes["categorias"].append(etiqueta_fecha)
                    grafico_mes["ingresos"].append(res.get("ingresos", 0.0))
                    grafico_mes["productos"].append(res.get("productos", 0))
                    grafico_mes["ventas"].append(res.get("ventas", 0))
                    
                    
                vals = data.get("mediosPago", {}).get("valores", [0, 0])
                if len(vals) == 2:
                    medios_pago_acum[0] += vals[0]
                    medios_pago_acum[1] += vals[1]

                for i in range(4):
                    if "cajas" in data:
                        if "metricas" in data["cajas"] and i < len(data["cajas"]["metricas"]):
                            cajas_metricas[i]["ventas"] += data["cajas"]["metricas"][i].get("ventas", 0)
                            cajas_metricas[i]["ingresos"] += data["cajas"]["metricas"][i].get("ingresos", 0.0)
                        if "graficos" in data["cajas"] and "productos" in data["cajas"]["graficos"]:
                            cajas_productos[i] += data["cajas"]["graficos"]["productos"][i]

                for prod in data.get("productos", {}).get("listaCompleta", []):
                    n = prod.get("nombre", "N/A")
                    productos_acum[n] = productos_acum.get(n, 0) + prod.get("cantidad", 0)

            except Exception as e:
                print(f"⚠️ Error en {archivo}: {e}")

    totales["ingresos"] = round(totales["ingresos"], 2)
    total_p = sum(medios_pago_acum)
    porc_pago = [round((medios_pago_acum[0]/total_p)*100), 0] if total_p > 0 else [0, 0]
    porc_pago[1] = 100 - porc_pago[0] if total_p > 0 else 0

    lista_prods = sorted([{"nombre": k, "cantidad": v} for k, v in productos_acum.items()], key=lambda x: x["cantidad"], reverse=True)

    resultado = {
        "totalesPeriodo": totales,
        "mediosPago": {"etiquetas": ["Posnet (Tarjeta/QR)", "Efectivo"], "valores": porc_pago},
        "cajas": {
            "nombres": ["Caja 1", "Caja 2", "Caja 3", "Caja 4"],
            "metricas": [{"ventas": m["ventas"], "ingresos": round(m["ingresos"], 2)} for m in cajas_metricas],
            "graficos": {"ventas": [m["ventas"] for m in cajas_metricas], "productos": cajas_productos, "ingresos": [round(m["ingresos"], 2) for m in cajas_metricas]}
        },
        "productos": {"destacado": lista_prods[0] if lista_prods else {"nombre": "Sin datos", "cantidad": 0}, "listaCompleta": lista_prods}
    }
    
    if tipo_periodo == 'semana':
        resultado["resumenSemana"] = totales
        resultado["semana"] = grafico_semana
    else:
        resultado["resumenMes"] = totales
        resultado["mes"] = grafico_mes

    return resultado

# 4. Guardar semana y mes
with open('datos_7_day.json', 'w', encoding='utf-8') as f:
    json.dump(consolidar_datos(archivos_ordenados[-7:], 'semana'), f, indent=2, ensure_ascii=False)

with open('datos_month.json', 'w', encoding='utf-8') as f:
    json.dump(consolidar_datos(archivos_ordenados[-30:], 'mes'), f, indent=2, ensure_ascii=False)

print("🚀 Todos los índices actualizados correctamente.")