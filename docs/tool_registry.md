# Tool Registry Schema

Tools are declared in `mcp_server/registry/tool_registry.yaml`.
The registry loader parses this file at server startup and registers
each tool as an MCP-compatible endpoint.

## Schema
```yaml
tools:
  - name: string               # unique tool identifier (snake_case)
    description: string        # shown to the LLM during tool selection
    enabled: bool              # false = loaded but not exposed via MCP
    auth_required: bool        # if true, JWT must be present in request
    handler: string            # Python dotted path to the handler function
    input_schema:              # JSON Schema for tool arguments
      type: object
      properties:
        param_name:
          type: string|integer|boolean|array|object
          description: string
      required: [list of required param names]
    output_schema:             # JSON Schema for tool response (documentation)
      type: object
      properties: {}
    metadata:
      category: string         # sql | search | filesystem | web
      timeout_seconds: int     # max execution time before error
      rate_limit_per_min: int  # 0 = unlimited
```

## Example Entry
```yaml
tools:
  - name: sql_query
    description: >
      Execute a read-only SQL SELECT statement against the enterprise
      database. Returns rows as a list of JSON objects. Never modifies data.
    enabled: true
    auth_required: true
    handler: mcp_server.tool_handlers.sql_tool.run_sql_query
    input_schema:
      type: object
      properties:
        query:
          type: string
          description: A valid SQL SELECT statement.
        limit:
          type: integer
          description: Maximum rows to return. Defaults to 50.
      required:
        - query
    output_schema:
      type: object
      properties:
        rows:
          type: array
        row_count:
          type: integer
        execution_time_ms:
          type: number
    metadata:
      category: sql
      timeout_seconds: 10
      rate_limit_per_min: 30
```

## Planned Tools

| Tool Name | Category | Description |
|---|---|---|
| `sql_query` | sql | Read-only SQL query against PostgreSQL |
| `rest_api_search` | search | Query an external REST API endpoint |
| `filesystem_search` | filesystem | Search files by name/content in allowed paths |
| `web_search` | web | Tavily-powered web search |