DROP TABLE IF EXISTS trade_allocation;
DROP TABLE IF EXISTS holding;

CREATE TABLE trade_allocation (
    allocation_id INTEGER PRIMARY KEY,
    trade_id INTEGER,
    revision_id INTEGER,
    trade_type TEXT,

    security_id INTEGER,
    security_type TEXT,
    security_name TEXT,
    isin TEXT,

    trade_date TEXT,
    settle_date TEXT,

    quantity REAL,
    price REAL,
    principal REAL,
    total_cash REAL,

    allocation_qty REAL,
    allocation_principal REAL,
    allocation_cash REAL,

    portfolio_name TEXT,
    custodian_name TEXT,

    strategy TEXT,
    strategy1 TEXT,
    strategy2 TEXT,

    counterparty TEXT,
    allocation_rule TEXT,
    is_custom_allocation INTEGER
);

CREATE TABLE holding (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT,
    open_date TEXT,
    close_date TEXT,

    portfolio_name TEXT,
    custodian_name TEXT,

    strategy TEXT,
    strategy1 TEXT,
    strategy2 TEXT,

    direction TEXT,

    security_id INTEGER,
    security_type TEXT,
    security_name TEXT,

    start_qty REAL,
    qty REAL,
    start_price REAL,
    price REAL,

    start_fx_rate REAL,
    fx_rate REAL,

    mv_local REAL,
    mv_base REAL,

    pl_dtd REAL,
    pl_qtd REAL,
    pl_mtd REAL,
    pl_ytd REAL
);
