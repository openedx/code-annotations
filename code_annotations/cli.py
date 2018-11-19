"""
Command line interface for code annotation tools.
"""
import click


@click.group()
def cli():
    """
    Code annotation tools.
    """
    pass


@cli.command('seed_safelist')
def seed_safelist():
    """
    Subcommand for seeding the initial .pii_safe_list.yaml file.
    """
    pass
