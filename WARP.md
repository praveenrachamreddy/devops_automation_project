# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Architecture

This project is a DevOps Automation Assistant built with a multi-agent system using the Google Agent Development Kit (ADK). The core of the project is a FastAPI server that provides a web interface and API endpoints for interacting with the agents.

The agent system is composed of:
- **Orchestrator Agent (Root Agent):** The central decision-maker that routes tasks to the appropriate specialized agents.
- **Specialized Agents:**
    - **Simple Task Agents:** Handle tasks like web searches and code execution.
    - **Sub-agents:** Handle more complex, specialized tasks like:
        - **Elasticsearch Agent:** Analyzes logs stored in Elasticsearch.
        - **CI/CD Pipeline Agent:** Manages CI/CD operations (TODO).
        - **Infrastructure Agent:** Manages infrastructure provisioning (TODO).
        - **Monitoring Agent:** Monitors system health and performance (TODO).
        - **Deployment Agent:** Handles application deployments (TODO).

The system uses a `config.yaml` file for configuration, including agent settings, API keys, and connection parameters for various services.

## Common Development Tasks

### Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables:**
    Create a `.env` file and add the necessary environment variables, such as `GOOGLE_API_KEY`. See `.env.example` for a template.

### Running the application

-   **Start the FastAPI server:**
    ```bash
    python main.py
    ```
    The server will be available at `http://localhost:8000`.

### Running tests

-   **Run all tests:**
    ```bash
    pytest
    ```
-   **Run a specific test file:**
    ```bash
    pytest tests/test_agents.py
    ```

### Linting

This project does not have a pre-configured linter. You can add one, such as `flake8` or `black`.


