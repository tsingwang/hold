import datetime

import click

from .db import Session, ProfitStats


@click.command()
@click.option("--date", "-d", default=datetime.date.today())
def flag_month(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with Session.begin() as session:
        p = session.query(ProfitStats).filter(ProfitStats.date == date).first()
        if p is None:
            print(f"No record found on {date}")
            return
        p.flag_month = True
        p.flag_quarter = date.month in (3, 6, 9, 12,)
        p.flag_year = date.month == 12
        print("{} flag_month={}, flag_quarter={}, flag_year={}".format(
            p.date, p.flag_month, p.flag_quarter, p.flag_year))
        click.confirm('Are you sure?', abort=True)
