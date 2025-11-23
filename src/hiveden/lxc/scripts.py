import urllib.request
import json
from typing import List, Dict
from hiveden.lxc.models import Script, Category, InstallMethod, Resources, DefaultCredentials, Note

API_URL = "https://community-scripts.github.io/ProxmoxVE/api/categories"
RAW_BASE_URL = "https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main"

def get_community_scripts() -> List[Script]:
    """
    Retrieve the list of available scripts from the Proxmox VE Helper-Scripts API.
    Returns a list of Script objects, deduplicated by slug.
    """
    req = urllib.request.Request(API_URL)
    req.add_header('User-Agent', 'hiveden-cli')
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise Exception(f"Failed to fetch scripts from API: {e}")

    scripts_by_slug: Dict[str, Script] = {}

    for cat_data in data:
        # We don't strictly need to parse Category if we just want scripts, 
        # but let's do it properly to validate structure if needed.
        # However, for simplicity and robustness, we can just iterate over scripts in each category.
        
        for script_data in cat_data.get('scripts', []):
            # Parse nested objects
            install_methods = []
            for im in script_data.get('install_methods', []):
                res_data = im.get('resources', {})
                resources = Resources(
                    cpu=res_data.get('cpu'),
                    ram=res_data.get('ram'),
                    hdd=res_data.get('hdd'),
                    os=res_data.get('os'),
                    version=res_data.get('version')
                )
                install_methods.append(InstallMethod(
                    type=im['type'],
                    script=im['script'],
                    resources=resources
                ))
            
            creds_data = script_data.get('default_credentials', {})
            default_credentials = DefaultCredentials(
                username=creds_data.get('username'),
                password=creds_data.get('password')
            )
            
            notes = [Note(text=n['text'], type=n['type']) for n in script_data.get('notes', [])]

            script = Script(
                name=script_data['name'],
                slug=script_data['slug'],
                categories=script_data.get('categories', []),
                date_created=script_data.get('date_created', ''),
                type=script_data.get('type', ''),
                updateable=script_data.get('updateable', False),
                privileged=script_data.get('privileged', False),
                interface_port=script_data.get('interface_port'),
                documentation=script_data.get('documentation'),
                website=script_data.get('website'),
                logo=script_data.get('logo'),
                config_path=script_data.get('config_path', ''),
                description=script_data.get('description', ''),
                install_methods=install_methods,
                default_credentials=default_credentials,
                notes=notes
            )
            
            # Deduplicate by slug
            if script.slug not in scripts_by_slug:
                scripts_by_slug[script.slug] = script
    
    return sorted(list(scripts_by_slug.values()), key=lambda x: x.slug)

def install_script(container_name: str, script_slug: str):
    """
    Install a community script into an LXC container.
    """
    import lxc
    from hiveden.lxc.containers import get_container

    scripts = get_community_scripts()
    script = next((s for s in scripts if s.slug == script_slug), None)
    
    if not script:
        raise Exception(f"Script '{script_slug}' not found in community repository.")
    
    script_path = script.default_install_script
    if not script_path:
        raise Exception(f"No default install method found for script '{script_slug}'.")

    script_url = f"{RAW_BASE_URL}/{script_path}"
    container = get_container(container_name)
    
    print(f"Installing {script.name} ({script_slug}) into {container_name}...")
    print(f"Source: {script_url}")
    if script.description:
        print(f"Description: {script.description}")

    # Command to download and execute the script
    cmd = ["bash", "-c", f"wget -qLO - {script_url} | bash"]
    
    if not container.running:
        raise Exception(f"Container {container_name} is not running.")

    result = container.attach_wait(lxc.attach_run_command, cmd)
    
    if result != 0:
        raise Exception(f"Script execution failed with exit code {result}")
    
    print(f"Script {script.name} installed successfully.")
    
    if script.notes:
        print("\nNotes:")
        for note in script.notes:
            print(f"[{note.type.upper()}] {note.text}")
            
    if script.default_credentials.username or script.default_credentials.password:
        print("\nDefault Credentials:")
        if script.default_credentials.username:
            print(f"Username: {script.default_credentials.username}")
        if script.default_credentials.password:
            print(f"Password: {script.default_credentials.password}")
