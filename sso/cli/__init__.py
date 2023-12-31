"""
This is the entry point for the command-line interface (CLI) application.

It can be used as a handy facility for running the task from a command line.

.. note::

    To learn more about Click visit the
    `project website <http://click.pocoo.org/5/>`_.  There is also a very
    helpful `tutorial video <https://www.youtube.com/watch?v=kNke39OZ2k0>`_.

    To learn more about running Luigi, visit the Luigi project's
    `Read-The-Docs <http://luigi.readthedocs.io/en/stable/>`_ page.

.. currentmodule:: sso.cli
.. moduleauthor:: Jeff Bachtel <jeff.bachtel@gmail.com>
"""
import logging

import click

import sso.getcreds

from sso.cli.wrapper import wrapper as wrapper_cmd

from ..__init__ import __version__

LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}  #: a mapping of `verbose` option counts to logging levels


class Info:
    """An information object to pass data between CLI functions."""

    def __init__(self):  # Note: This object must have an empty constructor.
        """Create a new instance."""
        self.verbose: int = 0


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(Info, ensure=True)

# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group()
@click.option("--verbose", "-v", count=True, help="Enable verbose output.")
@pass_info
def cli(info: Info, verbose: int):
    """Run sso."""
    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logging.basicConfig(level=LOGGING_LEVELS[verbose] if verbose in LOGGING_LEVELS else logging.DEBUG)
        click.echo(
            click.style(
                f"Verbose logging is enabled. " f"(LEVEL={logging.getLogger().getEffectiveLevel()})",
                fg="yellow",
            )
        )
    info.verbose = verbose

# @click.command(short_help="Populate ~/.aws/credentials file from AWS SSO")
@cli.command()
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

# Add varios subcommands
cli.add_command(wrapper_cmd)
