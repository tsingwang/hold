import asyncio

import click

from .dividend import dividend
from .holding import holding
from .profit import profit
from .trade import trade


@click.group(invoke_without_command=True)
@click.option('--readonly', '-r', is_flag=True)
@click.pass_context
def cli(ctx, readonly):
    if ctx.invoked_subcommand is None:
        asyncio.run(holding(readonly))

cli.add_command(dividend)
cli.add_command(profit)
cli.add_command(trade)
