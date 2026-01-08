# Test Cloud - Prueba de Integración Inicial

## 📋 Resumen

Script de **prueba simple** para validar que la integración con AnyLogic Cloud funciona correctamente. Ejecuta una simulación del modelo "Service System Demo", modifica un parámetro de prueba y captura los resultados en CSV.

**Propósito:** Debugging y validación inicial de credenciales y conectividad

**Estado:** ⚠️ Legacy - Ver [../launch_simulation/](../launch_simulation/README.md) para automatización

---

## 🎯 Objetivo Principal
Servir como **script de prueba end-to-end** para validar que:
1. La conexión con AnyLogic Cloud funciona
2. El modelo está accesible y se puede ejecutar
3. Los parámetros de entrada se pueden modificar
4. Los resultados se capturan correctamente
5. El flujo completo de integración es viable

---

## 🔧 Funcionalidades

### 1. **Carga de Credenciales** (líneas 72-77)
```python
load_env_from(BASE_DIR / ".env")
load_env_from(BASE_DIR / ".env.local")
API_KEY = os.getenv("ANYLOGIC_API_KEY")
```
- Lee API key desde `.env` o `.env.local`
- Lanza excepción si no encuentra la clave
- **Requisito:** Crear `.env` con `ANYLOGIC_API_KEY=tu_api_key`

### 2. **Configuración de Modelo** (líneas 78-87)
Define valores por defecto o desde variables de entorno:
- **MODEL_ID**: UUID del modelo (por defecto: Service System Demo)
- **MODEL_NAME_FALLBACKS**: Lista de nombres alternativos para buscar
- **EXPERIMENT_NAME**: Nombre del experimento a usar ("Baseline" por defecto)

Estrategia de fallback:
```
Intenta por ID → Si falla, intenta por cada nombre en la lista
```

### 3. **Conexión con AnyLogic Cloud** (líneas 94-117)
```python
client = CloudClient(API_KEY)
version = obtener_version(model_id=MODEL_ID)
```
- Crea cliente con la API key
- Obtiene la versión más reciente del modelo
- Maneja excepciones y fallback a búsqueda por nombre
- Imprime advertencias claras si hay problemas

### 4. **Creación de Inputs** (líneas 119-139)
```python
inputs = client.create_inputs_from_experiment(version, EXPERIMENT_NAME)
```
- Intenta usar un experimento específico ("Baseline")
- Si no existe, crea inputs por defecto
- Intenta modificar parámetro de ejemplo "Server capacity" a 8
- Enumera inputs disponibles si el parámetro no se encuentra

### 5. **Ejecución de Simulación** (líneas 141-143)
```python
simulation = client.create_simulation(inputs)
outputs = simulation.get_outputs_and_run_if_absent()
```
- Crea simulación con los inputs definidos
- Ejecuta de forma **síncrona** (espera a que termine)
- Captura outputs automáticamente

### 6. **Extracción Robusta de Outputs** (función `recoger_todos_los_outputs`)
Implementa **5 estrategias progresivas** para máxima compatibilidad:

1. **get_outputs()** - Método estándar (lista de objetos con .name)
2. **Dict interno** (outputs.outputs) - Acceso directo a atributos
3. **get_values()** - Retorna dict con pares key-value
4. **JSON methods** (to_json, as_json) - Serialización a dict
5. **Fallback** - KPIs típicos conocidos (hardcoded)

Cada estrategia se intenta en orden; si una funciona, devuelve los resultados inmediatamente.

### 7. **Almacenamiento de Resultados** (líneas 175-181)
```python
csv_path = BASE_DIR / "resultados.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["output_name", "value"])
    for k, v in valores.items():
        w.writerow([k, v])
```
- Genera archivo `resultados.csv` en el mismo directorio que el script
- Formato: dos columnas (nombre del output, valor)
- Sobrescribe el archivo en cada ejecución

---

## 📁 Archivos de Entrada

### `.env` (obligatorio)
```
ANYLOGIC_API_KEY=tu_clave_api_aqui
ANYLOGIC_MODEL_ID=1ba2f2f6-7c7f-4067-885a-441bb0bd5d03  # opcional
ANYLOGIC_EXPERIMENT=Baseline  # opcional
```

### `.env.local` (opcional)
Para override local sin modificar `.env` principal

---

## 📁 Archivos de Salida

| Archivo | Contenido |
|---------|-----------|
| `resultados.csv` | Tabla con dos columnas: output_name, value |

**Formato CSV:**
```
output_name,value
Mean queue size|Mean queue size,3.45
Utilization|Server utilization,0.78
Throughput|Throughput,42
```

---

## 🚀 Modo de Uso

### 1. **Instalación de dependencias**
```bash
pip install anylogic-cloud-client
```

### 2. **Configuración inicial**
Crear `.env`:
```
ANYLOGIC_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...
ANYLOGIC_MODEL_ID=1ba2f2f6-7c7f-4067-885a-441bb0bd5d03
ANYLOGIC_EXPERIMENT=Baseline
```

### 3. **Ejecución**
```bash
python test_cloud.py
```

### 4. **Salida esperada en terminal**
```
ANYLOGIC_API_KEY cargada (prefijo): eyJ0eXAi...
MODEL_ID: 1ba2f2f6-7c7f-4067-885a-441bb0bd5d03
Usando experimento: Baseline
Param 'Server capacity' actualizado a 8

=== Salidas disponibles ===
- Mean queue size|Mean queue size = 3.45
- Utilization|Server utilization = 0.78
- Throughput|Throughput = 42
===========================

Mean queue size|Mean queue size = 3.45
Utilization|Server utilization = 0.78

Resultados guardados en: /ruta/a/resultados.csv

¡Run completado!
```

---

## 🔍 Detalles Técnicos

### Funciones Auxiliares

#### `load_env_from(path: Path)`
Lee y carga variables de entorno desde archivo `.env`
- Ignora líneas vacías y comentarios (#)
- Soporta valores entrecomillados ("valor" o 'valor')
- No requiere dependencias externas (sin dotenv)

#### `recoger_todos_los_outputs(outputs)`
Extrae outputs de forma robusta con múltiples estrategias
- **Retorna:** Dict {nombre: valor}
- **Estrategia:** Intenta métodos progresivamente hasta encontrar un resultado
- **Compatibilidad:** Funciona con múltiples versiones de anylogic-cloud-client

#### `obtener_version(model_id=None, model_name=None)`
Obtiene la versión más reciente de un modelo
- **Por ID:** Búsqueda directa (recomendado)
- **Por nombre:** Búsqueda por string (más lenta)

---

## 💡 Estrategia de Búsqueda de Modelo

```mermaid
Intento 1: Buscar por MODEL_ID (UUID)
    ↓ Si falla
Intento 2-5: Buscar por cada nombre en MODEL_NAME_FALLBACKS
    ↓ Si todos fallan
Error: "No se encontró ningún modelo accesible"
```

**Fallbacks por defecto:**
1. "Service System Demo"
2. "Service Systems Demo"
3. "Bass Diffusion Demo"
4. "Bass Diffusion"

### Configurar modelo específico

Opción 1: Variables de entorno (.env)
```
ANYLOGIC_MODEL_ID=mi-uuid-aqui
```

Opción 2: Modificar lista de fallbacks en el código
```python
MODEL_NAME_FALLBACKS = ["Mi Modelo", "Modelo v2"]
```

---

## 🛡️ Manejo de Errores

El script maneja gracefully los siguientes escenarios:

| Situación | Acción |
|-----------|--------|
| API key no encontrada | Lanza ValueError con instrucciones |
| Modelo no accesible por ID | Intenta buscar por nombre |
| Experimento no existe | Usa inputs por defecto |
| Parámetro no existe | Enumera disponibles, continúa |
| Outputs no enumerables | Intenta múltiples métodos de acceso |
| CSV no escribible | Lanza excepción (permisos de directorio) |

---

## 📊 Ejemplo Completo

### 1. Configurar .env
```
ANYLOGIC_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...
ANYLOGIC_MODEL_ID=abc123-def456-ghi789
ANYLOGIC_EXPERIMENT=Sensitivity
```

### 2. Ejecutar
```bash
python test_cloud.py
```

### 3. Verificar resultados.csv
```csv
output_name,value
KPI_1,100.5
KPI_2,45.3
Total_Cost,1250.75
```

---

## 🔗 Dependencias Externas

- **anylogiccloudclient**: Cliente oficial de AnyLogic Cloud
  - Proporciona: `CloudClient`, `CloudError`
  - Métodos: get_model_by_id, get_latest_model_version, create_simulation, etc.

### Dependencias estándar de Python
- `os` - Variables de entorno
- `csv` - Lectura/escritura de CSV
- `pathlib.Path` - Manejo de rutas

---

## 💡 Casos de Uso

### 1. **Validación de Integración**
- Verificar que AnyLogic Cloud está accesible
- Confirmar que el modelo se puede ejecutar
- Probar que los parámetros se pueden modificar

### 2. **Pruebas Automáticas (CI/CD)**
- Ejecutar como test en pipeline
- Verificar que outputs tienen valores esperados
- Detectar cambios en estructura del modelo

### 3. **Captura de Datos**
- Generar resultados CSV para análisis posterior
- Crear histórico de ejecuciones
- Alimentar otros sistemas con KPIs

### 4. **Prototipado**
- Plantilla para otros scripts de integración
- Entender API de anylogic-cloud-client
- Debugging de problemas de conexión

---

## ⚙️ Requisitos del Sistema

- **Python 3.7+**
- **Conexión a internet** (comunicación con AnyLogic Cloud)
- **Clave API válida** de AnyLogic Cloud
- **Acceso de lectura/ejecución** al modelo en AnyLogic Cloud
- **Permisos de escritura** en directorio del script (para CSV)

---

## 🐛 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `ValueError: No se encontró ANYLOGIC_API_KEY` | Clave API no configurada | Crear `.env` con ANYLOGIC_API_KEY |
| `SystemExit: No se encontró ningún modelo accesible` | ID/nombre incorrecto o sin permisos | Verificar MODEL_ID y permisos en AnyLogic |
| `CSV vacío` | Outputs no se capturaron | Revisar configuración del modelo |
| `Exception: Param 'Server capacity' no encontrado` | Nombre de parámetro incorrecto | Ejecutar `inspect_anylogic_model.py` primero |
| `timeout` | Simulación tarda demasiado | Simplificar modelo o aumentar timeout |

---

## 📝 Notas Importantes

1. **Síncrono:** El script **espera bloqueante** a que la simulación termine
2. **Sobrescritura:** `resultados.csv` se sobrescribe en cada ejecución
3. **Red:** Requiere conexión a internet durante toda la ejecución
4. **Permisos:** La API key necesita permisos de ejecución del modelo
5. **Parámetro hardcoded:** El script intenta cambiar "Server capacity" a 8
   - Si no existe, simplemente lo muestra en warnings

---

## 🔄 Flujo Completo

```
┌─────────────────────┐
│  Cargar .env        │
│  API_KEY, MODEL_ID  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Conectar Cloud     │
│  CloudClient(key)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Obtener modelo     │
│  get_model_by_id    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Crear inputs       │
│  Experiment/Default │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Modificar input    │
│  "Server capacity"=8│
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Ejecutar simulación│
│  create_simulation  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Capturar outputs   │
│  (5 estrategias)    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Guardar CSV        │
│  resultados.csv     │
└──────────┬──────────┘
           │
     ¡Éxito!
```

---

