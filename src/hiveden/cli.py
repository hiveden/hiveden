import click
import yaml


@click.group()
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.pass_context
def main(ctx, config):
    """Hiveden CLI"""
    ctx.ensure_object(dict)
    with open(config, "r") as f:
        ctx.obj["config"] = yaml.safe_load(f)


@main.group()
@click.pass_context
def docker(ctx):
    """Docker commands"""
    pass


@docker.command(name="list-containers")
@click.pass_context
def list_containers(ctx):
    """List all docker containers."""
    from hiveden.docker.containers import list_containers

    containers = list_containers(all=True)
    for container in containers:
        click.echo(f"{container.name} - {container.image.id} - {container.status}")


@docker.command()
@click.pass_context
def hello(ctx):
    """Prints the docker config."""
    click.echo(ctx.obj["config"]["docker"])


if __name__ == "__main__":
    main()
