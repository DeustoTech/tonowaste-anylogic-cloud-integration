# TONOWASTE AnyLogic Cloud API

Version 2.0.0. Last updated on September 11, 2026.

This project provides a small FastAPI service for running the TONOWASTE model in
AnyLogic Cloud. It keeps the AnyLogic API key and model ID on the server, so API
clients only need to send the simulation inputs.

## API endpoints

- `GET /health` checks whether the service is running.
- `POST /simulate` runs the original input contract.
- `POST /simulate2` runs the same simulation and also requires
  `AverageDailyConsumption`.
- `GET /docs` opens the interactive API documentation.

The service always uses the latest version of the model identified by
`ANYLOGIC_MODEL_ID`. If the requested experiment does not exist in that version,
the service uses the model's default inputs.

## Run the service locally

Create `.env` from the template if you do not already have one:

```bash
cp .env.template .env
```

Set at least these two values:

```env
ANYLOGIC_API_KEY=your_real_api_key
ANYLOGIC_MODEL_ID=your_model_id
```

Do not commit `.env`. It contains credentials that must remain private.

Build and start the service:

```bash
docker compose up -d --build
```

Check that it is healthy:

```bash
docker compose ps
curl http://localhost:8000/health
```

The health endpoint should return:

```json
{"status":"ok"}
```

Open `http://localhost:8000/docs` to test the endpoints from your browser.

## Run a simulation

Use `/simulate` for clients that use the original contract:

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "experiment": "Simulation",
    "inputs": {
      "hhWasteRate": 0.2196,
      "fsWasteRate": 0.2156,
      "rdWasteRate": 0.0292,
      "pmWasteRate": 0.4595,
      "ppWasteRate": 0.24,
      "exPost1FLW": 0.39,
      "exPost2FLW": 0.29
    }
  }'
```

Use `/simulate2` when the client can provide average daily consumption:

```bash
curl -X POST http://localhost:8000/simulate2 \
  -H "Content-Type: application/json" \
  -d '{
    "experiment": "Simulation",
    "inputs": {
      "hhWasteRate": 0.2196,
      "fsWasteRate": 0.2156,
      "rdWasteRate": 0.0292,
      "pmWasteRate": 0.4594,
      "ppWasteRate": 0.24,
      "exPost1FLW": 0.39,
      "exPost2FLW": 0.29,
      "AverageDailyConsumption": 1.563
    }
  }'
```

`AverageDailyConsumption` is required by `/simulate2`. FastAPI returns HTTP 422
when it is missing or is not a number. Swagger preloads the example with a value
of `1.563`, but clients must still include the field in their requests.

## Test the model from the command line

The repository includes two small development tools:

```bash
python core/inspect_model.py
python core/launch_simulation.py configs/tonowaste.json
```

`inspect_model.py` lists the inputs and outputs exposed by the latest model
version. `launch_simulation.py` runs a simulation directly, without starting the
FastAPI service.

To test the running API and create CSV files from its time-series outputs, run:

```bash
python core/test_local_api.py
```

## Configuration

The local service reads these settings from `.env`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `ANYLOGIC_API_KEY` | Authenticates requests to AnyLogic Cloud. | Required |
| `ANYLOGIC_MODEL_ID` | Selects the AnyLogic Cloud model. | Required |
| `DEFAULT_CONFIG` | Selects a file from `configs/`. | `tonowaste.json` |
| `API_PORT` | Publishes the service on the host. | `8000` |
| `UVICORN_WORKERS` | Sets the number of API worker processes. | `1` |
| `UVICORN_LOG_LEVEL` | Sets the API log level. | `info` |

The remaining registry variables are only needed when publishing a Docker image.

## Build and publish the Docker image

Set the registry values in `.env`:

```env
IMAGE_NAME=tonowaste-anylogic-cloud-integration
IMAGE_TAG=1.0.1beta
REGISTRY_NS=your_dockerhub_user_or_org
REGISTRY_USERNAME=your_dockerhub_user
REGISTRY_PASSWORD=your_dockerhub_token_or_password
```

Then run:

```bash
./build/build_and_push.sh
```

The script builds the image, signs in to the registry, tags the image, and pushes
it to the configured namespace.

## Deploy with Portainer

Use `portainer/docker-compose.yml` as the stack definition and copy the values
from `portainer/stack.env.template` into the Portainer environment settings.

The deployment expects an existing external Docker network named
`traefik-proxy_web`. Its Traefik labels publish the service at
`https://api.sd.tools.tonowaste.eu`.

After deploying, check:

- `https://api.sd.tools.tonowaste.eu/health`
- `https://api.sd.tools.tonowaste.eu/docs`

## Main project files

- `scripts/service_anylogic.py` defines the FastAPI schemas and endpoints.
- `core/anylogic_wrapper.py` communicates with AnyLogic Cloud.
- `core/launch_simulation.py` runs a model directly from a JSON configuration.
- `core/inspect_model.py` shows the inputs and outputs available in Cloud.
- `core/test_local_api.py` tests the local API and saves selected results as CSV.
- `docker-compose.yml` runs the service locally.
- `portainer/docker-compose.yml` defines the production stack.
