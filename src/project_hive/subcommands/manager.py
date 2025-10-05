import typer

from services.nats_server import NATSServer
from services.hive_network import HiveNetwork
from services.hive_pod import HivePod
from services.hive_volume import HiveVolume
from services.opensearch_node import OpenSearchNode

app = typer.Typer()

@app.command()
def create():
    print("Creating Open Search Node...")
    HiveNetwork().create_network()
    HiveVolume().create_volume()
    HivePod().create_pod()
    OpenSearchNode().create_opensearch_node(password="$Haveen2004")

@app.command()
def start():
    OpenSearchNode().start_opensearch_node()

@app.command()
def check():
    OpenSearchNode().check_opensearch_node()

@app.command()
def restart():
    OpenSearchNode().restart_opensearch_node()

@app.command()
def stop():
    HivePod().stop_pod()

@app.command()
def delete():
    OpenSearchNode().delete_opensearch_node()
    HivePod().delete_pod()
    HiveNetwork().delete_network()
    HiveVolume().delete_volume()
    
# @app.command()
# def init():
#     pass

# @app.command()
# def start():
#     pass

# @app.command()
# def restart():
#     pass

# @app.command()
# def stop():
#     pass

# @app.command()
# def delete():
#     pass

# @app.command()
# def status():
#     pass