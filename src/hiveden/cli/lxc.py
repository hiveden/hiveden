import click

@click.group()
@click.pass_context
def lxc(ctx):
    """LXC container management commands"""
    from hiveden.lxc.containers import check_lxc_support
    try:
        check_lxc_support()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        ctx.abort()

@lxc.command(name='list')
def list_lxc_containers():
    """List all LXC containers."""
    from hiveden.lxc.containers import list_containers
    containers = list_containers()
    for c in containers:
        click.echo(f"{c.name} - {c.state}")

@lxc.command()
@click.argument('name')
@click.option('--template', default='ubuntu', help='The template to use.')
def create_lxc_container(name, template):
    """Create a new LXC container."""
    from hiveden.lxc.containers import create_container
    try:
        create_container(name, template)
        click.echo(f"Container '{name}' created.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@lxc.command()
@click.argument('name')
def start_lxc_container(name):
    """Start an LXC container."""
    from hiveden.lxc.containers import start_container
    try:
        start_container(name)
        click.echo(f"Container '{name}' started.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@lxc.command()
@click.argument('name')
def stop_lxc_container(name):
    """Stop an LXC container."""
    from hiveden.lxc.containers import stop_container
    try:
        stop_container(name)
        click.echo(f"Container '{name}' stopped.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@lxc.command()
@click.argument('name')
def delete_lxc_container(name):
    """Delete an LXC container."""
    from hiveden.lxc.containers import delete_container
    try:
        delete_container(name)
        click.echo(f"Container '{name}' deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@lxc.group()
def scripts():
    """Manage community scripts."""
    pass

@scripts.command(name="list")
def list_scripts():
    """List available community scripts."""
    try:
        from hiveden.lxc.scripts import get_community_scripts
        scripts = get_community_scripts()
        
        if not scripts:
            click.echo("No scripts found.")
            return

        click.echo(f"Found {len(scripts)} scripts:")
        click.echo(f"{'SLUG':<25} {'TYPE':<10} {'NAME':<30} {'DESCRIPTION'}")
        click.echo("-" * 100)
        
        for script in scripts:
            # Truncate description if too long
            desc = script.description.replace('\n', ' ')
            if len(desc) > 50:
                desc = desc[:47] + "..."
            
            click.echo(f"{script.slug:<25} {script.type:<10} {script.name:<30} {desc}")
            
    except Exception as e:
        click.echo(f"Error fetching scripts: {e}", err=True)

@scripts.command(name="install")
@click.argument("container_name")
@click.argument("script_slug")
def install(container_name, script_slug):
    """
    Install a community script into a container.
    
    CONTAINER_NAME: Name of the target LXC container.
    SCRIPT_SLUG: Slug of the script to install (e.g. 'adguard', 'docker').
    """
    try:
        from hiveden.lxc.scripts import install_script
        install_script(container_name, script_slug)
    except Exception as e:
        click.echo(f"Error installing script: {e}", err=True)
        sys.exit(1)
