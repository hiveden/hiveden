import os
import shutil
import time
from urllib.parse import urlparse
import click
import psycopg2
from docker import errors
from hiveden.config.settings import config
from hiveden.bootstrap.defaults import get_default_containers
from hiveden.docker.containers import DockerManager
from hiveden.db.session import get_db_manager
from hiveden.db.repositories.locations import LocationRepository

TEMP_ROOT = "/hiveden-temp-root"

def bootstrap_infrastructure():
    """Phase 1: Bootstrap infrastructure (dirs and containers) without DB."""
    click.echo("Bootstrapping infrastructure...")
    
    # 1. Create basic directories (using defaults) so containers can mount them
    ensure_directories(use_db=False)
    
    # 2. Start Containers (Postgres, Redis, Traefik)
    ensure_containers()

def bootstrap_data():
    """Phase 2: Bootstrap data (migrations and directory moves) using DB."""
    click.echo("Bootstrapping data and migrations...")
    
    # 1. Wait for DB Server to be ready
    wait_for_db()
    
    # 2. Ensure Database Exists
    ensure_database_exists()
    
    db_manager = get_db_manager()
    db_manager.initialize_db()
    
    # 3. Directory Migration (using DB paths)
    ensure_directories(use_db=True)

def wait_for_db(retries=30, delay=2):
    """Wait for database server to be ready by connecting to 'postgres' db."""
    db_manager = get_db_manager()
    
    # Parse URL to switch to 'postgres' db
    parsed = urlparse(db_manager.db_url)
    postgres_url = parsed._replace(path="/postgres").geturl()
    
    for i in range(retries):
        try:
            conn = psycopg2.connect(postgres_url)
            conn.close()
            return
        except psycopg2.OperationalError as e:
            if i == 0:
                click.echo(f"Waiting for database server... ({e})")
            time.sleep(delay)
    raise Exception("Database server failed to start.")

def ensure_database_exists():
    """Ensure the target database exists, creating it if necessary."""
    db_manager = get_db_manager()
    parsed = urlparse(db_manager.db_url)
    target_db = parsed.path.lstrip('/')
    
    # Connect to default 'postgres' db
    postgres_url = parsed._replace(path="/postgres").geturl()
    
    conn = psycopg2.connect(postgres_url)
    conn.autocommit = True
    try:
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        if not cursor.fetchone():
            click.echo(f"Database '{target_db}' not found. Creating...")
            cursor.execute(f"CREATE DATABASE {target_db}")
            click.echo(f"Database '{target_db}' created successfully.")
        else:
            # click.echo(f"Database '{target_db}' already exists.")
            pass
    finally:
        conn.close()

def ensure_directories(use_db=True):
    """Ensure directory structure exists and migrate if necessary."""
    repo = None
    if use_db:
        try:
            db_manager = get_db_manager()
            repo = LocationRepository(db_manager)
        except Exception as e:
            click.echo(f"Warning: Could not connect to DB for directory verification: {e}")

    # Define the keys we care about for bootstrap
    location_keys = ["apps", "movies", "tvshows", "pictures", "documents", "ebooks", "music", "backup"]
    
    for key in location_keys:
        target_path = None
        
        if repo:
            try:
                location = repo.get_by_key(key)
                if location:
                    target_path = location.path
            except Exception:
                pass
        
        # Fallback to defaults if no DB or key not found
        if not target_path:
            target_path = getattr(config, f"{key if key != 'apps' else 'app'}_directory")

        temp_path = os.path.join(TEMP_ROOT, key)
        
        # Ensure target exists
        if not os.path.exists(target_path):
            try:
                os.makedirs(target_path, exist_ok=True)
                click.echo(f"Created directory: {target_path}")
            except OSError as e:
                click.echo(f"Error creating directory {target_path}: {e}")
             
        # Migration logic
        # We only migrate if we are checking against DB, as that implies a potential user change.
        # During Phase 1 (use_db=False), target is always default, so mismatch is unlikely unless ENV changed.
        abs_target = os.path.abspath(target_path)
        abs_temp = os.path.abspath(temp_path)
        
        if abs_target != abs_temp and os.path.exists(abs_temp):
             click.echo(f"Migrating {key} from {abs_temp} to {abs_target}...")
             try:
                 for item in os.listdir(abs_temp):
                     s = os.path.join(abs_temp, item)
                     d = os.path.join(abs_target, item)
                     if os.path.exists(d):
                         click.echo(f"Skipping {item}, already exists in target.")
                     else:
                         shutil.move(s, d)
                         click.echo(f"Moved {item}")
             except Exception as e:
                 click.echo(f"Error migrating {key}: {e}")

def ensure_containers():
    """Ensure default containers are running."""
    # We should also pull network name and app_directory from DB or Config?
    # For now, keeping as is, but eventually DockerManager should query DB for its config.
    manager = DockerManager(network_name=config.docker_network_name)
    defaults = get_default_containers()
    
    # Try to fetch app root from DB if possible, but don't fail if DB is down (bootstrap phase 1)
    app_root = config.app_directory
    try:
        db_manager = get_db_manager()
        # Simple check without migration logic to see if we can get a connection
        # If this fails, we are likely in Phase 1, so use defaults.
        # Actually, ensure_containers is called in Phase 1. DB is NOT ready.
        # So we MUST use config defaults here.
        # But wait, if user changed path in DB, and we restart server, we want containers to respect that.
        # So: catch exception.
        repo = LocationRepository(db_manager)
        apps_location = repo.get_by_key('apps')
        if apps_location:
            app_root = apps_location.path
    except Exception:
        pass # Database likely not ready, use default
    
    for container_def in defaults:
        try:
            try:
                manager.client.containers.get(container_def.name)
                pass
            except errors.NotFound:
                click.echo(f"Creating container '{container_def.name}'...")
                # We pass app_root here to override the default in the manager if possible,
                # or ensure the manager uses the right root.
                manager.create_container(
                    name=container_def.name,
                    image=container_def.image,
                    env=container_def.env,
                    ports=container_def.ports,
                    mounts=container_def.mounts,
                    command=container_def.command,
                    network_name=config.docker_network_name,
                    app_directory=app_root # Assuming we update DockerManager to accept this
                )
        except Exception as e:
            click.echo(f"Error bootstrapping container '{container_def.name}': {e}")
