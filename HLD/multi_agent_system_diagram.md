```mermaid
graph TD
    subgraph User Interaction
        User[👨‍💻 DevOps Engineer]
    end

    subgraph ADK Agent System
        direction LR
        Orchestrator[
            🤖 DevOps Orchestrator Agent
            (agent.py)
        ]

        subgraph Specialized Agents (Tools & Sub-Agents)
            direction TB
            SearchAgent[🔎 Search Agent]
            CodingAgent[🧮 Coding Agent]
            MonitoringAgent[📈 Monitoring Agent]
            KubectlAgent[☸️ Kubectl-AI Agent]
            ElasticsearchAgent[📜 Elasticsearch Agent]
            CICDAgent[🚀 CI/CD Agent]
            InfraAgent[☁️ Infrastructure Agent]
            DeployAgent[📦 Deployment Agent]
        end
    end

    subgraph MCP Servers (Tool Providers)
        direction TB
        ThanosMCP[📊 Thanos MCP Server]
        KubectlMCP[⚙️ Kubectl-AI MCP Server]
        ElasticsearchMCP[🗄️ Elasticsearch MCP Server]
    end

    subgraph Backend DevOps Systems
        direction TB
        Thanos[<img src='https://thanos.io/icon.svg' width='20' /> Thanos / Prometheus]
        Kubernetes[<img src='https://kubernetes.io/images/favicon.png' width='20' /> OpenShift / Kubernetes API]
        Elasticsearch[<img src='https://www.elastic.co/favicon.ico' width='20' /> Elasticsearch Cluster]
        WebSearch[🌐 Web Search API]
        PythonREPL[🐍 Python REPL]
    end

    %% --- Connections ---

    %% User to Orchestrator
    User -- "Sends Request" --> Orchestrator

    %% Orchestrator to Agents
    Orchestrator -- "Delegates to / Uses" --> SearchAgent
    Orchestrator -- "Delegates to / Uses" --> CodingAgent
    Orchestrator -- "Delegates to / Uses" --> MonitoringAgent
    Orchestrator -- "Delegates to / Uses" --> KubectlAgent
    Orchestrator -- "Delegates to / Uses" --> ElasticsearchAgent
    Orchestrator -- "Delegates to / Uses" --> CICDAgent
    Orchestrator -- "Delegates to / Uses" --> InfraAgent
    Orchestrator -- "Delegates to / Uses" --> DeployAgent

    %% Agents to MCP Servers
    MonitoringAgent      -- "Uses Tools From" --> ThanosMCP
    KubectlAgent         -- "Uses Tools From" --> KubectlMCP
    ElasticsearchAgent   -- "Uses Tools From" --> ElasticsearchMCP

    %% Simple Agents to Backends
    SearchAgent -- "Interacts with" --> WebSearch
    CodingAgent -- "Executes in" --> PythonREPL

    %% MCP Servers to Backends
    ThanosMCP -- "Queries" --> Thanos
    KubectlMCP -- "Executes 'oc' against" --> Kubernetes
    ElasticsearchMCP -- "Queries" --> Elasticsearch

    %% --- Styling ---
    classDef agent fill:#D6EAF8,stroke:#3498DB,stroke-width:2px
    classDef mcp fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px
    classDef backend fill:#FDEDEC,stroke:#E74C3C,stroke-width:2px

    class Orchestrator,SearchAgent,CodingAgent,MonitoringAgent,KubectlAgent,ElasticsearchAgent,CICDAgent,InfraAgent,DeployAgent agent
    class ThanosMCP,KubectlMCP,ElasticsearchMCP mcp
    class Thanos,Kubernetes,Elasticsearch,WebSearch,PythonREPL backend
```
