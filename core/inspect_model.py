"""List the inputs and outputs exposed by an AnyLogic Cloud model."""

import os
import sys
from pathlib import Path

from anylogiccloudclient.client.cloud_client import CloudClient


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_environment_variables():
    """Load credentials and model settings from the local .env file."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        print("ERROR: .env was not found in the project root")
        sys.exit(1)

    with env_path.open("r", encoding="utf-8-sig") as env_file:
        for line in env_file:
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main():
    """Connect to the latest model version and print its public interface."""
    load_environment_variables()
    model_id = (
        sys.argv[1] if len(sys.argv) > 1 else os.getenv("ANYLOGIC_MODEL_ID")
    )
    api_key = os.getenv("ANYLOGIC_API_KEY")

    if not model_id:
        print("ERROR: Pass a model ID or set ANYLOGIC_MODEL_ID in .env")
        return
    if not api_key:
        print("ERROR: ANYLOGIC_API_KEY is not set in .env")
        return

    try:
        client = CloudClient(api_key)
        model = client.get_model_by_id(model_id)
        version = client.get_latest_model_version(model)
        inputs = client.create_default_inputs(version)

        print(f"Model: {model.name}")
        print(f"Version: {version.version}")
        print("\nAvailable inputs")
        for name in inputs.names():
            print(f"- {name}")

        print("\nAvailable outputs")
        try:
            for output in version.get_output_definitions():
                print(f"- {output.name}")
        except Exception:
            print("The client could not list output definitions for this version.")
    except Exception as exc:
        print(f"Could not inspect the model: {exc}")


if __name__ == "__main__":
    main()
