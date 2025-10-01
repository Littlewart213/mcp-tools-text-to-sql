"""Parsers used by the demo service to keep parity with production code."""
from __future__ import annotations

import ast
import re
from typing import List, Optional, Tuple


def parse_xml_to_markdown(text: str) -> str:
    pattern = re.compile(r"<(\w+)>\s*(.*?)\s*</\\1>", re.DOTALL)
    markdown_output = []
    for match in pattern.finditer(text):
        tag, content = match.groups()
        markdown_output.append(f"#### {tag.upper()}\n{content.strip()}\n")
    return "\n".join(markdown_output)


def parse_think_block(response: str, section: Optional[str] = None) -> Tuple[str, str]:
    match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
    if not match:
        raise ValueError("Invalid response format, please retry...")

    think_block = match.group(1).strip()
    content = re.split(r"</think>\s*", response, maxsplit=1)[-1] if "think" in response else ""
    if section:
        content = re.sub(rf"</?{section}>", "", content)
    return think_block, content.strip()


def parse_list(response: str) -> List[str]:
    match = re.search(r"(\[[^\]]+\])", response)
    if not match:
        return []
    items = ast.literal_eval(match.group(1))
    return items


def parse_sql_query(response: str) -> str:
    pattern = re.compile(r"<sql>\s*(?:```sql\s*)?(.*?)(?:\s*```)?\s*</sql>", re.DOTALL)
    match = pattern.search(response)
    sql = match.group(1).strip() if match else response.strip()
    sql = sql.replace("\\n", "\n").replace("\\t", "\t")

    round_pattern = r"ROUND\s*\(\s*([^(),]+)\s*,\s*(\d+)\s*\)"

    def replace_round(m):
        expression = m.group(1).strip()
        precision = m.group(2).strip()
        if expression.endswith("::numeric"):
            return f"ROUND({expression}, {precision})"
        return f"ROUND({expression}::numeric, {precision})"

    return re.sub(round_pattern, replace_round, sql, flags=re.IGNORECASE)

