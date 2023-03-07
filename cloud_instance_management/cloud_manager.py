import os
from abc import abstractmethod
from typing import Any


def update_ssh_config(instance_name: str, instance_info: dict[str, Any]):
    config_file = os.path.expanduser("~/.ssh/config")
    instance_ip = instance_info["ip"]

    with open(config_file) as f:
        config = f.read()
        if f"Host {instance_name}\n" not in config:
            raise ValueError(f"Host {instance_name} not found in ssh config file")
        else:
            # If there is a section for the host, find its index and update its HostName value
            start_index = config.index(f"Host {instance_name}\n")
            end_index = (
                config.index("\n\n", start_index)
                if "\n\n" in config[start_index:]
                else len(config)
            )
            host_section = config[start_index:end_index]

            hostname_index = host_section.find("HostName ") + len("HostName ")
            next_line_index = host_section.find("\n", hostname_index)
            current_hostname = host_section[hostname_index:next_line_index]

            new_config = (
                config[: start_index + hostname_index]
                + f"{instance_ip}"
                + host_section[next_line_index:]
                + config[end_index:]
            )
            new_config = new_config.strip()

            with open(config_file, "w") as f:
                f.write(new_config)


class CloudManager:
    def __init__(self, cloud):
        pass

    @abstractmethod
    def start_instance(self, instance):
        """
        When starting the instance, it updates the ssh config file.
        """
        pass

    @abstractmethod
    def stop_instance(self, instance):
        pass

    @abstractmethod
    def list_instances(self):
        pass

    def start_vs_code_remote(self, local_instance_name):
        # Ref: https://code.visualstudio.com/docs/remote/troubleshooting#_connect-to-a-remote-host-from-the-terminal
        os.system(f"code -n --remote ssh-remote+{local_instance_name}")
