import os
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from yoyo import read_migrations, get_backend

class DatabaseManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.parsed_url = urlparse(db_url)
        self.db_type = self.parsed_url.scheme

    def get_connection(self):
        """Get a raw database connection."""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

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

