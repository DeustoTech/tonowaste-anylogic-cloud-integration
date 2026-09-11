"""Run TONOWASTE simulations through the AnyLogic Cloud Python client."""

import json
import os

from anylogiccloudclient.client.cloud_client import CloudClient


class AnyLogicWrapper:
    """Provide the small part of the AnyLogic client used by the API."""

    def __init__(self):
        api_key = os.getenv("ANYLOGIC_API_KEY")
        if not api_key:
            raise ValueError("ANYLOGIC_API_KEY is not set")
        self.client = CloudClient(api_key)

    def run_simulation(self, model_id, params, experiment_name="Simulation"):
        """Run the latest model version and return JSON-friendly results."""
        model = self.client.get_model_by_id(model_id)
        version = self.client.get_latest_model_version(model)

        try:
            inputs = self.client.create_inputs_from_experiment(
                version, experiment_name
            )
        except Exception:
            inputs = self.client.create_default_inputs(version)

        for name, value in params.items():
            try:
                inputs.set_input(name, value)
            except Exception as exc:
                raise ValueError(
                    f"AnyLogic Cloud rejected the input parameter '{name}'"
                ) from exc

        simulation = self.client.create_simulation(inputs)
        raw_outputs = simulation.get_outputs_and_run_if_absent()
        results = {}

        for name in raw_outputs.names():
            value = raw_outputs.value(name)
            clean_name = name.replace("root|", "").replace(" ", "_").lower()

            # Some AnyLogic outputs arrive as JSON strings instead of dictionaries.
            if isinstance(value, str) and value.strip().startswith('{"dataX"'):
                try:
                    value = json.loads(value)
                except ValueError:
                    pass

            if isinstance(value, dict) and "dataX" in value:
                results[clean_name] = {
                    "dataX": value["dataX"],
                    "dataY": value["dataY"],
                }
            elif hasattr(value, "get_y_values"):
                results[clean_name] = {
                    "dataX": list(value.get_x_values()),
                    "dataY": list(value.get_y_values()),
                }
            else:
                results[clean_name] = value

        return results
