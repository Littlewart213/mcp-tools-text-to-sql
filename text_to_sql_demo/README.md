# Text-to-SQL Demo Cookbook

This cookbook reproduces the moving pieces from the production service in a
dependable, self-contained environment so new contributors can study the
workflow without hitting restricted systems. It demonstrates a text-to-SQL flow
where natural-language questions are mapped into SQL queries through three MCP
tools: ranking relevant tables, inspecting table structure, and executing SQL
while normalising filters. The layout mirrors the production folders
(`config/`, `helper/`, `library/`, `service/`, and `data/`) and ships with a small
SQLite dataset plus metadata in the same shape as the production metadata files.

## What the Demo Shows

- How an MCP service can orchestrate multi-step reasoning from a plain-language
  question to runnable SQL.
- Reranking table descriptions before peeking into schemas, mirroring the
  production decision flow but using lightweight, local components.
- Parsing and normalising SQL (e.g., enforcing case-insensitive comparisons)
  prior to execution so the final query is friendly to the embedded dataset.
- Logging each interaction to help teams review generated SQL and the context
  that produced it.

## Example Scenario

The bundled SQLite database models oil and gas wells, their operators, and basic
production history. A typical session might look like:

1. Ask, "Show the annual production trend for active wells in Sumatra." The
   `rank_metadata_tables` tool surfaces tables such as `production_history` and
   `wells` because their metadata emphasises regions and production metrics.
2. Call `outline_table_schema` on `production_history` to confirm it contains
   columns like `year`, `oil_volume`, and `region`.
3. Draft a query with `run_demo_sql`, letting the helper normalise equality
   clauses so filters like `region = 'Sumatra'` become case-insensitive and safe
   for the demo data.

The same pattern applies to other analytical questions—identifying inactive
operators, comparing production across fields, or summarising well statuses—so
teams can practise prompt design before pointing the workflow at their own
datasets.

## Folder Layout

```
cookbook/text_to_sql_demo/
├── config/              # Lightweight config loader with production-compatible env keys
├── data/                # metadata-demo.json + generated sample.db
├── helper/              # Parser, well table, and normaliser helpers
├── library/             # Simple reranker that replaces EbdeskTEIReranker
├── service/             # Generalised AskDatabase MCP service clone
├── scripts/             # Utilities to build demo assets (e.g. SQLite seeding)
└── README.md
```

## 1. Bootstrap the Demo Dataset

The demo ships with a reproducible SQLite database. Regenerate it anytime:

```bash
cd cookbook/text_to_sql_demo
python scripts/create_sample_db.py
```

This creates `data/sample.db` with sample wells, operators, and production
history plus keeps the metadata file in sync.

## 2. Configure Environment Variables

Copy the example file and adjust if needed:

```bash
cp cookbook/text_to_sql_demo/.env.example cookbook/text_to_sql_demo/.env
```

`CLIENT` and `CONNECTION_STRING` are the main variables consumed by the demo
service. They default to the local metadata (`metadata-demo.json`) and SQLite
database. Legacy keys (`LEGACY_CLIENT`, `CONNECTION_STRING_LEGACY`) remain
supported in case you need parity with the original naming.

## 3. Explore the Service from Python

The module exports the core tool functions (`rank_metadata_tables`,
`outline_table_schema`, `run_demo_sql`) so you can demonstrate the
flow without standing up the MCP server:

```python
from cookbook.text_to_sql_demo.service import mcp_service_demo as demo

# Inspect ranked tables
print(demo.rank_metadata_tables("production trend wells in Sumatra"))

# Introspect schema
print(demo.outline_table_schema("wells"))

# Run SQL directly
print(demo.run_demo_sql("<sql>SELECT well_name, status FROM wells;</sql>"))

```

## 4. (Optional) Run the FastMCP Server

If you want the exact server behaviour:

```bash
pip install fastmcp  # only required for the SSE transport
python -m cookbook.text_to_sql_demo.service.mcp_service_demo
```

The server listens on `0.0.0.0:2332` and exposes the same tool set as the
production variant.

## 5. Presenting the Architecture

Key parallels to highlight during a presentation:

- `DemoSQLAgent` matches the responsibilities of `SQLAgent` (connection
  management, reranking, logging, and metadata loading) but points at the local
  dataset.
- Metadata (`metadata-demo.json`) follows the `metadata-{client}.json` naming
  convention, so extending to new demo clients is a drop-in experience.
- The reranker swaps `EbdeskTEIReranker` with a simple string-similarity model
  to avoid external APIs while keeping the ranking hook.
With this replica, teams can rehearse prompt flows, tool-calling order, and SQL
normalisation strategies before moving over to the real production infrastructure.
