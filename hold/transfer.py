import click

from .db import Session, Account


@click.command()
@click.argument("account_id", type=int)
@click.argument("amount", type=int)
def transfer(account_id, amount):
    with Session.begin() as session:
        account = session.query(Account).get(account_id)
        account.init += amount
        account.cash += amount
        assert account.cash >= 0, f"账户{account.id} 现金不能为负"
        print(f"账户{account.id} 本金{account.init} 现金{account.cash}")

        click.confirm('Are you sure?', abort=True)
