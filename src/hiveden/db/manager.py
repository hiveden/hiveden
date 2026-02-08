import os
import subprocess
from urllib.parse import urlparse

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor
from yoyo import get_backend, read_migrations


class DatabaseManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.parsed_url = urlparse(db_url)
        self.db_type = self.parsed_url.scheme

    def get_connection(self):
        """Get a raw database connection."""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def _get_admin_connection(self):
        """
        Get a connection to the 'postgres' system database.
        Required for operations like CREATE DATABASE that can't run in a transaction block.
        """
        # Replace the path (database name) with 'postgres'
        postgres_url = self.parsed_url._replace(path="/postgres").geturl()
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    def run_migrations(self):
        """Run database migrations."""
        backend = get_backend(self.db_url)
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        migrations = read_migrations(migrations_dir)
        print(f"Running migrations for {self.db_type}, Migrations Directory: {migrations_dir}, Migrations: {migrations}")
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    def initialize_db(self):
        """Initialize the database by running migrations."""
        self.run_migrations()

    def create_database(self, db_name: str, owner: str = None):
        """Create a new database."""
        conn = self._get_admin_connection()
        try:
            cursor = conn.cursor()
            
            # Sanitize inputs strictly or use sql.Identifier (best practice)
            # Since we are using psycopg2, we should use its composable sql building
            from psycopg2 import sql
            
            query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            
            if owner:
                query = query + sql.SQL(" OWNER {}").format(sql.Identifier(owner))
                
            cursor.execute(query)
        finally:
            conn.close()

    def delete_database(self, db_name: str):
        """Delete a database, terminating connections first."""
        if db_name in ['postgres', 'hiveden']:
            raise ValueError(f"Cannot delete system database '{db_name}'.")

        conn = self._get_admin_connection()
        try:
            cursor = conn.cursor()
            from psycopg2 import sql

            # Terminate connections
            # PostgreSQL < 13 uses pg_terminate_backend(pid)
            # We query pg_stat_activity to find pids connected to the target DB
            terminate_query = sql.SQL("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = {}
                AND pid <> pg_backend_pid()
            """).format(sql.Literal(db_name))
            
            cursor.execute(terminate_query)
            
            # Drop Database
            drop_query = sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name))
            cursor.execute(drop_query)
        finally:
            conn.close()

    def list_databases(self):
        """List all databases."""
        conn = self._get_admin_connection()
        try:
            cursor = conn.cursor()
            # datname: db name
            # pg_get_userbyid(datdba): owner name
            # pg_encoding_to_char(encoding): encoding
            query = """
                SELECT
                    datname as name,
                    pg_get_userbyid(datdba) as owner,
                    pg_encoding_to_char(encoding) as encoding,
                    pg_database_size(datname) as size_bytes
                FROM pg_database
                WHERE datistemplate = false
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            conn.close()

    def list_users(self):
        """List all database users."""
        conn = self._get_admin_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    rolname as name,
                    rolsuper as is_superuser,
                    rolcreaterole as can_create_role,
                    rolcreatedb as can_create_db
                FROM pg_roles
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            conn.close()

    def backup_database(self, db_name: str, output_path: str):
        """Backup a database to a file."""
        # Construct connection string for the specific target DB
        target_url = self.parsed_url._replace(path=f"/{db_name}").geturl()
        
        try:
            subprocess.run(
                ["pg_dump", "--dbname", target_url, "-f", output_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Database backup failed: {e.stderr}") from e

    def restore_database(self, db_name: str, input_path: str):
        """Restore a database from a file."""
        if not os.path.exists(input_path):
             raise FileNotFoundError(f"Backup file not found: {input_path}")
             
        # Construct connection string for the specific target DB
        target_url = self.parsed_url._replace(path=f"/{db_name}").geturl()
        
        try:
            subprocess.run(
                ["psql", "--dbname", target_url, "-f", input_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Database restore failed: {e.stderr}") from e