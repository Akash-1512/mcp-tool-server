# Architecture

## System Diagram
```mermaid
graph TD
    U[👤 User] -->|chat message| UI[Streamlit Chat UI\nchat_ui.py]
    UI -->|LangChain message| A

    subgraph mcp_network [Docker Network: mcp_network]

        subgraph agent_container [Container: mcp_agent]
            A[LangGraph Agent\nlanggraph_agent.py]
            TD[Tool Discovery\ntool_discovery.py]
            A --> TD
        end

        subgraph server_container [Container: mcp_server]
            F[FastAPI App\nmain.py]
            JW[JWT Middleware\nauth/jwt_middleware.py]
            RL[Registry Loader\nregistry/registry_loader.py]
            TY[tool_registry.yaml]
            SQL[sql_tool.py]
            WS[search_tool.py]
            FS[filesystem_tool.py]
            REST[rest_api_tool.py]

            F --> JW
            JW -->|validated| RL
            RL --> TY
            RL --> SQL
            RL --> WS
            RL --> FS
            RL --> REST
        end

        subgraph db_container [Container: mcp_db]
            PG[(PostgreSQL 16\nProcurement Schema)]
        end

        TD -->|POST initialize\nPOST tools/list| F
        A  -->|POST tools/call| F
        SQL --> PG
    end

    WS  -->|HTTPS| TAV[🌐 Tavily Search API]
    REST -->|HTTPS| EXT[🌐 External REST APIs]

    style mcp_network fill:#0f172a,stroke:#38bdf8,color:#e2e8f0
    style agent_container fill:#1e293b,stroke:#64748b,color:#e2e8f0
    style server_container fill:#1e293b,stroke:#64748b,color:#e2e8f0
    style db_container fill:#1e293b,stroke:#64748b,color:#e2e8f0
```

## Procurement Database Schema
```mermaid
erDiagram
    spend_categories {
        int id PK
        varchar category_code UK
        varchar category_name
        varchar parent_category
        varchar spend_type
        varchar commodity_code
    }

    vendors {
        int id PK
        varchar vendor_code UK
        varchar vendor_name
        varchar category_code FK
        varchar country
        char currency
        varchar tier
        varchar status
        varchar payment_terms
    }

    contracts {
        int id PK
        varchar contract_number UK
        int vendor_id FK
        varchar title
        numeric contract_value
        char currency
        date start_date
        date end_date
        boolean auto_renewal
        varchar status
    }

    purchase_orders {
        int id PK
        varchar po_number UK
        int vendor_id FK
        int contract_id FK
        varchar category_code FK
        varchar department
        varchar buyer_name
        numeric total_amount
        char currency
        varchar status
        varchar priority
        date created_at
        date required_by
    }

    po_line_items {
        int id PK
        int po_id FK
        int line_number
        varchar material_code
        varchar description
        numeric quantity
        numeric unit_price
        numeric line_total
        char currency
        varchar delivery_status
        date expected_delivery
        date actual_delivery
    }

    approval_workflow {
        int id PK
        int po_id FK
        int level
        varchar approver_name
        varchar approver_role
        varchar decision
        timestamp decided_at
    }

    spend_categories ||--o{ vendors : "categorises"
    vendors ||--o{ contracts : "has"
    vendors ||--o{ purchase_orders : "receives"
    contracts ||--o{ purchase_orders : "covers"
    spend_categories ||--o{ purchase_orders : "classifies"
    purchase_orders ||--o{ po_line_items : "contains"
    purchase_orders ||--o{ approval_workflow : "routed through"
```

## Container Networking

All services run on the Docker bridge network `mcp_network`.

- **agent → mcp-server**: `http://mcp-server:8000` — Docker internal DNS resolves
  the service name declared in `docker-compose.yml` to the container IP
- **mcp-server → db**: `db:5432` — same DNS mechanism
- **mcp-server → external**: Tavily API and REST endpoints called over HTTPS,
  egress through the host's network stack
- No container is addressable by IP directly — always use service names

## MCP Request Flow
```
1.  User types message in Streamlit UI
2.  LangGraph agent receives message, enters ReAct loop
3.  On first run: agent sends initialize → notifications/initialized → tools/list
4.  Agent receives tool manifest (sql_query, web_search, filesystem_search, rest_api_search)
5.  LLM selects tool, agent sends tools/call with JSON arguments
6.  JWT middleware validates Bearer token — rejects if missing/expired
7.  Registry loader routes call to correct handler module
8.  Handler executes against real data source (PostgreSQL / Tavily / filesystem)
9.  Result returned as MCP JSON-RPC tools/call response
10. Agent incorporates result, continues ReAct loop or returns final answer
11. Streamlit UI renders final answer + full tool call trace panel
```