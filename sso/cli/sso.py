"""sso.cli.sso - module defining `sso sso` subcommand."""
import click
import sso.getcreds

@click.command(name="getcreds", short_help="Populate ~/.aws/credentials file from AWS SSO")
@click.option(
    "--dev/--no-dev", default=True, required=False, help="Pull credentials from Dev organization", show_default=True
)
@click.option(
    "--prod/--no-prod", default=False, required=False, help="Pull credentials from Prod organization", show_default=True
)
def getcreds(dev: bool, prod: bool):
    """
    sso getcreds command.
    """
    environments = []
    if dev:
        environments.append("dev")
    if prod:
        environments.append("prod")
    sso.getcreds.getcreds(environments)
