import sys
from typing import Any, Iterable

from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from rich import print

from cloud_instance_management.cloud_manager import (CloudManager,
                                                     update_ssh_config)

# Source of info: https://cloud.google.com/compute/docs/samples/compute-start-instance#compute_start_instance-python
# To parse network info: https://cloud.google.com/compute/docs/instances/view-ip-address#api


class GCP(CloudManager):
    def __init__(self, project_id):
        self.instances_client = compute_v1.InstancesClient()
        self.project_id = project_id

    def _wait_for_extended_operation(
        self,
        operation: ExtendedOperation,
        verbose_name: str = "operation",
        timeout: int = 300,
    ) -> Any:
        """
        Waits for the extended (long-running) operation to complete.

        If the operation is successful, it will return its result.
        If the operation ends with an error, an exception will be raised.
        If there were any warnings during the execution of the operation
        they will be printed to sys.stderr.

        Args:
            operation: a long-running operation you want to wait on.
            verbose_name: (optional) a more verbose name of the operation,
                used only during error and warning reporting.
            timeout: how long (in seconds) to wait for operation to finish.
                If None, wait indefinitely.

        Returns:
            Whatever the operation.result() returns.

        Raises:
            This method will raise the exception received from `operation.exception()`
            or RuntimeError if there is no exception set, but there is an `error_code`
            set for the `operation`.

            In case of an operation taking longer than `timeout` seconds to complete,
            a `concurrent.futures.TimeoutError` will be raised.
        """
        result = operation.result(timeout=timeout)

        if operation.error_code:
            print(
                f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
                file=sys.stderr,
                flush=True,
            )
            print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
            raise operation.exception() or RuntimeError(operation.error_message)

        if operation.warnings:
            print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
            for warning in operation.warnings:
                print(
                    f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True
                )

        return result

    def start_instance(self, instance_name: str):
        """
        When starting the instance, it updates the ssh config file.
        """
        instance_info = self.list_instances()[instance_name]

        # Start the instance
        operation = self.instances_client.start(
            project=self.project_id, zone=instance_info["zone"], instance=instance_name
        )

        self._wait_for_extended_operation(operation, f"instance {instance_name} start")

        # Update the ssh config file with the instance information
        # update_ssh_config(instance)

    def stop_instance(self, instance_name: str):
        """
        Stop the instance
        """
        instance_info = self.list_instances()[instance_name]

        operation = self.instances_client.stop(
            project=self.project_id, zone=instance_info["zone"], instance=instance_name
        )

        self._wait_for_extended_operation(operation, "instance stopping")

    def list_instances(self) -> dict[str, Iterable[compute_v1.Instance]]:
        """
        List all instances in the project.
        """
        instance_client = compute_v1.InstancesClient()
        request = compute_v1.AggregatedListInstancesRequest()
        request.project = self.project_id

        agg_list = instance_client.aggregated_list(request=request)

        all_instances = {}
        for zone, response in agg_list:
            if response.instances:
                for instance in response.instances:
                    instance_info = {}
                    instance_info["status"] = instance.status
                    instance_info["machine_type"] = instance.machine_type.split("/")[-1]
                    instance_info["zone"] = zone.split("/")[-1]

                    if instance.status == "RUNNING":
                        instance_info["ip"] = (
                            instance.network_interfaces[0].access_configs[0].nat_i_p
                        )

                    all_instances[instance.name] = instance_info

        return all_instances

    def start_vs_code_remote(self, gcp_instance_name: str, local_instance_name: str):
        print("Starting VS Code remote...")
        instances = self.list_instances()
        if gcp_instance_name not in instances:
            raise ValueError(f"Instance {gcp_instance_name} does not exist")

        instance = instances[gcp_instance_name]

        if instance["status"] != "RUNNING":
            print("Instance was not running. Starting it now...")
            self.start_instance(gcp_instance_name)
            print("Instance started. Launching VS Code...")
            instance = self.list_instances()[gcp_instance_name]
            update_ssh_config(local_instance_name, instance)

        super().start_vs_code_remote(local_instance_name)
