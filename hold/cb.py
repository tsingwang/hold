import datetime

import click

from .db import Session, Stock, Holding, TradeHistory


@click.command()
@click.argument("account_id", type=int)
@click.argument("bond_code")
@click.argument("stock_code")
@click.argument("amount", type=int)
@click.argument("cb_price", type=float)
@click.option("-d", "--date", default=datetime.date.today())
@click.option("-n", "--note", default="转股")
def cb(date, account_id, bond_code, stock_code, amount, cb_price, note):
    assert amount > 0
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with Session.begin() as session:
        bond = session.query(Stock).filter(Stock.code==bond_code).first()
        stock = session.query(Stock).filter(Stock.code==stock_code).first()
        assert bond is not None, f"{bond_code} not existed"
        assert stock is not None, f"{stock_code} not existed"

        # 1. Update bond hold
        bond_hold = session.query(Holding).filter(Holding.account_id==account_id).\
                filter(Holding.code==bond_code).first()
        assert bond_hold is not None and bond_hold.amount >= amount, \
                f"账户{account_id} {bond.name} 数量不足"
        cost = amount * bond_hold.cost / bond_hold.amount
        bond_hold.cost -= cost
        bond_hold.amount -= amount

        # 2. Update stock hold
        stock_amount = int(100 * amount / cb_price)
        hold = session.query(Holding).filter(Holding.account_id==account_id).\
                                      filter(Holding.code==stock_code).\
                                      filter(Holding.direction=='B').first()
        if hold is None:
            hold = Holding(account_id=account_id, code=stock_code, direction='B',
                           amount=stock_amount, cost=cost)
            session.add(hold)
        else:
            hold.cost += cost
            hold.amount += stock_amount

        print(f"账户{account_id} {bond.name}{amount}张 => {stock.name}{stock_amount}股"
              f"，变动后：{hold.amount}股")

        click.confirm('Are you sure?', abort=True)

        session.add(TradeHistory(date=date, account_id=account_id, code=bond_code,
                                 price=cb_price, amount=amount, note=note))
