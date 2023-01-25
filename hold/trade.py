import datetime

import click

from .db import Session, Account, Holding, TradeHistory


@click.command()
@click.argument("account_id", type=int)
@click.argument("code")
@click.argument("action", type=click.Choice(['B', 'S']))
@click.argument("price", type=float)
@click.argument("amount", type=int)
@click.option("-d", "--date", default=datetime.date.today())
@click.option("-n", "--note", default="")
def trade(date, account_id, code, action, price, amount, note):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    if action == "S":
        amount *= -1
    cost = price * amount

    with Session.begin() as session:
        session.add(TradeHistory(date=date, account_id=account_id, code=code,
                                 price=price, amount=amount, note=note))

        # 1. Update Account cash
        account = session.query(Account).get(account_id)
        account.cash -= cost
        assert account.cash >= 0, f"账户{account.id} 现金不足，无法买入"

        # 2. Update Holding amount and cost
        hold = session.query(Holding).filter(Holding.account_id==account_id).\
                                      filter(Holding.code==code).first()
        if hold is None:
            hold = Holding(account_id=account_id, code=code, amount=amount,
                           cost=cost)
            session.add(hold)
        else:
            hold.cost += cost
            hold.amount += amount

        assert hold.amount >= 0, f"账户{account.id} {hold.code} 数量不能为负数"

        print(f"账户{account.id} {hold.code} {price} {amount}股 剩余{hold.amount}股")

        click.confirm('Are you sure?', abort=True)
