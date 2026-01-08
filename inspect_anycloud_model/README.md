# Inspeccionar Modelos AnyLogic Cloud

## 📋 Resumen

Script de **inspección automática** para descubrir inputs y outputs de cualquier modelo en AnyLogic Cloud. Ejecuta una simulación de prueba y genera un esquema JSON con la estructura completa del modelo.

**Propósito:** Descubrir qué parámetros y resultados tiene un modelo sin acceder manualmente a la interfaz web

**Estado:** ✅ Production-ready para investigación

---

## 🎯 Objetivo Principal
Proporcionar una forma **robusta y flexible** de descubrir qué inputs y outputs tiene un modelo en AnyLogic Cloud, sin necesidad de acceder manualmente a la interfaz web. Es especialmente útil cuando:
- El modelo tiene muchos parámetros
- Necesitas automatizar la integración con AnyLogic Cloud
- Quieres documentar el esquema del modelo programáticamente

---

## 🔧 Funcionalidades

### 1. **Carga de Credenciales** (líneas 54-64)
```python
load_env_from(BASE_DIR / ".env")
API_KEY = os.getenv("ANYLOGIC_API_KEY")
```
- Lee variables de entorno desde archivo `.env`
- Obtiene la clave API necesaria para autenticarse con AnyLogic Cloud
- **Requisito:** Crear un archivo `.env` con: `ANYLOGIC_API_KEY=tu_api_key`

### 2. **Identificación del Modelo** (líneas 67-84)
- Permite identificar un modelo por:
  - **ID directo** (`MODEL_ID` en config.json)
  - **Nombre** (fallbacks de nombres alternativos)
  - **Input interactivo**: Si no está configurado, pide al usuario introducir ID o nombre

### 3. **Búsqueda de Experimentos** (líneas 119-135)
- Intenta crear inputs desde diferentes **experimentos** del modelo:
  - "Simulation", "Baseline", "Main", "Experiment", "Default"
- Usa el primero que encuentre
- Si ninguno funciona, crea inputs por defecto

### 4. **Enumeración de Inputs** (líneas 139-173)
Tres métodos progresivos para listar inputs:
1. **API pública** (`inputs.get_inputs()`)
2. **Dict interno** (`inputs.inputs`)
3. **Introspección** (dir, __dict__) – como fallback para APIs privadas/versiones antiguas

Guarda resultados en: `inputs__dir.json`, `inputs__dict.json`

### 5. **Ejecución y Enumeración de Outputs** (líneas 178-253)
Cuatro métodos para extraer outputs:
1. **get_outputs()** - API pública
2. **Dict interno** (`outputs.outputs`)
3. **Métodos agregados** (`get_values()`, `to_json()`, `as_json()`)
4. **Raw outputs** (`get_raw_outputs()`) – para APIs antiguas/privadas

También ejecuta una simulación de prueba para capturar valores de ejemplo.

Guarda resultados en: `outputs__raw.json`, `outputs__dir.json`, `outputs__dict.json`

### 6. **Generación de Esquema y Documentación** (líneas 258-272)
Genera dos archivos JSON principales:
- **`model_schema.json`**: Estructura del modelo (id, experimento usado, inputs, outputs)
- **`outputs_values.json`**: Valores de ejemplo de outputs (resultado de la simulación de prueba)

---

## 📁 Archivos de Entrada

### `.env` (obligatorio)
```
ANYLOGIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

### `config.json` (opcional)
```json
{
  "model_id": "abc123",
  "model_name_fallbacks": ["MyModel", "MyModel_v2"],
  "experiment": "Simulation"
}
```

---

## 📁 Archivos de Salida

| Archivo | Contenido |
|---------|-----------|
| `model_schema.json` | ID modelo, experimento usado, lista de inputs, lista de outputs |
| `outputs_values.json` | Valores de los outputs obtenidos de la simulación |
| `inputs__dir.json` | Listado de propiedades/métodos del objeto inputs (introspección) |
| `inputs__dict.json` | Tipos de atributos internos de inputs |
| `outputs__raw.json` | Metadatos de raw outputs (name, title, path, id, descriptor) |
| `outputs__dir.json` | Listado de propiedades/métodos del objeto outputs |
| `outputs__dict.json` | Tipos de atributos internos de outputs |

---

## 🚀 Modo de Uso

### 1. **Instalación de dependencias**
```bash
pip install anylogic-cloud-client
```

### 2. **Configuración**
Crear archivo `.env` en el mismo directorio que el script:
```
ANYLOGIC_API_KEY=tu_clave_api_aqui
```

### 3. **Ejecución**
```bash
# Modo con config.json preconfigurado
python inspect_anylogic_model.py

# O responder preguntas interactivas si no existe config.json
# Te pedirá: MODEL_ID o nombre del modelo
```

### 4. **Salida en terminal**
El script imprime:
- ✅ Inputs disponibles
- ✅ Outputs disponibles  
- ✅ Valores de ejemplo
- ✅ Mensajes de depuración útiles

---

## 🔍 Detalles Técnicos

### Funciones Auxiliares

#### `load_env_from(path)`
Carga variables de entorno desde un archivo `.env`
- Ignora líneas vacías y comentarios (#)
- Soporta valores entrecomillados

#### `safe_dir(obj)`
Wrapper seguro de `dir()` que:
- Filtra atributos privados (_xxx)
- Ordena alfabéticamente
- Maneja excepciones

#### `try_attr(obj, name, default=None)`
Obtiene atributos con seguridad ante excepciones

#### `dump_json(path, data)`
Guarda datos a JSON con encoding UTF-8 y formato indentado

#### `print_kv_block(title, items)`
Imprime diccionarios formateados en terminal

---

## 🛡️ Manejo de Errores

El script es **robusto ante cambios de API**:
- Si `get_inputs()` falla, intenta acceso directo a dict interno
- Si API pública no funciona, hace introspección (`__dict__`, `__dir__`)
- Excepciones capturadas y manejadas sin romper el flujo
- Mensaje claro si no se puede acceder al modelo

---

## 📊 Ejemplo de Salida

### Terminal
```
API key (prefijo): abc12345...
MODEL_ID: - | NAME_FALLBACKS: ['MySimulation']
Experimentos a probar: ['Simulation', 'Baseline', 'Main', ...]

Inputs creados desde experimento: Simulation

=== INPUTS DISPONIBLES ===
- parameter1
- parameter2
- parameter3

Simulación ejecutada para inspeccionar outputs.

=== OUTPUTS DISPONIBLES ===
- result_metric1
- result_metric2
- result_metric3

📝 dump -> ./model_schema.json
📝 dump -> ./outputs_values.json

Hecho. Además de los JSON, ya has visto en terminal los campos más útiles.
   Usa esos nombres exactos en tu config.json (inputs/outputs) para el lanzador genérico.
```

### `model_schema.json`
```json
{
  "model_id": "model123",
  "used_experiment": "Simulation",
  "inputs": ["parameter1", "parameter2", "parameter3"],
  "outputs": ["result_metric1", "result_metric2", "result_metric3"]
}
```

### `outputs_values.json`
```json
{
  "result_metric1": 42.5,
  "result_metric2": "success",
  "result_metric3": 123
}
```

---

## 🔗 Dependencias Externas

- **anylogiccloudclient**: Cliente oficial de AnyLogic Cloud para Python
  - Proporciona: `CloudClient`, `CloudError`
  - Manejo de autenticación, modelos y simulaciones

---

## 💡 Casos de Uso

1. **Automatizar integración con AnyLogic Cloud**
   - Descubrir inputs/outputs sin interfaz web
   - Generar documentación automática

2. **QA/Testing**
   - Validar que inputs/outputs de un modelo están correctamente configurados
   - Capturar cambios entre versiones del modelo

3. **Documentación**
   - Crear ficha técnica del modelo (inputs, outputs, rango de valores)
   - Audit trail de modelos disponibles en Cloud

4. **Desarrollo de aplicaciones**
   - Consumir el `model_schema.json` para construir UIs dinámicas
   - Validar parámetros antes de enviar a AnyLogic Cloud

---

## ⚙️ Requisitos del Sistema

- **Python 3.7+**
- **Acceso a AnyLogic Cloud** (API key válida)
- **Conexión a internet** (comunicación con servidores de AnyLogic)
- **Permisos de lectura** en el modelo (para `get_latest_model_version`)

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| `ANYLOGIC_API_KEY no encontrada` | Crear `.env` con la clave en el mismo directorio |
| `No se pudo acceder al modelo` | Verificar MODEL_ID / nombre exacto del modelo |
| Outputs vacíos | El modelo puede no tener outputs públicos. Revisar versión/configuración |
| Archivos JSON no se generan | Verificar permisos de escritura en el directorio |

---

## 📝 Notas Importantes

- El script **no modifica el modelo**, solo lo inspecciona (lectura)
- La **ejecución de simulación es necesaria** para obtener outputs
- Los archivos JSON generados son **sobreescritos en cada ejecución**
- Compatible con **múltiples versiones de anylogic-cloud-client**


