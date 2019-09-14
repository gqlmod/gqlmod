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
def check(files):
    """
    Checks the schema of .gql files.
    """
    for fobj in files:
        fname = fobj.name
        for err in scan_file(fname, fobj):
            for loc in err.locations:
                click.echo(f"{fname}:{loc.line}:{loc.column}:{err.message}")
