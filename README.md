# AnyLogic Cloud Integration - Suite de Automatización de Simulaciones

## 📋 Resumen Ejecutivo

Suite completa de Python para **automatizar simulaciones en AnyLogic Cloud** de forma genérica y parametrizable. Permite:
- 🔍 Inspeccionar modelos (descubrir inputs/outputs)
- ⚙️ Configurar simulaciones vía JSON
- 🚀 Ejecutar simulaciones automáticamente
- 📊 Capturar y almacenar resultados en CSV

---

## 🎯 Evolución de la Solución

### Fase 1: Prueba Inicial (`test_cloud.py`)

**Objetivo:** Validar que la integración con AnyLogic Cloud funciona

```python
# ❌ Problema: Hardcoded, no reutilizable
- Modelo fijo: "Service System Demo"
- Un parámetro modificado manualmente
- CSV con todos los outputs (ruido)
- Para cada modelo nuevo, editar código
```

**Resultado:** `resultados_serviceSystemDemo.csv`

---

### Fase 2: Inspección de Modelos (`inspect_anylogic_model.py`)

**Objetivo:** Descubrir automáticamente inputs y outputs de cualquier modelo

```
Script interactivo que:
✅ Lee credenciales desde .env
✅ Conecta con AnyLogic Cloud
✅ Identifica modelo por ID o nombre
✅ Enumera inputs disponibles
✅ Ejecuta simulación de prueba
✅ Extrae y documenta outputs
✅ Genera JSON de esquema
```

**Salida:** `model_schema.json`, archivos de introspección

**Ventaja:** Ahora sabemos exactamente qué parámetros y resultados tiene cada modelo

---

### Fase 3: Configuración Genérica (`config.json` / `config2.json`)

**Objetivo:** Parametrizar los modelos sin cambiar código

```json
{
  "model_id": "uuid-del-modelo",
  "model_name_fallbacks": ["Nombre 1", "Nombre 2"],
  "experiment": "Baseline",
  "inputs": {
    "Server capacity": 8,
    "Mean inter-arrival time": 2.5
  },
  "outputs": [
    "Mean queue size|Mean queue size",
    "Utilization|Server utilization"
  ],
  "strict_outputs": true
}
```

**Archivos disponibles:**
- `config.json` → Bass Diffusion Demo
- `config2.json` → Service System Demo

**Ventaja:** Configuración separada del código, fácil de mantener

---

### Fase 4: Automatización Genérica (`launch_simulation.py`)

**Objetivo:** Script universal que funciona con cualquier config.json

```
launch_simulation.py:
✅ Lee config.json
✅ Autentica con AnyLogic Cloud
✅ Busca modelo (ID o fallback names)
✅ Configura múltiples inputs
✅ Ejecuta simulación
✅ Captura outputs solicitados
✅ Valida completitud (strict mode)
✅ Guarda resultados en CSV
```

**Resultado:** `resultados.csv` (solo outputs solicitados)

**Ventaja:** Script único para todos los modelos. Solo cambias `config.json`

---

## 📁 Estructura de Archivos

```
Anycloud/
├── README.md                           # Este archivo
├── .env                                # Credenciales (no versionado)
│   └── ANYLOGIC_API_KEY=xxx
│
├── Scripts de Automatización
├── ├── test_cloud.py                   # ❌ Legacy (no usar)
├── ├── inspect_anylogic_model.py       # 🔍 Inspeccionar modelos
├── └── launch_simulation.py            # 🚀 Lanzar simulaciones (PRINCIPAL)
│
├── Configuración
├── ├── config.json                     # Config Bass Diffusion Demo
├── └── config2.json                    # Config Service System Demo
│
├── Documentación
├── ├── DOCUMENTACION_inspect_anylogic_model.md
├── ├── DOCUMENTACION_launch_simulation.md
├── ├── DOCUMENTACION_test_cloud.md
│
├── Salidas
├── ├── resultados.csv                  # Última ejecución
├── ├── resultados_serviceSystemDemo.csv # Legacy
├── ├── model_schema.json               # Esquema inspeccionado
├── └── *.json                          # Archivos auxiliares
│
└── Dependencias
    └── requirements.txt                # pip install -r requirements.txt
```

---

## 🚀 Guía de Uso Rápido

### 1. Instalación Inicial

```bash
# Clonar/descargar repositorio
cd /home/oihane/00_ToNoWaste/Anycloud

# Instalar dependencias
pip install -r requirements.txt

# O instalar manualmente:
pip install anylogic-cloud-client
```

### 2. Configurar Credenciales

Crear archivo `.env` en el directorio (no versionado):

```bash
cat > .env <<EOF
ANYLOGIC_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...
EOF
```

Obtener API key: https://cloud.anylogic.com/settings/api-keys

### 3. Ejecutar Simulación (Más Común)

```bash
# Con Bass Diffusion Demo (config.json por defecto)
python launch_simulation.py

# Con Service System Demo
cp config2.json config.json
python launch_simulation.py

# Ver resultados
cat resultados.csv
```

### 4. Inspeccionar Nuevo Modelo

Si quieres trabajar con un modelo nuevo:

```bash
# Ejecutar inspector (interactivo)
python inspect_anylogic_model.py

# Te pide: MODEL_ID o nombre del modelo
# Genera: model_schema.json con estructura del modelo

# Luego crear config.json con la estructura descubierta
```

---

## 📊 Comparativa: test_cloud.py vs launch_simulation.py

| Aspecto | test_cloud.py | launch_simulation.py |
|--------|--------------|----------------------|
| **Configuración** | Hardcoded en código | config.json |
| **Inputs** | 1 parámetro modificado | Múltiples desde JSON |
| **Outputs** | Todos los encontrados | Solo los solicitados |
| **Modelos** | Service System Demo fijo | Cualquiera (vía config) |
| **Validación** | No | Modo strict |
| **CSV** | Todos los outputs | Solo los requeridos |
| **Producción** | ❌ No | ✅ Sí |
| **Reutilizable** | ❌ No | ✅ Sí |
| **Mantenimiento** | Editar código | Editar JSON |

---

## 🔧 Flujo Completo Recomendado

### Para un Modelo Nuevo

```
┌────────────────────────────────────────┐
│ 1. Obtener UUID del modelo             │
│    (desde https://cloud.anylogic.com)  │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 2. Ejecutar inspect_anylogic_model.py  │
│    Descubre inputs/outputs             │
│    Genera model_schema.json            │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 3. Crear config.json                   │
│    - model_id                          │
│    - inputs deseados                   │
│    - outputs a capturar                │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 4. Ejecutar launch_simulation.py       │
│    Lee config.json                     │
│    Lanza simulación                    │
│    Guarda resultados.csv               │
└────────────────────┬───────────────────┘
                     │
           resultados.csv ✅
```

---

## 📝 Archivos de Configuración

### `config.json` (Bass Diffusion Demo)

```json
{
  "model_id": "e13a96db-b9f4-4575-acfe-b5bf0c6767fe",
  "model_name_fallbacks": ["Bass Diffusion Demo", "Bass Diffusion"],
  "experiment": "Experiment",
  "inputs": {},
  "outputs": [
    "Potential adopters and adopters by months|Number of Potential Adopters",
    "Potential adopters and adopters by months|Number of Adopters"
  ],
  "strict_outputs": false
}
```

### `config2.json` (Service System Demo)

```json
{
  "model_id": "1ba2f2f6-7c7f-4067-885a-441bb0bd5d03",
  "model_name_fallbacks": ["Service System Demo", "Service Systems Demo"],
  "experiment": "Baseline",
  "inputs": {
    "Server capacity": 8
  },
  "outputs": [
    "Mean queue size|Mean queue size",
    "Utilization|Server utilization"
  ]
}
```

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| model_id | string | UUID único del modelo en AnyLogic Cloud |
| model_name_fallbacks | array | Nombres alternativos para buscar si ID falla |
| experiment | string | Nombre del experimento a usar |
| inputs | object | Parámetros a configurar (clave: valor) |
| outputs | array | Nombres exactos de salidas a capturar |
| strict_outputs | boolean | Si true, falla si no encuentra todos los outputs |

---

## 📊 Ejemplos de Salida

### Ejecución exitosa

```bash
$ python launch_simulation.py

AnyLogic API key cargada (prefijo): eyJ0eXAi...
Configuración cargada desde config.json
Modelo ID: e13a96db-b9f4-4575-acfe-b5bf0c6767fe
Experimento: Experiment
Usando experimento: Experiment

Lanzando simulación...
Simulación completada.

=== Salidas solicitadas explícitamente ===
- Potential adopters and adopters by months|Number of Potential Adopters: {...}
- Potential adopters and adopters by months|Number of Adopters: {...}
==========================================

Guardado (outputs explícitos): /ruta/a/resultados.csv
Ejecución finalizada.
```

### Archivo CSV generado

```csv
output_name,value
Mean queue size|Mean queue size,0.9988466025848514
Utilization|Server utilization,0.31275860811685163
```

---

## 🔍 Scripts Detallados

### `test_cloud.py` (⚠️ Legacy, no recomendado)

**Propósito:** Prueba simple de integración (debugging)

**Documentación:** [DOCUMENTACION_test_cloud.md](DOCUMENTACION_test_cloud.md)

```bash
python test_cloud.py
# Genera: resultados_serviceSystemDemo.csv
```

---

### `inspect_anylogic_model.py` (🔍 Investigación)

**Propósito:** Descubrir estructura de nuevos modelos

**Documentación:** [DOCUMENTACION_inspect_anylogic_model.md](DOCUMENTACION_inspect_anylogic_model.md)

```bash
python inspect_anylogic_model.py

# Salidas:
# - model_schema.json (estructura del modelo)
# - outputs__raw.json (metadatos de outputs)
# - inputs__dir.json (propiedades de inputs)
# - inputs__dict.json (tipos de inputs)
```

---

### `launch_simulation.py` (🚀 Principal)

**Propósito:** Ejecutar simulaciones de forma genérica y parametrizable

**Documentación:** [DOCUMENTACION_launch_simulation.md](DOCUMENTACION_launch_simulation.md)

```bash
python launch_simulation.py
# Lee: config.json
# Genera: resultados.csv
```

---

## 💡 Casos de Uso

### 1. Captura Regular de Datos (Cron/Scheduler)

```bash
# En crontab: ejecutar cada día a las 9 AM
0 9 * * * cd /ruta/a/Anycloud && python launch_simulation.py >> run.log 2>&1
```

### 2. Múltiples Modelos

```bash
for config in config*.json; do
  cp "$config" config.json
  python launch_simulation.py
  mv resultados.csv "resultados_$(basename $config .json).csv"
done
```

### 3. Validación en CI/CD

```bash
# En pipeline: verificar que modelo sigue ejecutándose
python launch_simulation.py
if [ $? -eq 0 ]; then
  echo "✅ Modelo OK"
else
  echo "❌ Modelo fallido"
  exit 1
fi
```

### 4. Batch Processing

```bash
# Generar múltiples escenarios con diferentes parámetros
python -c "
import json
for capacity in [5, 10, 15, 20]:
  config = json.load(open('config2.json'))
  config['inputs']['Server capacity'] = capacity
  json.dump(config, open('config.json', 'w'))
  os.system('python launch_simulation.py')
"
```

---

## ⚙️ Requisitos del Sistema

- **Python 3.7+**
- **Conexión a internet** (para AnyLogic Cloud)
- **API key válida** de AnyLogic Cloud
- **Librerías Python:**
  - anylogic-cloud-client
  - (no requiere otras dependencias)

### Instalar dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install anylogic-cloud-client
```

---

## 🐛 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `ValueError: No se encontró ANYLOGIC_API_KEY` | `.env` no existe o está vacío | Crear `.env` con API key |
| `FileNotFoundError: No existe config.json` | Config file no está en directorio | Usar `config.json` o `config2.json` |
| `SystemExit: No se encontró ningún modelo` | ID/nombre incorrecto | Verificar UUID en AnyLogic Cloud |
| Outputs vacíos en CSV | Nombres de outputs incorrectos | Ejecutar `inspect_anylogic_model.py` |
| `timeout` | Simulación tarda demasiado | Simplificar modelo o esperar |
| `CloudError: Unauthorized` | API key inválida o expirada | Regenerar key desde AnyLogic |

---

## 📚 Referencias y Documentación

**Documentación de cada script:**
- [DOCUMENTACION_test_cloud.md](DOCUMENTACION_test_cloud.md) - Script de prueba
- [DOCUMENTACION_inspect_anylogic_model.md](DOCUMENTACION_inspect_anylogic_model.md) - Inspector de modelos
- [DOCUMENTACION_launch_simulation.py](DOCUMENTACION_launch_simulation.md) - Lanzador principal

**Referencias externas:**
- [AnyLogic Cloud Documentation](https://cloud.anylogic.com/docs)
- [AnyLogic Python Client](https://anylogic.help/cloud/api/python.html)
- [AnyLogic API Reference](https://cloud.anylogic.com/api)

---

## 🔐 Seguridad

### Credenciales

- **❌ NO** incluir `.env` en Git (agregar a `.gitignore`)
- **✅ SI** usar variables de entorno en producción
- **✅ SI** rotar API keys regularmente
- **✅ SI** limitar permisos de API key a modelos necesarios

### .gitignore

```
.env
.env.local
*.pyc
__pycache__/
resultados*.csv
```

---

## 📈 Ventajas de Esta Solución

✅ **Reutilizable** - Funciona con cualquier modelo sin cambiar código

✅ **Mantenible** - Configuración vía JSON, fácil de versionar

✅ **Automatizable** - Integración con cron, CI/CD, workflows

✅ **Auditable** - Genera CSV con timestamps y valores

✅ **Escalable** - Soporta múltiples modelos y experimentos

✅ **Robusto** - Manejo de errores y validación de datos

✅ **Documentado** - Cada script tiene documentación detallada

---

## 🎓 Ejemplo Completo: De Cero a Ejecución

### 1. Preparación (5 minutos)

```bash
# Clonar/descargar en tu máquina
cd /ruta/a/Anycloud

# Crear .env con tu API key
echo "ANYLOGIC_API_KEY=tu_api_key_aqui" > .env

# Instalar dependencias
pip install anylogic-cloud-client
```

### 2. Exploración (10 minutos)

```bash
# Ver qué modelos están disponibles
# (acude a https://cloud.anylogic.com/models)

# Copiar UUID del modelo deseado (p. ej., Bass Diffusion)
# UUID: e13a96db-b9f4-4575-acfe-b5bf0c6767fe
```

### 3. Investigación (5 minutos)

```bash
# Ejecutar inspector
python inspect_anylogic_model.py

# Seguir prompts interactivos
# Genera: model_schema.json con estructura

# Ver outputs y inputs disponibles
cat model_schema.json
```

### 4. Configuración (5 minutos)

```bash
# Crear config.json con lo descubierto
cat > config.json <<EOF
{
  "model_id": "e13a96db-b9f4-4575-acfe-b5bf0c6767fe",
  "model_name_fallbacks": ["Bass Diffusion Demo"],
  "experiment": "Experiment",
  "inputs": {},
  "outputs": [
    "Potential adopters and adopters by months|Number of Adopters"
  ],
  "strict_outputs": false
}
EOF
```

### 5. Ejecución (1 minuto)

```bash
# Lanzar simulación
python launch_simulation.py

# Ver resultados
cat resultados.csv
```

**¡Hecho en ~25 minutos!** ✅

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisar la documentación del script específico
2. Ejecutar `inspect_anylogic_model.py` para validar modelo
3. Verificar que `.env` tiene API key válida
4. Revisar logs y mensajes de error

---

## 📝 Licencia y Atribuciones

- Cliente oficial: [AnyLogic Cloud Python Client](https://anylogic.help/cloud/api/python.html)
- Modelos de prueba: AnyLogic Cloud
- Documentación: 2026

---

**Última actualización:** Enero 2026  
**Versión:** 1.0  
**Estado:** ✅ Production-ready
