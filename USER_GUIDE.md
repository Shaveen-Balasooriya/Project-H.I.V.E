# Project H.I.V.E User Guide - Starting the Application

This guide provides instructions on how to start the different components of the Project H.I.V.E application.

## Prerequisites

Before starting, ensure you have Python installed and have installed the necessary dependencies for each component, typically found in a `requirements.txt` file within each component's directory (e.g., `frontend`, `honeypot_manager`, `log_manager`). You might need to run `pip install -r requirements.txt` in each directory.

It's recommended to run each component in a separate terminal window.

## 1. Starting the Honeypot Manager API

The Honeypot Manager is a FastAPI application responsible for creating, managing, and monitoring honeypot containers.

1.  **Navigate to the Honeypot Manager directory:**
    ```bash
    cd d:\shave\Documents\repos\Project-H.I.V.E\honeypot_manager
    ```
2.  **Start the Uvicorn server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8081 --reload
    ```
    *   `--host 0.0.0.0`: Makes the API accessible from other machines on the network.
    *   `--port 8081`: Specifies the port the API will run on.
    *   `--reload`: Enables auto-reloading when code changes (useful for development).

The Honeypot Manager API will be running at `http://localhost:8081`. You can access its documentation at `http://localhost:8081/docs`.

## 2. Starting the Log Manager API

The Log Manager (assuming a similar structure to the Honeypot Manager) is likely a FastAPI application responsible for collecting and managing logs from honeypots.

1.  **Navigate to the Log Manager directory:**
    ```bash
    cd d:\shave\Documents\repos\Project-H.I.V.E\log_manager 
    ```
    *(Note: Adjust the directory name if it differs)*
2.  **Start the Uvicorn server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload 
    ```
    *(Note: The port `8080` is assumed; check the `log_manager/main.py` file if it exists for the correct port)*

The Log Manager API will likely be running at `http://localhost:8080`.

## 3. Starting the Frontend Application

The Frontend is a Flask application that provides the web interface for interacting with the Honeypot Manager and viewing data.

1.  **Navigate to the Frontend directory:**
    ```bash
    cd d:\shave\Documents\repos\Project-H.I.V.E\frontend
    ```
2.  **Start the Flask development server:**
    ```bash
    python app.py
    ```

The Frontend application will be running at `http://localhost:5000`. Open this address in your web browser to access the Project H.I.V.E interface. The application connects to the Honeypot Manager API (running on port 8081 by default, check `frontend/config.py` or similar if needed).
