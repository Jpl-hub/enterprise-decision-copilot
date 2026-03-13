from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings


DB_PATH = settings.data_dir / 'app.db'

SCHEMA = {
    'companies': '''
        CREATE TABLE IF NOT EXISTS companies (
            company_code TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            exchange TEXT NOT NULL,
            industry TEXT NOT NULL,
            segment TEXT NOT NULL
        )
    ''',
    'financial_features': '''
        CREATE TABLE IF NOT EXISTS financial_features (
            company_code TEXT,
            company_name TEXT,
            report_year INTEGER,
            revenue_million REAL,
            net_profit_million REAL,
            gross_margin_pct REAL,
            net_margin_pct REAL,
            rd_ratio_pct REAL,
            debt_ratio_pct REAL,
            current_ratio REAL,
            cash_to_short_debt REAL,
            inventory_turnover REAL,
            receivable_turnover REAL,
            operating_cashflow_million REAL,
            roe_pct REAL,
            source_url TEXT,
            published_at TEXT
        )
    ''',
    'research_reports': '''
        CREATE TABLE IF NOT EXISTS research_reports (
            company_code TEXT,
            company_name TEXT,
            report_date TEXT,
            title TEXT,
            analyst_view TEXT,
            institution TEXT,
            sentiment TEXT,
            content TEXT,
            source_url TEXT
        )
    ''',
    'industry_reports': '''
        CREATE TABLE IF NOT EXISTS industry_reports (
            industry_code TEXT,
            industry_name TEXT,
            report_date TEXT,
            title TEXT,
            institution TEXT,
            sentiment TEXT,
            content TEXT,
            source_url TEXT
        )
    ''',
    'macro_indicators': '''
        CREATE TABLE IF NOT EXISTS macro_indicators (
            period TEXT,
            indicator_name TEXT,
            indicator_value REAL,
            unit TEXT,
            source_url TEXT
        )
    ''',
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        )
    ''',
    'user_sessions': '''
        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT
        )
    ''',
    'agent_threads': '''
        CREATE TABLE IF NOT EXISTS agent_threads (
            thread_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            focus_company_code TEXT,
            focus_company_name TEXT,
            last_task_mode TEXT,
            last_task_label TEXT,
            thread_summary TEXT,
            thread_memory TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''',
    'agent_messages': '''
        CREATE TABLE IF NOT EXISTS agent_messages (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''',
    'audit_logs': '''
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            user_id TEXT,
            event_type TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            detail_json TEXT,
            created_at TEXT NOT NULL
        )
    ''',
}


INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_financial_features_company_year ON financial_features(company_code, report_year)',
    'CREATE INDEX IF NOT EXISTS idx_research_reports_company_date ON research_reports(company_code, report_date)',
    'CREATE INDEX IF NOT EXISTS idx_industry_reports_name_date ON industry_reports(industry_name, report_date)',
    'CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_agent_threads_user_id ON agent_threads(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_agent_messages_thread_id_created ON agent_messages(thread_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id_created ON audit_logs(user_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type_created ON audit_logs(event_type, created_at)',
]


THREAD_COLUMN_MIGRATIONS = {
    'last_task_mode': 'TEXT',
    'last_task_label': 'TEXT',
    'thread_summary': 'TEXT',
    'thread_memory': 'TEXT',
}


def get_db_path() -> Path:
    return DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_agent_thread_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row['name']
        for row in conn.execute("PRAGMA table_info(agent_threads)").fetchall()
    }
    for column_name, column_type in THREAD_COLUMN_MIGRATIONS.items():
        if column_name not in columns:
            conn.execute(f'ALTER TABLE agent_threads ADD COLUMN {column_name} {column_type}')


def init_db(db_path: Path | None = None) -> None:
    with get_connection(db_path) as conn:
        for ddl in SCHEMA.values():
            conn.execute(ddl)
        _ensure_agent_thread_columns(conn)
        for ddl in INDEXES:
            conn.execute(ddl)
        conn.commit()


def table_has_rows(table_name: str) -> bool:
    if not DB_PATH.exists():
        return False
    with get_connection() as conn:
        try:
            row = conn.execute(f'SELECT 1 FROM {table_name} LIMIT 1').fetchone()
            return row is not None
        except sqlite3.Error:
            return False
