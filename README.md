# TONOWASTE AnyLogic Cloud API Service

FastAPI service that runs AnyLogic Cloud simulations and exposes them through REST endpoints.

## Project files

- `docker-compose.yml`: local deployment.
- `portainer/docker-compose.yml`: Portainer stack template with Traefik labels.
- `portainer/stack.env.template`: Portainer environment variable template.
- `build/build_and_push.sh`: build and push image script.
- `scripts/service_anylogic.py`: API app (`/simulate`, `/health`).

## 1. Deploy in local (Docker Compose)

1. Create local env file:

```bash
cp .env.template .env
```

2. Fill required variables in `.env`:

```env
ANYLOGIC_API_KEY=your_real_api_key
ANYLOGIC_MODEL_ID=your_model_id
```

3. Build and start:

```bash
docker compose up -d --build
```

4. Validate:

```bash
docker compose ps
curl http://localhost:8000/health
```

5. Open docs:

- `http://localhost:8000/docs`

## 2. Build and push image to Docker Hub

Use the script:

```bash
./build/build_and_push.sh
```

Required `.env` variables for this script:

```env
IMAGE_NAME=tonowaste-anylogic-cloud-integration
IMAGE_TAG=1.0.1beta
REGISTRY_NS=your_dockerhub_user_or_org
REGISTRY_USERNAME=your_dockerhub_user
REGISTRY_PASSWORD=your_dockerhub_token_or_password
```

The script:

1. Builds image locally.
2. Logs in to registry.
3. Tags image as `${REGISTRY_NS}/${IMAGE_NAME}:${IMAGE_TAG}`.
4. Pushes the image.

## 3. Deploy in Portainer

Use:

- Stack file: `portainer/docker-compose.yml`
- Env template: `portainer/stack.env.template`

### Required in Portainer environment

```env
REGISTRY_NS=your_dockerhub_user_or_org
IMAGE_TAG=1.0.1beta
ANYLOGIC_API_KEY=your_real_api_key
ANYLOGIC_MODEL_ID=your_model_id
DEFAULT_CONFIG=tonowaste.json
UVICORN_WORKERS=1
UVICORN_LOG_LEVEL=info
```

### Notes

- `traefik-proxy_web` must exist as an external Docker network in that host.
- Traefik route is configured for:
  - `https://api.sd.tools.tonowaste.eu`
- Internal service port is `8000`.

### Portainer deployment steps

1. Go to `Stacks` -> `Add stack`.
2. Paste `portainer/docker-compose.yml`.
3. Add environment variables from `portainer/stack.env.template` with real values.
4. Deploy stack.
5. Verify:
   - `https://api.sd.tools.tonowaste.eu/health`
   - `https://api.sd.tools.tonowaste.eu/docs`

## API quick test

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
      "ppWasteRate": 0.2400,
      "exPost1FLW": 0.39,
      "exPost2FLW": 0.29
    }
  }'
```

The API always uses `ANYLOGIC_MODEL_ID` from environment.
