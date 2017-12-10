import logging
import os
import sqlite3
import sys
from sqlite3 import Error
import pandas as pd
import re

from dotenv import find_dotenv, load_dotenv

class DB_Helper:
    def __init__(self, db_path):
        self._conn = self._create_connection(db_path)

        company_create = """CREATE TABLE IF NOT EXISTS "company" (
        "symbol" TEXT NOT NULL PRIMARY KEY,
        "c_name" TEXT NOT NULL,
        "exchange" TEXT NOT NULL,
        "market_cap" integer NOT NULL,
        "industry" TEXT,
        "sector" TEXT
        );
        """
        data_series_create = """CREATE TABLE IF NOT EXISTS "data_series" (
            "frequency" TEXT,
            "frequency_short" TEXT,
            "id" varchar(20) NOT NULL PRIMARY KEY,
            "last_updated" datetime,
            "notes" TEXT,
            "observation_end" date,
            "observation_start" date,
            "popularity" integer,
            "realtime_start" date,
            "realtime_end" date,
            "seasonal_adjustment" TEXT,
            "seasonal_adjustment_short" TEXT,
            "title" TEXT,
            "units" TEXT,
            "units_short" TEXT
            );
            """
        data_create = """CREATE TABLE IF NOT EXISTS "data" ( 
            "date" date NOT NULL,
            "value" decimal NOT NULL, 
            "ds_id" TEXT NOT NULL REFERENCES "data_series"("series_id"),
            PRIMARY KEY ("date", "ds_id")
            );
            """
        self.create_table(company_create)
        self.create_table(data_series_create)
        self.create_table(data_create)

    def _create_connection(self, db_path):
        try: 
            return sqlite3.connect(db_path)
        except Error as e:
            print(e)
        return None

    def create_table(self, table_sql):
        try:
            self._conn.execute(table_sql)
            self._conn.commit()
        except Error as e:
            print(e)

    def add_company(self, name, symbol, exchange, m_cap, industry=None, sector=None):
        sql = 'INSERT INTO company(c_name, symbol, exchange, market_cap, industry, sector) values (?,?,?,?,?,?)'
        try:
            self._conn.execute(sql, (name, symbol, exchange, m_cap, industry, sector))
            self._conn.commit()

        except Error as e:
            logging.error('Could not add company %s', name)

    def add_companies_from_csv(self, f_path, exchange):
        """
        Bulk adding companies with data downloaded from the NASDAQ website. URL is 
        http://www.nasdaq.com/screening/companies-by-industry.aspx, then select an exchange.
        We expect to have the following headers:
        'Symbol', 'Name', 'LastSale', 'MarketCap', 'ADR TSO', 'IPOyear', 'Sector', 'Industry', 'Summary Quote'

            :param f_path: the full path to the data file.
            :param exchange: A string representing the exchange
        """
        df = pd.read_csv(f_path)
        df = df.dropna(axis='columns', how='all')
        if exchange == 'NYSE':
            mcap_replacer = {  # converting between '$4.32B' and '432000000000' so it can be classed as a int
                '$': '',
                '.': '',
                'T': '000000000000',
                'B': '000000000',
                'M': '000000'
            }
            # re trickery from https://stackoverflow.com/a/6117124
            rep = dict((re.escape(k), v) for k, v in mcap_replacer.items())
            pattern = re.compile('|'.join(rep.keys()))
            df['MarketCap'] = df['MarketCap'].str.replace(pattern, lambda m:rep[re.escape(m.group(0))])

        if exchange == 'NASDAQ':
            df = df.drop(columns=['ADR TSO'])
        df['exchange'] = exchange

        df = df.rename(columns={'Symbol': 'symbol', 'Name': 'c_name', 'MarketCap': 'market_cap', 'Industry': 'industry', 'Sector': 'sector'})\
        .drop(columns=['LastSale', 'IPOyear', 'Summary Quote'])\
        .fillna(value=0)

        df.to_sql('company', self._conn, if_exists='append', index=False)

 
    def get_data_series(self, s_id):
        """
        Gets the requested series from the data_series table, and parses it into a dictionary, where
        the keys are the column names. If the id doesn't exist, it retuns None. 

            :param s_id: The series ID you want to look up. Can be a FRED series or Yahoo ticker.
            :return: A dictionary containing the series information, None if the series cannot be found
        """
        sql = 'SELECT * FROM data_series WHERE id=?'
        query = self._conn.execute(sql, [s_id])
        fields = [i[0] for i in query.description]
        value = query.fetchone()
        if value is not None:  # The series exists
            return dict(zip(fields, value))
        return None

    def add_data_series_fred(self, ds):
        try:
            df = ds.to_frame().T
            df.to_sql('data_series', self._conn, if_exists='append', index=False)
        except Error as e:
            logging.error(e)

    def add_data_fred(self, ds, id):
        """
        Adding the series data from FRED to the data table. This function
        is seperate from the add_data_series_fred function because the 
        FRED API distinguishes between metadata and the series, so we do too.
            :param df: The data series to add to the DB, as it comes from
                       fred.get_series()
            :param id: The Fred Series ID associated with the data series 
        """
        df = ds.to_frame(name='value')\
        .rename(columns={'index':'date'})\
        .dropna()
        df['ds_id'] = id
        df.to_sql('data', self._conn, if_exists='append', index=True, index_label='date')

    def add_data_series_and_data_yahoo(self, df, ticker):
        """
        Adds a data series entry to the DB and the data for the given pandas dataframe. We expect the df to
        have come from the pandas_datareader module like 'pdr.data.DataReader(ticker, 'yahoo')'
            :param df: a Pandas Dataframe
            :param ticker: The ticker used to download the data
        """
        try:  # try to add to the data_series table
            # Getting the company name if we have it. If not, we add
            # none to the field, which would have been inferred if
            # not provided.
            c_query = self._conn.execute(
                'SELECT c_name FROM company WHERE symbol=?', [ticker])
            c_name = c_query.fetchone()
            c_name = c_name[0] if c_name is not None else None

            self._conn.execute("""INSERT INTO data_series (
                frequency_short,
                id,
                title,
                last_updated,
                observation_start,
                observation_end
                ) VALUES (?, ?, ?, ?, ?, ?)""", 
                (df.index.freq, 
                str(ticker), 
                str(c_name),
                df.index[-1].to_pydatetime(),
                df.index[0].to_pydatetime(),
                df.index[-1].to_pydatetime()))
        except Error as e:
            # TODO: specify error - RemoteDataError, ???
            # This could trigger if we already have the series info in the table
            logging.error(e)

        try:  # try to add to the data table
            df['ds_id'] = ticker
            df = df.rename(columns={'Close': 'value'})\
            .dropna()\
            .drop(columns=['Open', 'High', 'Low', 'Adj Close', 'Volume'])
            df.to_sql('data', self._conn, if_exists='append', index=True, index_label='date')
        except Error as e:
            # TODO: specify error
            logging.error(e)

    def have_data_for_series(self, s_id):
        """
        Checks to see if we have already downloaded data for a specific series

            :param id: The ID for the FRED data series or Yahoo ticker
            :return: True if we have data, false if not. 
        """
        sql = 'SELECT value FROM data where ds_id=? LIMIT 1'
        query = self._conn.execute(sql, [s_id])
        if query.fetchone() is not None:
            return True
        return False

def main():
    db_path = os.environ.get('DB_PATH')
    db = DB_Helper(db_path)

    
if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
