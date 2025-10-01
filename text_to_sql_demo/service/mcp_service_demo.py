"""Generalised AskDatabase MCP service for the cookbook demo.

This mirrors the production service while running against a self-contained
SQLite dataset so teams can experiment without connecting to external
infrastructure.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import srsly
from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.messages.utils import convert_to_openai_messages
from langchain_community.utilities import SQLDatabase
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT
PACKAGE_ROOT = ROOT.parent
SOURCE_ROOT = PACKAGE_ROOT.parent
for path in [SOURCE_ROOT, PACKAGE_ROOT, PROJECT, ROOT]:
    sys.path.insert(0, str(path))

from text_to_sql_demo.config import load_settings
from text_to_sql_demo.helper import create_current_date
from text_to_sql_demo.helper.normalizer import enforce_ilike
from text_to_sql_demo.helper.parser import parse_sql_query
from text_to_sql_demo.library.simple_reranker import SimpleReranker

load_dotenv(ROOT / ".env")
settings = load_settings(ROOT)


class DemoSQLAgent:
    def __init__(
        self,
        client: str,
        connection_string: str,
        metadata_dir: Path,
        return_direct: bool = False,
    ) -> None:
        self.client = client
        self.metadata_dir = metadata_dir
        self.connection_string = connection_string
        self.return_direct = return_direct
        self.db: Optional[SQLDatabase] = None
        self.cot = True
        self.reranker = SimpleReranker(top_n=5)
        self.log_dir = ROOT / "log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_date = create_current_date()

    def init_sql_connection(self) -> None:
        if self.db:
            return
        logger.debug("Initialising SQLAlchemy connection to {}", self.connection_string)
        engine_args: Dict[str, Any] = {}
        if self.connection_string.startswith("sqlite"):
            
            engine_args["connect_args"] = {"check_same_thread": False}
        self.db = SQLDatabase.from_uri(self.connection_string, sample_rows_in_table_info=0, engine_args=engine_args)

    def _metadata_path(self) -> Path:
        filename = f"metadata-{self.client}.json"
        path = self.metadata_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Metadata file not found: {path}")
        return path

    def _load_metadata(self) -> List[Dict[str, Any]]:
        return srsly.read_json(self._metadata_path())

    def write_log(
        self,
        messages: List[BaseMessage],
        response: BaseMessage,
        value: str,
        _type: Literal["sql_query_generation", "table_selector"] = "sql_query_generation",
    ) -> None:
        log_data = {
            "type": _type,
            "messages": convert_to_openai_messages(messages) + convert_to_openai_messages([response]),
            "final_result": value,
            "current_date": self.current_date,
        }
        srsly.write_jsonl(self.log_dir / "demo-log.jsonl", [log_data], append=True, append_new_line=False)
        logger.success("Logged MCP interaction to %s", self.log_dir)

    def rerank_tables(self, query: str, tables: List[Dict[str, Any]]):
        docs = [
            Document(
                page_content=item.get("table_description", ""),
                metadata={"table_name": item["table_name"]},
            )
            for item in tables
        ]
        ranked = self.reranker.compress_documents(docs, query)
        ranked_names = [doc.metadata["table_name"] for doc in ranked]
        logger.debug("Ranked table order: {}", ", ".join(ranked_names))
        order = {name: index for index, name in enumerate(ranked_names)}
        return sorted(tables, key=lambda item: order.get(item["table_name"], len(order)))


def _load_table_metadata(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    return table.get("table_metadata", [])


def _format_column_line(column: Dict[str, Any]) -> str:
    column_name = column.get("column_name", "").strip()
    data_type = column.get("data_type", "TEXT")
    description = column.get("description", "").strip()
    example = column.get("example")
    line = f"    {column_name} {data_type} -- {description}"
    if example not in (None, ""):
        line += f" Example: {example}."
    return line


def _query_to_rows(result: str) -> List[Dict[str, Any]]:
    try:
        data = json.loads(result)
        if isinstance(data, dict) and "rows" in data:
            return data["rows"]
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        try:
            import ast
            data = ast.literal_eval(result)
            if isinstance(data, dict) and "rows" in data:
                return data["rows"]
            if isinstance(data, list):
                return data
        except (ValueError, SyntaxError):
            logger.warning("Failed to parse SQL result: {}", result)
    return []

# ==== Initialize MCP and tools === #
sql_agent = DemoSQLAgent(
    client=settings.client,
    connection_string=settings.connection_string,
    metadata_dir=settings.metadata_dir,
)

mcp = FastMCP(name="AskDatabaseDemo")

# ==== Define tools 1 ==== #
@mcp.tool(
    name="rank_metadata_tables",
    description=(
        "Identify and rank database tables that relate to the user question. "
        "Always call this tool before querying table schemas or executing SQL."
    ),
)
def rank_metadata_tables(query: str) -> str:
    sql_agent.init_sql_connection()
    tables = sql_agent._load_metadata()
    ranked_tables = sql_agent.rerank_tables(query, tables)
    formatted = "\n---\n".join(
        [
            (
                f"- Table Name: {item['table_name']}\n"
                f"- Table Description: {item.get('table_description', '').strip()}\n"
                f"- Example Use Case: {item.get('use_case', '').strip()}"
            )
            for item in ranked_tables
        ]
    )
    logger.info("Ranked tables:\n{}", formatted)
    return formatted

# ==== Define tools 2==== #
@mcp.tool(
    name="outline_table_schema",
    description=(
        "Return a DDL-style description of a table using metadata and live PRAGMA data. "
        "Use this after selecting a table to understand its columns before generating SQL."
    ),
)
def outline_table_schema(table_name: str) -> str:
    sql_agent.init_sql_connection()
    tables = sql_agent._load_metadata()
    table = next((item for item in tables if item["table_name"] == table_name), None)
    if not table:
        return f"Table {table_name} not found."

    columns = _load_table_metadata(table)
    if not columns and sql_agent.db:
        pragma_query = f"PRAGMA table_info({table_name});"
        result = sql_agent.db.run(pragma_query, include_columns=True)
        rows = _query_to_rows(result)
        columns = [
            {
                "column_name": row.get("name", ""),
                "data_type": row.get("type", "TEXT"),
                "description": "",
                "example": "",
            }
            for row in rows
        ]

    ddl_body = "\n".join(_format_column_line(col) for col in columns)
    ddl = f"CREATE TABLE {table_name} (\n{ddl_body}\n)"
    logger.info("DDL for {}:\n{}", table_name, ddl)
    return ddl

# ==== Define tools 3 ==== #
@mcp.tool(
    name="run_demo_sql",
    description=(
        "Execute SQL statements against the demo database. "
        "The tool parses <sql> blocks, normalises simple equality filters, and returns the JSON result."
    ),
)
def run_demo_sql(sql_query: str) -> str:
    sql_agent.init_sql_connection()
    try:
        parsed_query = parse_sql_query(sql_query)
        logger.info("Parsed SQL:\n{}", parsed_query)
        normalized_query = enforce_ilike(parsed_query)
        logger.info("Normalised SQL:\n{}", normalized_query)
        result = sql_agent.db.run(normalized_query, include_columns=True)
        logger.info("SQL execution result: {}", result)
        return result
    except Exception as e:
        logger.exception("Error executing SQL")
        return f"Error executing SQL query: {e}"


if __name__ == "__main__":
    logger.info("🚀 Running AskDatabase Demo MCP Server on port 2332")
    mcp.run(transport="sse", host="0.0.0.0", port=2332)
