import asyncio

import click

from .dividend import dividend
from .flag_month import flag_month
from .holding import holding
from .profit import profit
from .set_cash import set_cash
from .trade import trade
from .transfer import transfer


@click.group(invoke_without_command=True)
@click.option('--readonly', '-r', is_flag=True)
@click.pass_context
def cli(ctx, readonly):
    if ctx.invoked_subcommand is None:
        asyncio.run(holding(readonly))

cli.add_command(dividend)
cli.add_command(flag_month)
cli.add_command(profit)
cli.add_command(set_cash)
cli.add_command(trade)
cli.add_command(transfer)
