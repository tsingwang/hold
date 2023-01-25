import datetime
from pathlib import Path

from sqlalchemy import (Column, Integer, Boolean, String, Date, Enum, Float,
                        ForeignKey, UniqueConstraint, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker


workdir = Path.home().joinpath(".hold")
workdir.mkdir(exist_ok=True)
db_path = Path.home().joinpath(".hold/hold.sqlite3")
if not db_path.exists():
    db_path.touch()

engine = create_engine("sqlite:///" + str(db_path), echo=False)
Session = sessionmaker(bind=engine)

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stock"

    code = Column(String(10), primary_key=True)
    name = Column(String(32))
    type = Column(Enum("CASH", "A", "B", "CB", "ETF", "ETF_HK", "ETF_US"))


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(16))
    init = Column(Integer)
    cash = Column(Integer)                      # 场内现金
    cash_outside = Column(Integer, default=0)   # 场外现金
    cash_extra = Column(Integer, default=0)     # 额外的, 不参与收益率计算
    debt = Column(Integer, default=0)           # 负债


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), ForeignKey("stock.code"))
    amount = Column(Integer)
    cost = Column(Integer)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", backref=backref("holdings"))
    stock = relationship("Stock")
    UniqueConstraint(account_id, code)


class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.date.today())
    code = Column(String(10), ForeignKey("stock.code"))
    amount = Column(Integer)
    price = Column(Float)
    note = Column(String(512))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", backref=backref("trade_hists"))
    stock = relationship("Stock")


class HoldHistory(Base):
    __tablename__ = "hold_history"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.date.today())
    code = Column(String(10), ForeignKey("stock.code"))
    accumulated_profit = Column(Integer)
    stock = relationship("Stock", backref=backref("hold_hists"))


class HoldStats(Base):
    __tablename__ = "hold_stats"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.date.today())
    code = Column(String(10), ForeignKey("stock.code"))
    amount = Column(Integer)
    cost = Column(Integer)
    value = Column(Integer)
    stock = relationship("Stock")
    UniqueConstraint(date, code)


class ProfitStats(Base):
    __tablename__ = "profit_stats"

    date = Column(Date, primary_key=True, default=datetime.date.today())
    init = Column(Integer)
    total = Column(Integer)
    cash = Column(Integer)
    a = Column(Integer)
    b = Column(Integer)
    cb = Column(Integer)
    etf = Column(Integer)
    etf_hk = Column(Integer)
    etf_us = Column(Integer)
    flag_week = Column(Boolean, default=False)
    flag_month = Column(Boolean, default=False)
    flag_quarter = Column(Boolean, default=False)
    flag_year = Column(Boolean, default=False)
    cash_extra = Column(Integer)    # 额外的, 不参与收益率计算
    debt = Column(Integer)          # 负债


Base.metadata.create_all(engine)
