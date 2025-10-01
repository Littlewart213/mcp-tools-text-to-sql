"""Create the SQLite dataset used throughout the text_to_sql demo.

Run this script once to create `data/sample.db` populated with a handful of
wells, operators, and production records.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "sample.db"

WELLS = [
    ("Andalas-1", "Aceh, Indonesia", "Nusantara Energy", "Sumatra Basin", "Producing", "2017-05-12", 8400),
    ("Merah Putih-2", "East Kalimantan, Indonesia", "Garuda Oil", "Kutei Basin", "Drilling", "2021-09-30", 10250),
    ("Cendrawasih-Deep", "West Papua, Indonesia", "Papua Exploration", "Bintuni Basin", "Appraisal", "2019-03-20", 12100),
    ("Rajawali-Alpha", "Java Sea, Indonesia", "Samudra Offshore", "North West Java Basin", "Shut-in", "2015-11-02", 9750),
]

PRODUCTION = [
    ("Andalas-1", 2021, 1_250_000, 780_000),
    ("Andalas-1", 2022, 1_180_000, 730_000),
    ("Merah Putih-2", 2022, 540_000, 260_000),
    ("Cendrawasih-Deep", 2020, 780_000, 410_000),
]

OPERATORS = [
    ("Nusantara Energy", "Indonesia", 1998, "Upstream and midstream operations"),
    ("Garuda Oil", "Indonesia", 2005, "Offshore development projects"),
    ("Papua Exploration", "Indonesia", 2012, "Frontier exploration"),
    ("Samudra Offshore", "Singapore", 2001, "Offshore drilling services"),
]


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS production;
            DROP TABLE IF EXISTS wells;
            DROP TABLE IF EXISTS operators;

            CREATE TABLE wells (
                well_name TEXT PRIMARY KEY,
                location TEXT NOT NULL,
                operator TEXT NOT NULL,
                basin TEXT NOT NULL,
                status TEXT NOT NULL,
                spud_date DATE NOT NULL,
                total_depth_ft INTEGER NOT NULL
            );

            CREATE TABLE production (
                well_name TEXT NOT NULL,
                year INTEGER NOT NULL,
                oil_bbl INTEGER,
                gas_mcf INTEGER,
                FOREIGN KEY (well_name) REFERENCES wells (well_name)
            );

            CREATE TABLE operators (
                operator TEXT PRIMARY KEY,
                headquarters TEXT NOT NULL,
                founded_year INTEGER,
                capabilities TEXT
            );
            """
        )
        cur.executemany(
            "INSERT INTO wells VALUES (?, ?, ?, ?, ?, ?, ?);",
            WELLS,
        )
        cur.executemany(
            "INSERT INTO production VALUES (?, ?, ?, ?);",
            PRODUCTION,
        )
        cur.executemany(
            "INSERT INTO operators VALUES (?, ?, ?, ?);",
            OPERATORS,
        )
        conn.commit()

    print(f"SQLite demo database created at {DB_PATH}")


if __name__ == "__main__":
    main()

