"""Server-side PostgreSQL connectivity for synthetic-data development only."""
import streamlit as st
import psycopg


def connect():
    """Never print, log, or expose the connection URL."""
    url = st.secrets.get('MPA_DATABASE_URL')
    if not url:
        raise RuntimeError('Δεν έχει οριστεί MPA_DATABASE_URL στα Streamlit Secrets.')
    return psycopg.connect(url, connect_timeout=10, sslmode='require')


def check_schema():
    """Read-only smoke test. Does not migrate or modify any data."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY table_name", ('mpa',))
            return [row[0] for row in cur.fetchall()]
