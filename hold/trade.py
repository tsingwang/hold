import datetime

import click

from .db import Session, Stock, Account, Holding, TradeHistory
from .utils import get_future_info


@click.command()
@click.argument("account_id", type=int)
@click.argument("code")
@click.argument("price", type=float)
@click.argument("amount", type=int)
@click.option("--direction", type=click.Choice(['B', 'S']), default='B')
@click.option("-d", "--date", default=datetime.date.today())
@click.option("-n", "--note", default="")
def trade(date, account_id, code, price, amount, direction, note):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with Session.begin() as session:
        stock = session.query(Stock).filter(Stock.code==code).first()
        assert stock is not None, f"{code} not existed"

        session.add(TradeHistory(date=date, account_id=account_id, code=code,
                                 price=price, amount=amount, direction=direction,
                                 note=note))

        cost = price * amount
        future = get_future_info(code)
        if future:
            cost *= future["unit"]

        # 1. Update Holding amount and cost
        hold = session.query(Holding).filter(Holding.account_id==account_id).\
                                      filter(Holding.code==code).\
                                      filter(Holding.direction==direction).first()
        if hold is None:
            hold = Holding(account_id=account_id, code=code, direction=direction,
                           amount=amount, cost=cost)
            session.add(hold)
        else:
            if future and direction == "S" and amount < 0:
                # Sell Close
                cost += (hold.cost / hold.amount - price*future['unit']) * amount * 2
            hold.cost += cost
            hold.amount += amount

        assert hold.amount >= 0, f"账户{account_id} {code} 数量不能为负数"

        # 2. Update Account cash
        account = session.query(Account).get(account_id)
        account.cash -= cost
        if not future:
            assert account.cash >= 0, f"账户{account.id} 现金不足，无法买入"

        print(f"账户{account.id} {direction} {stock.name}({code}) "
              f"{price} {amount}股 剩余{hold.amount}股 余额{account.cash}")

        click.confirm('Are you sure?', abort=True)
