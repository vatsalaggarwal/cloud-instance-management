import typer
from rich import print

from cloud_manager import update_ssh_config
from constants import INSTANCE_NAME, LOCAL_INSTANCE_NAME, PROJECT_ID
from gcp import GCP

gcp = GCP(PROJECT_ID)

app = typer.Typer()


@app.command()
def start():
    print("Starting instance...")
    gcp.start_instance(INSTANCE_NAME)
    print("Instance started. Querying IP...")
    instance_info = gcp.list_instances()[INSTANCE_NAME]
    print("Updating ssh config...")
    update_ssh_config(LOCAL_INSTANCE_NAME, instance_info)


@app.command()
def stop():
    print("Stopping instance...")
    gcp.stop_instance(INSTANCE_NAME)
    print("Instance stopped...")
    
@app.command()
def list():
    print(gcp.list_instances())

if __name__ == "__main__":
    app()