# Cookbook Playground

The `cookbook/` directory houses self-contained environments that mirror the
production text-to-SQL stack. Each subfolder keeps the same module layout and
dependencies as `service/mcp_service_phe.py`, but swaps in lightweight assets so
you can prototype or present features without accessing live infrastructure.

Available recipes:

- `text_to_sql_demo/` – a full AskDatabase replica backed by SQLite metadata and
  a simple reranker. Use this for workshops or walkthroughs of the PHE service.

Refer to the README inside each recipe for setup steps and usage patterns.
