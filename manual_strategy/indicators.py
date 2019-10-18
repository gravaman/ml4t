import os
import datetime as dt
import pandas as pd


def load_data(symbols, dates, addSPY=True):
    """Read stock data for given symbols from CSV files."""
    df = pd.DataFrame()

    # conditionally add SPY for reference
    if addSPY and 'SPY' not in symbols:
        symbols = ['SPY'] + symbols

    # add data for each symbol provided
    for symbol in symbols:
        df_tmp = pd.read_csv(sym_to_path(symbol), index_col='Date',
                             parse_dates=True, na_values=['nan'])
        mi = pd.MultiIndex.from_product([[symbol], df_tmp.index.values],
                                        names=['Symbol', 'Date'])
        df_tmp = pd.DataFrame(df_tmp.values, index=mi, columns=df_tmp.columns)
        df = pd.concat([df, df_tmp])

    # conditionally filter SPY trading days
    if 'SPY' in symbols:
        tdays = df.loc['SPY'].index.values
        df = df.loc[(slice(None), tdays), :]

    df = df.loc[(slice(None), dates), :]

    # remove whitespace from column names
    df.columns = [c.replace(' ', '') for c in df.columns.values]
    return df


def sym_to_path(symbol, base_dir=None):
    """Return CSV file path given ticker symbol"""
    if base_dir is None:
        base_dir = os.environ.get('MARKET_DATA_DIR', '../data/')
    return os.path.join(base_dir, f'{symbol}.csv')


def pct_sma(df, window_sizes=[5, 10]):
    tmp = df.sort_index()
    groups = tmp.reset_index('Symbol').groupby('Symbol')
    df_pct_sma = pd.DataFrame(index=tmp.index)
    col_names = tmp.columns.values
    for ws in window_sizes:
        sma = tmp / groups.rolling(ws).mean()
        sma.columns = [f'{c}_pct_sma_{ws}' for c in col_names]
        df_pct_sma = df_pct_sma.join(sma)
    return df_pct_sma


def rsi(df, window_sizes=[5, 10]):
    """
        RSI = 100 - 100/1+RS
        RS1 = total_gain/total_loss
        RS2 = [((n-1)total_gain+gain_n]/[(n-1)total_loss+loss_n]
    """
    chg = df.sort_index()
    chg = (chg/chg.shift(1)-1).dropna()
    gain = chg[chg >= 0].fillna(0)
    loss = chg[chg < 0].abs().fillna(0)
    gain_grp = gain.reset_index('Symbol').groupby('Symbol')
    loss_grp = loss.reset_index('Symbol').groupby('Symbol')
    df_rsi = pd.DataFrame(index=chg.index)
    col_names = chg.columns.values
    for n in window_sizes:
        tgain = gain_grp.rolling(n).sum()
        tloss = loss_grp.rolling(n).sum()
        rs2 = ((n-1)*tgain+gain)/((n-1)*tloss+loss)
        rsi = 100-100/(1+rs2.fillna(tgain/tloss))
        rsi.columns = [f'{c}_rsi_{n}' for c in col_names]
        df_rsi = df_rsi.join(rsi)
    return df_rsi


if __name__ == '__main__':
    # todo: reverse sort direction for indicators
    universe = ['JPM', 'GS']
    start_date = dt.datetime(2008, 1, 1)
    end_date = dt.datetime(2009, 12, 31)
    dates = pd.date_range(start_date, end_date)
    data = load_data(universe, dates)
    print(data.info())