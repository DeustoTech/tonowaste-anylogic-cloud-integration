# Lanzador de Simulaciones (Launch Simulation)

## 📋 Resumen

Script de **automatización genérica** para ejecutar simulaciones en AnyLogic Cloud usando configuración vía JSON. Produce resultados reproducibles y parametrizables.

**Propósito:** Ejecutar simulaciones automáticamente con diferentes modelos y parámetros sin cambiar código

**Estado:** ✅ Production-ready

---

## 🎯 Objetivo Principal
Servir como **herramienta de automatización end-to-end** para:
1. Leer configuración desde JSON (flexible, sin cambiar código)
2. Autenticarse y conectar con AnyLogic Cloud
3. Cargar modelo específico (por ID o nombre)
4. Configurar múltiples parámetros de entrada
5. Ejecutar simulación
6. Extraer outputs específicos solicitados
7. Validar completitud (en modo strict)
8. Guardar resultados en CSV

Ideal para **automatización, CI/CD, batch processing y auditoría**.

---

## 🔧 Funcionalidades

### 1. **Carga de Credenciales** (líneas 84-90)
```python
load_env_from(BASE_DIR / ".env")
API_KEY = os.getenv("ANYLOGIC_API_KEY")
```
- Lee `.env` sin dependencias externas
- Valida que API key existe
- Lanza `ValueError` clara si falta

### 2. **Carga de Configuración JSON** (líneas 92-103)
```python
CONFIG_PATH = BASE_DIR / "config.json"
config = json.load(f)
MODEL_ID = config.get("model_id")
INPUTS_CONF = config.get("inputs", {})
OUTPUTS_CONF = config.get("outputs", [])
```

**Estructura esperada de `config.json`:**
```json
{
  "model_id": "uuid-del-modelo",
  "model_name_fallbacks": ["Nombre 1", "Nombre 2"],
  "experiment": "Baseline",
  "inputs": {
    "parameter1": 100,
    "parameter2": 0.5,
    "parameter3": "some_value"
  },
  "outputs": [
    "Output KPI 1",
    "Output KPI 2",
    "Output KPI 3"
  ],
  "strict_outputs": true
}
```

### 3. **Búsqueda de Modelo** (líneas 116-130)
```python
version = obtener_version(MODEL_ID, MODEL_NAME_FALLBACKS)
```
Estrategia de fallback:
1. Busca por **MODEL_ID** (prioritario, más rápido)
2. Si falla, busca por cada nombre en **model_name_fallbacks**
3. Lanza error claro si ninguno funciona

### 4. **Creación de Inputs** (líneas 132-147)
```python
inputs = client.create_inputs_from_experiment(version, EXPERIMENT_NAME)
for k, v in INPUTS_CONF.items():
    inputs.set_input(k, v)
```
- Intenta usar experimento específico
- Si no existe, usa inputs por defecto
- Configura todos los parámetros desde JSON
- Imprime warnings si algún parámetro no existe (pero continúa)

### 5. **Ejecución de Simulación** (líneas 149-153)
```python
simulation = client.create_simulation(inputs)
outputs = simulation.get_outputs_and_run_if_absent()
```
- Crea simulación con inputs configurados
- Ejecuta de forma **síncrona** (espera a terminar)
- Captura outputs automáticamente

### 6. **Extracción Robusta de Outputs** (función `get_all_outputs`)
Implementa **4 estrategias progresivas**:

1. **Métodos agregados** (get_values, to_json, as_json)
2. **get_outputs()** - Lista de objetos con .name
3. **get_raw_outputs()** - Fallback para APIs antiguas
4. **Dict interno** (outputs.outputs)

### 7. **Lectura Explícita de Outputs** (líneas 181-200)
```python
for name in OUTPUTS_CONF:
    try:
        val = outputs.value(name)
        explicitos[name] = val
    except Exception:
        missing.append(name)
```
- Lee **SOLO** los outputs especificados en config.json
- Registra outputs faltantes
- Si `strict_outputs=true`, falla si falta alguno
- Imprime warnings para debugging

### 8. **Validación en Modo Strict** (líneas 202-204)
```python
if STRICT_OUTPUTS and missing:
    raise SystemExit(f"Faltan salidas requeridas: {missing}")
```
- Modo `strict_outputs: true` en config.json
- Falla si no se encuentran TODOS los outputs solicitados
- Útil para auditoría y validación

### 9. **Almacenamiento de Resultados** (líneas 206-213)
```python
csv_path = BASE_DIR / "resultados.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w.writerow(["output_name", "value"])
    for k, v in explicitos.items():
        w.writerow([k, v])
```
- Genera `resultados.csv` con **solo outputs solicitados**
- Formato: dos columnas (nombre, valor)
- Evita ruido de outputs no requeridos

---

## 📁 Archivos de Entrada

### `.env` (obligatorio, en directorio raíz)

```
ANYLOGIC_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...
```

Crear en: `../.env` (uno nivel arriba de este directorio)

### `config.json` (obligatorio, en directorio raíz)
```json
{
  "model_id": "1ba2f2f6-7c7f-4067-885a-441bb0bd5d03",
  "model_name_fallbacks": [
    "Service System Demo",
    "Service Systems Demo"
  ],
  "experiment": "Baseline",
  "inputs": {
    "Server capacity": 8,
    "Mean inter-arrival time": 2.5,
    "Service time": 1.2
  },
  "outputs": [
    "Mean queue size|Mean queue size",
    "Utilization|Server utilization",
    "Throughput|Throughput",
    "Average delay|Average delay"
  ],
  "strict_outputs": true
}
```

**Campos en config.json:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| model_id | string | ✅ | UUID del modelo en AnyLogic Cloud |
| model_name_fallbacks | array | ❌ | Nombres alternativos para buscar si ID falla |
| experiment | string | ❌ | Nombre del experimento ("Baseline" por defecto) |
| inputs | object | ✅ | Diccionario de parámetros → valores |
| outputs | array | ✅ | Nombres exactos de outputs a capturar |
| strict_outputs | boolean | ❌ | Si true, falla si no encuentra todos los outputs |

---

## 📁 Archivos de Salida

| Archivo | Contenido |
|---------|-----------|
| `resultados.csv` | Tabla con dos columnas: output_name, value (solo outputs solicitados) |

**Formato CSV:**
```
output_name,value
Mean queue size|Mean queue size,3.45
Utilization|Server utilization,0.78
Throughput|Throughput,42
Average delay|Average delay,1.25
```

---

## 🚀 Modo de Uso

### 1. **Instalación de dependencias**
```bash
pip install anylogic-cloud-client
```

### 2. **Crear `.env` (en raíz del proyecto)**
```bash
echo "ANYLOGIC_API_KEY=tu_clave_api_aqui" > ../.env
```

### 3. **Crear `config.json` (en raíz del proyecto)**

Ejemplo minimalista:

```json
{
  "model_id": "abc123-def456",
  "experiment": "Baseline",
  "inputs": {
    "Server capacity": 10,
    "Arrival rate": 5
  },
  "outputs": [
    "Average wait time",
    "System utilization"
  ],
  "strict_outputs": false
}
```

Guardar en: `../config.json`

### 4. **Ejecutar**
```bash
python launch_simulation.py
```

### 5. **Salida esperada en terminal**
```
AnyLogic API key cargada (prefijo): eyJ0eXAi...
Configuración cargada desde ../config.json
Modelo ID: abc123-def456
Experimento: Baseline
Usando experimento: Baseline
Input 'Server capacity' = 10
Input 'Arrival rate' = 5

Lanzando simulación...
Simulación completada.

=== Salidas (intento de enumeración) ===
- Average wait time: 1.45
- System utilization: 0.87
- Processed: 450
========================================

=== Salidas solicitadas explícitamente ===
- Average wait time: 1.45
- System utilization: 0.87
==========================================

Guardado (outputs explícitos): ../resultados.csv
Ejecución finalizada.
```

Nota: `resultados.csv` se genera en el **directorio raíz** del proyecto (no en esta carpeta)

---

## 🔍 Detalles Técnicos

### Funciones Auxiliares

#### `load_env_from(path: Path)`
Lee variables de entorno desde `.env`
- Sin dependencias (no usa `python-dotenv`)
- Soporta valores entrecomillados
- Ignora líneas vacías y comentarios

#### `get_all_outputs(outputs)`
Extrae todos los outputs disponibles (para debugging)
- **Retorna:** Dict {nombre: valor}
- **Estrategia:** 4 intentos progresivos
- **Propósito:** Enumerar qué outputs existen (no es obligatorio usarlos)

#### `obtener_version(model_id, model_name_list)`
Obtiene versión más reciente del modelo
- Intenta por ID primero
- Luego por cada nombre en fallbacks
- Lanza SystemExit si ninguno funciona

---

## 💡 Diferencias con `test_cloud.py`

| Aspecto | test_cloud.py | launch_simulation.py |
|--------|--------------|----------------------|
| Config | Hardcoded en código | config.json |
| Inputs | Un solo parámetro modificado | Múltiples desde JSON |
| Outputs | Todos los que encuentra | Solo los especificados |
| Validación | No hay | Modo strict disponible |
| CSV | Todos los outputs | Solo los solicitados |
| Propósito | Prueba/debugging | Producción/automatización |
| Reutilizable | No (cambiar código) | Sí (cambiar JSON) |

---

## 🛡️ Manejo de Errores

| Situación | Acción |
|-----------|--------|
| `.env` no existe o sin API key | ValueError claro |
| `config.json` no existe | FileNotFoundError claro |
| `config.json` mal formado (JSON inválido) | JSONDecodeError |
| Outputs requeridos faltantes + strict=true | SystemExit con lista |
| Input no existe en modelo | Warning, continúa |
| Modelo no accesible | Intenta fallbacks, luego error |
| Experimento no existe | Usa inputs por defecto |

---

## 📊 Ejemplo Completo

### Escenario: Simular "Service System Demo" con 3 parámetros, capturar 4 KPIs

**1. `.env`**
```
ANYLOGIC_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**2. `config.json`**
```json
{
  "model_id": "1ba2f2f6-7c7f-4067-885a-441bb0bd5d03",
  "model_name_fallbacks": [
    "Service System Demo",
    "Service Systems Demo",
    "Bass Diffusion"
  ],
  "experiment": "Baseline",
  "inputs": {
    "Server capacity": 8,
    "Mean inter-arrival time": 2.0,
    "Service time": 1.5
  },
  "outputs": [
    "Mean queue size|Mean queue size",
    "Utilization|Server utilization",
    "Throughput|Throughput",
    "Average delay|Average delay"
  ],
  "strict_outputs": true
}
```

**3. Ejecutar**
```bash
python launch_simulation.py
```

**4. Ver `resultados.csv`**
```csv
output_name,value
Mean queue size|Mean queue size,2.15
Utilization|Server utilization,0.75
Throughput|Throughput,35
Average delay|Average delay,0.98
```

---

## 🔗 Dependencias Externas

- **anylogiccloudclient**: Cliente oficial de AnyLogic Cloud
  - Métodos: get_model_by_id, get_model_by_name, create_inputs_from_experiment, create_simulation, etc.

### Dependencias estándar
- `os`, `json`, `csv`, `pathlib`

---

## 💡 Casos de Uso

### 1. **Automatización Batch**
- Ejecutar múltiples simulaciones con diferentes `config.json`
- Un script para todos los modelos

### 2. **CI/CD Pipeline**
- Validar modelo en cada cambio
- Modo strict garantiza outputs esperados

### 3. **Captura de Datos para BI**
- Generar CSV regularmente (cron, scheduler)
- Alimentar data warehouse

### 4. **Generación de Reportes**
- Ejecutar lanzador
- Procesar CSV con pandas/excel
- Generar gráficos

### 5. **Testing/QA Automático**
- Verificar que modelo se ejecuta
- Validar que outputs tienen rangos esperados
- Detectar regresos en cambios de modelo

---

## ⚙️ Requisitos del Sistema

- **Python 3.7+**
- **Conexión a internet** (AnyLogic Cloud)
- **API key válida** con permisos en el modelo
- **Permisos de lectura/ejecución** del modelo
- **Permisos de escritura** en directorio del script

---

## 🐛 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `ValueError: No se encontró ANYLOGIC_API_KEY` | .env no existe o vacío | Crear .env con API key |
| `FileNotFoundError: No existe config.json` | config.json no está en directorio | Crear config.json en mismo directorio |
| `JSONDecodeError` en config.json | JSON mal formado | Validar JSON (usar jsonlint) |
| `SystemExit: Faltan salidas requeridas` | strict_outputs=true y outputs no encontrados | Desactivar strict o revisar nombres |
| Aviso: "No se pudo asignar 'X'" | Parámetro no existe en modelo | Revisar nombres en config exactamente |
| CSV vacío | Outputs no capturados | Ejecutar inspect_anylogic_model.py para listar disponibles |
| Timeout | Simulación tarda demasiado | Simplificar modelo o esperar |

---

## 📝 Notas Importantes

1. **Nombres exactos:** Los nombres de inputs/outputs en config.json deben ser **exactamente** como aparecen en el modelo (case-sensitive)
2. **Ejecución síncrona:** El script espera bloqueante a que termine la simulación
3. **Sobrescritura:** `resultados.csv` se sobrescribe en cada ejecución
4. **Red:** Se requiere conexión a internet durante toda la ejecución
5. **Strict mode:** Si necesitas garantías de completitud de datos, usa `"strict_outputs": true`

---

## 🔄 Flujo Completo

```
┌──────────────────────┐
│  Cargar .env         │
│  Validar API_KEY     │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Cargar config.json  │
│  Validar estructura  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Conectar Cloud      │
│  CloudClient(key)    │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Buscar modelo       │
│  Por ID → fallbacks  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Crear inputs        │
│  Experiment/default  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Configurar inputs   │
│  De config.json      │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Ejecutar simulación │
│  Síncrono            │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Enumerar outputs    │
│  (debugging)         │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Leer outputs        │
│  explícitos solicitados
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Validar completitud │
│  (strict mode)       │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Guardar CSV         │
│  resultados.csv      │
└──────────┬───────────┘
           │
        ¡Éxito!
```

---

## 🎓 Tips de Uso Avanzado

### 1. **Encontrar nombres exactos de inputs/outputs**
```bash
# Primero ejecuta inspect_anylogic_model.py para generar model_schema.json
python inspect_anylogic_model.py

# Luego revisa qué outputs están disponibles:
cat model_schema.json | grep outputs
```

### 2. **Modo no-strict para exploración**
```json
{
  "strict_outputs": false
}
```
Continúa aunque no encuentre algunos outputs (útil para debugging)

### 3. **Múltiples simulaciones**

Crea varios `config*.json` en raíz del proyecto y ejecuta:

```bash
cd launch_simulation

for config in ../config_*.json; do
  cp "$config" ../config.json
  python launch_simulation.py
  mv ../resultados.csv "../resultados_$(basename $config .json).csv"
done
```

### 4. **Verificar que todo está configurado**
```bash
python launch_simulation.py 2>&1 | head -20
```

---

## 🔗 Flujo Recomendado

```
1. Obtener UUID del modelo
   → https://cloud.anylogic.com/models
   
2. Inspeccionar modelo
   → cd ../inspect_anycloud_model
   → python inspect_anylogic_model.py
   → Ver model_schema.json
   
3. Crear config.json en raíz con nombres exactos
   
4. Ejecutar desde esta carpeta
   → python launch_simulation.py
   
5. Ver resultados.csv en raíz del proyecto
```

---

## 📚 Documentación Completa

Ver [../README.md](../README.md) para contexto general del proyecto

---

**Última actualización:** Enero 2026  
**Estado:** Production-ready

---

