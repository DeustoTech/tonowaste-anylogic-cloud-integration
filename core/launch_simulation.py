"""Run an AnyLogic Cloud simulation directly from the command line."""

import csv
import json
import os
import sys
from pathlib import Path

from anylogiccloudclient.client.cloud_client import CloudClient


CORE_DIR = Path(__file__).resolve().parent
ROOT_DIR = CORE_DIR.parent
OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_environment_variables():
    """Load the local environment file without adding another dependency."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        print("ERROR: .env was not found")
        sys.exit(1)

    with env_path.open("r", encoding="utf-8-sig") as env_file:
        for line in env_file:
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


def get_config_path():
    """Use the command-line path or the configured default JSON file."""
    config_name = os.getenv("DEFAULT_CONFIG", "service_system.json")
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    return ROOT_DIR / "configs" / config_name


def setup_cloud_client():
    """Create an authenticated AnyLogic Cloud client."""
    api_key = os.getenv("ANYLOGIC_API_KEY")
    if not api_key:
        print("ERROR: ANYLOGIC_API_KEY is not set in .env")
        sys.exit(1)
    return CloudClient(api_key)


def get_model_inputs(client, model_id, experiment_name):
    """Load the latest model version and prepare its inputs."""
    model = client.get_model_by_id(model_id)
    version = client.get_latest_model_version(model)
    version_number = version.version if version else "N/A"
    print(f"Connected to {model.name}, version {version_number}")

    try:
        inputs = client.create_inputs_from_experiment(version, experiment_name)
        print(f"Using experiment '{experiment_name}'")
    except Exception:
        inputs = client.create_default_inputs(version)
        print("The experiment was not found. Using the model defaults.")

    return inputs, version


def configure_parameters(inputs, parameters):
    """Apply values from the JSON configuration to the model inputs."""
    print("\nInput values")
    for name, value in parameters.items():
        try:
            inputs.set_input(name, value)
            print(f"{name} = {value}")
        except Exception:
            print(f"Could not set '{name}'. The model default will be used.")
    return inputs


def process_outputs(outputs):
    """Convert common AnyLogic output types into simple values."""
    data = {}
    for name in outputs.names():
        value = outputs.value(name)
        clean_name = name.split("|")[-1]

        if isinstance(value, dict) and "dataY" in value:
            data[f"{clean_name} (Final)"] = (
                value["dataY"][-1] if value["dataY"] else 0
            )
        elif isinstance(value, dict) and "mean" in value:
            data[f"{clean_name} (Mean)"] = value["mean"]
        else:
            data[clean_name] = value
    return data


def save_to_csv(results, config_stem):
    """Save the processed results in the local outputs directory."""
    csv_path = OUTPUT_DIR / f"results_{config_stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["Metric", "Value"])
        writer.writerows(results.items())
    return csv_path


def main():
    """Load the configuration, run the model, and save its results."""
    load_environment_variables()
    config_path = get_config_path()

    if not config_path.exists():
        print(f"ERROR: {config_path} does not exist")
        return

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except Exception as exc:
        print(f"ERROR: Could not read the JSON configuration: {exc}")
        return

    model_id = config.get("model_id") or os.getenv("ANYLOGIC_MODEL_ID")
    if not model_id:
        print("ERROR: Set model_id in the configuration or ANYLOGIC_MODEL_ID")
        return

    client = setup_cloud_client()
    inputs, _ = get_model_inputs(
        client,
        model_id,
        config.get("experiment", "Simulation"),
    )
    configure_parameters(inputs, config.get("inputs", {}))

    print("\nRunning the simulation in AnyLogic Cloud...")
    try:
        simulation = client.create_simulation(inputs)
        raw_outputs = simulation.get_outputs_and_run_if_absent()
        results = process_outputs(raw_outputs)
        csv_path = save_to_csv(results, config_path.stem)
        print("\nSimulation completed")
        print(f"Results saved to {csv_path.name}")
    except Exception as exc:
        print(f"The simulation failed: {exc}")


if __name__ == "__main__":
    main()
