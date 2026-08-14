import click

from .db import Session, Account


@click.command()
@click.argument("account_id", type=int)
@click.argument("cash", type=int)
def set_cash(account_id, cash):
    with Session.begin() as session:
        account = session.query(Account).get(account_id)
        diff = cash - account.cash
        account.cash = cash
        assert account.cash >= 0, f"账户{account.id} 现金不能为负"
        print(f"账户{account.id} 本金{account.init} 现金{account.cash} 变动{diff}")

        click.confirm('Are you sure?', abort=True)


@click.command()
@click.argument("account_id", type=int)
@click.argument("cash_outside", type=int)
def set_cash_outside(account_id, cash_outside):
    with Session.begin() as session:
        account = session.query(Account).get(account_id)
        diff = cash_outside - account.cash_outside
        account.cash_outside = cash_outside
        print(f"账户{account.id} 场外现金{account.cash_outside} 变动{diff}")

        click.confirm('Are you sure?', abort=True)


@click.command()
@click.argument("account_id", type=int)
@click.argument("debt", type=int)
def set_debt(account_id, debt):
    with Session.begin() as session:
        account = session.query(Account).get(account_id)
        diff = debt - account.debt
        account.debt = debt
        print(f"账户{account.id} 负债{account.debt} 变动{diff}")

        click.confirm('Are you sure?', abort=True)
