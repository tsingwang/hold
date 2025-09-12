import datetime

import click

from .db import Session, Stock, Account, Holding, TradeHistory
from .utils import is_contract, contract_unit, contract_fee


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
        name = stock.name if stock else '合约'

        cost = price * amount
        if is_contract(code):
            cost *= contract_unit(code)
            cost += contract_fee(code) * amount

        # 1. Update Holding amount and cost
        hold = session.query(Holding).filter(Holding.account_id==account_id).\
                                      filter(Holding.code==code).\
                                      filter(Holding.direction==direction).first()
        if hold is None:
            hold = Holding(account_id=account_id, code=code, direction=direction,
                           amount=amount, cost=cost)
            session.add(hold)
        else:
            if direction == "S" and amount < 0:
                # Sell Close
                cost += (hold.cost / hold.amount - price * contract_unit(code)) * amount * 2
            hold.cost += cost
            hold.amount += amount

        assert hold.amount >= 0, f"账户{account_id} {name}({code}) 数量不足"

        # 2. Update Account cash
        account = session.query(Account).get(account_id)
        account.cash -= cost
        assert account.cash >= 0, f"账户{account.id} 现金不足，无法买入"

        print(f"账户{account.id} {direction} {name}({code}) {price} {amount}股"
              f"，变动后：{hold.amount}股 现金{account.cash}")

        click.confirm('Are you sure?', abort=True)

        session.add(TradeHistory(date=date, account_id=account_id, code=code,
                                 price=price, amount=amount, direction=direction,
                                 note=note))
