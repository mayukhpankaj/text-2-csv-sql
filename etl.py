import pandas as pd
from pathlib import Path
from sqlite3 import Connection


TRADES_CSV = "./csv/trades.csv"
HOLDINGS_CSV = "./csv/holdings.csv"


def run_etl(conn: Connection) -> dict:
    load_trades(conn)
    load_holdings(conn)
    return {"status": "success"}


def load_trades(conn: Connection) -> None:
    df = pd.read_csv(TRADES_CSV)

    df_out = pd.DataFrame({
        "allocation_id": df["AllocationId"],
        "trade_id": df["id"],
        "revision_id": df["RevisionId"],
        "trade_type": df["TradeTypeName"],
        "security_id": df["SecurityId"],
        "security_type": df["SecurityType"],
        "security_name": df["Name"],
        "isin": df["ISIN"],
        "trade_date": df["TradeDate"],
        "settle_date": df["SettleDate"],
        "quantity": df["Quantity"],
        "price": df["Price"],
        "principal": df["Principal"],
        "total_cash": df["TotalCash"],
        "allocation_qty": df["AllocationQTY"],
        "allocation_principal": df["AllocationPrincipal"],
        "allocation_cash": df["AllocationCash"],
        "portfolio_name": df["PortfolioName"],
        "custodian_name": df["CustodianName"],
        "strategy": df["StrategyName"],
        "strategy1": df["Strategy1Name"],
        "strategy2": df["Strategy2Name"],
        "counterparty": df["Counterparty"],
        "allocation_rule": df["AllocationRule"],
        "is_custom_allocation": df["IsCustomAllocation"],
    })

    df_out.to_sql("trade_allocation", conn, if_exists="append", index=False)



def load_holdings(conn: Connection) -> None:
    df = pd.read_csv(HOLDINGS_CSV)

    # Explicit date parsing (DD/MM/YY)
    for col in ["AsOfDate", "OpenDate", "CloseDate"]:
        df[col] = pd.to_datetime(
            df[col],
            format="%d/%m/%y",
            errors="coerce"
        )

    df_out = pd.DataFrame({
        "as_of_date": df["AsOfDate"].dt.strftime("%Y-%m-%d"),
        "open_date": df["OpenDate"].dt.strftime("%Y-%m-%d"),
        "close_date": df["CloseDate"].dt.strftime("%Y-%m-%d"),
        "portfolio_name": df["PortfolioName"],
        "custodian_name": df["CustodianName"],
        "strategy": df["StrategyRefShortName"],
        "strategy1": df["Strategy1RefShortName"],
        "strategy2": df["Strategy2RefShortName"],
        "direction": df["DirectionName"],
        "security_id": df["SecurityId"],
        "security_type": df["SecurityTypeName"],
        "security_name": df["SecName"],
        "start_qty": df["StartQty"],
        "qty": df["Qty"],
        "start_price": df["StartPrice"],
        "price": df["Price"],
        "start_fx_rate": df["StartFXRate"],
        "fx_rate": df["FXRate"],
        "mv_local": df["MV_Local"],
        "mv_base": df["MV_Base"],
        "pl_dtd": df["PL_DTD"],
        "pl_qtd": df["PL_QTD"],
        "pl_mtd": df["PL_MTD"],
        "pl_ytd": df["PL_YTD"],
    })

    df_out.to_sql("holding", conn, if_exists="append", index=False)
