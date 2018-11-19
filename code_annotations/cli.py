"""
Command line interface for code annotation tools.
"""
import click

@click.group()
def cli():
    pass

@cli.command('seed_safelist')
def seed_safelist():
    """
    Subcommand to seed the initial .pii_safe_list.yaml file.
    """
    pass
