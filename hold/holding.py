import calendar
import datetime

import pandas as pd
from txd.services import Xueqiu

from .db import Session, Stock, Account, Holding, HoldHistory, HoldStats, ProfitStats

pd.set_option('display.precision', 2)
pd.set_option('display.float_format', lambda x: '%.2f' % x)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 1000)

today = datetime.date.today()
HKDCNY = 0.8632
prices = {}


async def fetch_prices():
    global prices
    with Session.begin() as session:
        async with Xueqiu() as xueqiu:
            code_set = {h.code for h in session.query(Holding)}
            quotes = await xueqiu.fetch_quotes(code_set)
            prices = {q["code"]: q["current"] for q in quotes}


def show_account_stats():
    columns = ["", "本金", "市值", "沪市", "深市", "现金", "场外现金"]
    index, data = [], []
    with Session.begin() as session:
        for account in session.query(Account):
            index.append(account.id)
            cash = account.cash
            sh, sz, b, other = 0, 0, 0, 0
            for hold in account.holdings:
                if hold.stock.type == "CASH":
                    cash += prices[hold.code] * hold.amount
                elif hold.stock.type == "A" and hold.code[0] == "6":
                    sh += prices[hold.code] * hold.amount
                elif hold.stock.type == "A" and hold.code[0] in ("0", "3",):
                    sz += prices[hold.code] * hold.amount
                elif hold.stock.type == "B":
                    b += prices[hold.code] * hold.amount * HKDCNY
                else:
                    other += prices[hold.code] * hold.amount

            data.append([
                account.name,
                account.init / 10000,
                (cash + sh + sz + b + other) / 10000,
                sh / 10000,
                sz / 10000,
                cash / 10000,
                account.cash_outside / 10000,
            ])

    print(pd.DataFrame(data, index, columns))


def run_hold_stats():
    holdings = {}
    with Session.begin() as session:
        for hold in session.query(Holding):
            if hold.code not in holdings:
                holdings[hold.code] = {}
                holdings[hold.code]['amount'] = hold.amount
                holdings[hold.code]['cost'] = hold.cost
            else:
                holdings[hold.code]['amount'] += hold.amount
                holdings[hold.code]['cost'] += hold.cost

        for code, hold in holdings.items():
            stat = session.query(HoldStats).filter(HoldStats.code==code).\
                filter(HoldStats.date==today).first()
            if stat is None:
                stat = HoldStats(date=today, code=code)

            stat.amount = hold['amount']
            stat.value = prices[code] * hold['amount']
            stat.cost = hold['cost']

            history = session.query(HoldHistory).filter(HoldHistory.code==code).\
                order_by(HoldHistory.id.desc()).first()
            if history:
                stat.cost -= history.accumulated_profit

            session.add(stat)

        # Clean
        for hold in session.query(Holding):
            if hold.amount != 0:
                continue

            # Account is empty with the stock, so the value is 0
            accumulated_profit = 0 - hold.cost
            history = session.query(HoldHistory).filter(HoldHistory.code==hold.code).\
                order_by(HoldHistory.id.desc()).first()
            if history:
                accumulated_profit += history.accumulated_profit

            session.add(HoldHistory(date=today, code=code,
                                    accumulated_profit=accumulated_profit))
            # when multi accounts empty the stock simultaneous, but the new
            # history added is non committed, can not query next time.
            session.flush()

            session.delete(hold)


def show_hold_stats():
    with Session.begin() as session:
        last = session.query(HoldStats).order_by(HoldStats.id.desc()).first()
        if not last:
            return

        res = [h for h in session.query(HoldStats).filter(HoldStats.date==last.date)]
        res.sort(key=lambda h: h.value, reverse=True)
        etf_list = list(filter(lambda h: "ETF" in h.stock.type, res))
        stock_list = list(filter(lambda h: h.stock.type in ("A", "B",), res))
        cb_list = list(filter(lambda h: h.stock.type == "CB", res))
        total = sum([h.value for h in res])
        for account in session.query(Account):
            total += account.cash + account.cash_outside

        df = pd.DataFrame()
        for _list in (etf_list, stock_list, cb_list,):
            # limit 20 rows
            for i in range(0, len(_list), 20):
                data = [[h.stock.name,
                         h.value / 10000,
                         100 * h.value / total] for h in _list[i:i+20]]
                tmp_df = pd.DataFrame(data, columns=["", "市值", "仓位"])
                df = pd.concat([df, tmp_df], axis=1)
        df.fillna("", inplace=True)
        df.index += 1
        print(df)


def run_profit_stats():
    init_total, cash_total = 0, 0
    A, B, CB, ETF, ETF_HK, ETF_US = 0, 0, 0, 0, 0, 0
    cash_extra, debt = 0, 0
    with Session.begin() as session:
        for account in session.query(Account):
            init_total += account.init + account.cash_outside
            cash_total += account.cash + account.cash_outside
            cash_extra += account.cash_extra
            debt += account.debt

        for hold in session.query(Holding):
            if hold.stock.type == "CASH":
                cash_total += prices[hold.code] * hold.amount
            elif hold.stock.type == "A":
                A += prices[hold.code] * hold.amount
            elif hold.stock.type == "B":
                B += prices[hold.code] * hold.amount * HKDCNY
            elif hold.stock.type == "CB":
                CB += prices[hold.code] * hold.amount
            elif hold.stock.type == "ETF":
                ETF += prices[hold.code] * hold.amount
            elif hold.stock.type == "ETF_HK":
                ETF_HK += prices[hold.code] * hold.amount
            elif hold.stock.type == "ETF_US":
                ETF_US += prices[hold.code] * hold.amount
            else:
                print("Unknow stock type: " + hold.stock.type)

        total = cash_total + A + B + CB + ETF + ETF_HK + ETF_US

        flag_week = today.weekday() == 4
        flag_month = today.day == calendar.monthrange(today.year, today.month)[1]
        flag_quarter = flag_month and today.month in (3, 6, 9, 12,)
        flag_year = flag_quarter and today.month == 12

        profit = ProfitStats(date=today, init=init_total, total=total, cash=cash_total,
                             a=A, b=B, cb=CB, etf=ETF, etf_hk=ETF_HK, etf_us=ETF_US,
                             flag_week=flag_week, flag_month=flag_month,
                             flag_quarter=flag_quarter, flag_year=flag_year,
                             cash_extra=cash_extra, debt=debt)
        session.merge(profit)


def show_profit_stats():
    with Session.begin() as session:
        profit = session.query(ProfitStats).order_by(ProfitStats.date.desc()).first()
        print("A股{:.2f}% B股{:.2f}% 转债{:.2f}% ETF {:.2f}% HK {:.2f}% 现金{:.2f}%".\
            format(100 * profit.a / profit.total,
                   100 * profit.b / profit.total,
                   100 * profit.cb / profit.total,
                   100 * profit.etf / profit.total,
                   100 * profit.etf_hk / profit.total,
                   100 * profit.cash / profit.total))
        print("A股{:.2f} B股{:.2f} 转债{:.2f} ETF {:.2f} HK {:.2f} 现金{:.2f}".\
            format(profit.a / 10000,
                   profit.b / 10000,
                   profit.cb / 10000,
                   profit.etf / 10000,
                   profit.etf_hk / 10000,
                   profit.cash / 10000))
        print("总本金{:.2f} 总资产{:.2f} 净资产{:.2f}".\
            format(profit.init / 10000,
                   profit.total / 10000,
                   (profit.total + profit.cash_extra - profit.debt) / 10000))

        increase = lambda x, y: (y.total - y.init) - (x.total - x.init)
        growth = lambda x, y: increase(x, y) / (y.init + x.total - x.init)

        last_day = session.query(ProfitStats).\
                filter(ProfitStats.date < profit.date).\
                order_by(ProfitStats.date.desc()).first()
        last_week = session.query(ProfitStats).\
                filter(ProfitStats.date < profit.date).\
                filter(ProfitStats.flag_week == True).\
                order_by(ProfitStats.date.desc()).first()
        last_month = session.query(ProfitStats).\
                filter(ProfitStats.date < profit.date).\
                filter(ProfitStats.flag_month == True).\
                order_by(ProfitStats.date.desc()).first()
        last_quarter = session.query(ProfitStats).\
                filter(ProfitStats.date < profit.date).\
                filter(ProfitStats.flag_quarter == True).\
                order_by(ProfitStats.date.desc()).first()
        last_year = session.query(ProfitStats).\
                filter(ProfitStats.date < profit.date).\
                filter(ProfitStats.flag_year == True).\
                order_by(ProfitStats.date.desc()).first()
        print()
        print("本日{:.2f}% 本周{:.2f}% 本月{:.2f}% 本季{:.2f}% 本年{:.2f}%".format(
            100 * growth(last_day, profit),
            100 * growth(last_week, profit),
            100 * growth(last_month, profit),
            100 * growth(last_quarter, profit),
            100 * growth(last_year, profit)))
        print("本日{:.2f} 本周{:.2f} 本月{:.2f} 本季{:.2f} 本年{:.2f}".format(
            increase(last_day, profit) / 10000,
            increase(last_week, profit) / 10000,
            increase(last_month, profit) / 10000,
            increase(last_quarter, profit) / 10000,
            increase(last_year, profit) / 10000))

        highest = max(session.query(ProfitStats), key=lambda p: p.total - p.init)
        drawdown = 0
        y_list = session.query(ProfitStats).\
                filter(ProfitStats.date>=datetime.date(profit.date.year, 1, 1)).all()
        for i in range(len(y_list) - 1):
            low = min(y_list[i+1:], key=lambda p: p.total - p.init)
            drawdown = min(drawdown, growth(y_list[i], low))
        print("年内最大回撤{:.2f}% 最高点回撤{:.2f}%".format(
            100 * drawdown,
            100 * growth(highest, profit)))


async def holding(readonly=True):
    await fetch_prices()

    if not readonly:
        run_hold_stats()
        run_profit_stats()

    show_account_stats()
    print()
    show_hold_stats()
    print()
    show_profit_stats()
