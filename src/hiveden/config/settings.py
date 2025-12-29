import os

class Config:
    app_directory = os.getenv("HIVEDEN_APP_DIRECTORY", "/hiveden-temp-root/apps")
    movies_directory = os.getenv("HIVEDEN_MOVIES_DIRECTORY", "/hiveden-temp-root/movies")
    tvshows_directory = os.getenv("HIVEDEN_TVSHOWS_DIRECTORY", "/hiveden-temp-root/tvshows")
    backup_directory = os.getenv("HIVEDEN_BACKUP_DIRECTORY", "/hiveden-temp-root/backups")
    pictures_directory = os.getenv("HIVEDEN_PICTURES_DIRECTORY", "/hiveden-temp-root/pictures")
    documents_directory = os.getenv("HIVEDEN_DOCUMENTS_DIRECTORY", "/hiveden-temp-root/documents")
    ebooks_directory = os.getenv("HIVEDEN_EBOOKS_DIRECTORY", "/hiveden-temp-root/ebooks")
    music_directory = os.getenv("HIVEDEN_MUSIC_DIRECTORY", "/hiveden-temp-root/music")
    docker_network_name = os.getenv("HIVEDEN_DOCKER_NETWORK_NAME", "hiveden-net")
    domain = os.getenv("HIVEDEN_DOMAIN", "hiveden.local")

    # Pi-hole Configuration
    pihole_enabled = os.getenv("HIVEDEN_PIHOLE_ENABLED", "false").lower() == "true"
    pihole_host = os.getenv("HIVEDEN_PIHOLE_HOST", "http://pi.hole")
    pihole_password = os.getenv("HIVEDEN_PIHOLE_PASSWORD", "")

config = Config()