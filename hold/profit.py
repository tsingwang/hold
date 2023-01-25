import datetime

import click
import pandas as pd

from .db import Session, ProfitStats

pd.set_option('display.precision', 2)
pd.set_option('display.float_format', lambda x: '%.2f' % x)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 1000)


@click.command()
@click.option('--show_by_month', '-m', is_flag=True, help="Show by year default")
def profit(show_by_month):
    today = datetime.date.today()
    columns = ["总本金", "市值", "总盈亏", "当期本金", "当期盈亏", "收益率",
               "年化", "场外现金", "负债", "个人资产"]
    index = []
    data = []
    with Session.begin() as session:
        if show_by_month:
            last_year = datetime.date(today.year, 1, 1) - datetime.timedelta(days=1)
            _list = session.query(ProfitStats).\
                    filter(ProfitStats.date>=last_year).\
                    filter(ProfitStats.flag_month==True).all()
        else:
            _list = session.query(ProfitStats).\
                    filter(ProfitStats.flag_year==True).all()

        for i in range(len(_list)):
            if show_by_month and i == 0:
                continue
            p = _list[i]
            index.append(p.date)
            cur_init = p.init + _list[i-1].total - _list[i-1].init \
                    if i > 0 else p.init
            # Formula: init * (1 + avg_rate)^n = total
            avg_rate = pow(p.total / p.init, 1.0/(i+1)) - 1
            data.append([
                p.init / 10000,
                p.total / 10000,
                (p.total - p.init) / 10000,
                cur_init / 10000,
                (p.total - cur_init) / 10000,
                100 * (p.total - cur_init) / cur_init,
                100 * avg_rate,
                p.cash_extra / 10000,
                p.debt / 10000,
                (p.total + p.cash_extra - p.debt) / 10000,
            ])

    print(pd.DataFrame(data, index, columns))
