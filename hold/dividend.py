import click

from .db import Session, Holding


@click.command()
@click.argument("code")
@click.argument("price", type=float)
def dividend(code, price):
    with Session.begin() as session:
        for hold in session.query(Holding).filter(Holding.code==code):
            hold.cost -= price * hold.amount
            hold.account.cash += price * hold.amount
            print(f"账户{hold.account.id} {hold.code} {hold.amount}股 每股分红 {price}")

        click.confirm('Are you sure?', abort=True)
