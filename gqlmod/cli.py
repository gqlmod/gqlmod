import pathlib

import click

from .importer import scan_file


@click.group()
def cli():
    """
    gqlmod static analysis utilities.
    """
    pass


@cli.command()
@click.argument('files', nargs=-1, type=click.File())
@click.option('--search/--no-search', help="Search for .gql")
def check(files, search):
    """
    Checks the schema of .gql files.
    """
    if search:
        files = map(open, pathlib.Path().glob("**/*.gql"))
    for fobj in files:
        fname = fobj.name
        for err in scan_file(fname, fobj):
            for loc in err.locations:
                click.echo(f"{fname}:{loc.line}:{loc.column}:{err.message}")
