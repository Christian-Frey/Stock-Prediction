import logging
import os
import sqlite3
import sys
from sqlite3 import Error
import pandas as pd

from dotenv import find_dotenv, load_dotenv

class DB_Helper:
    def __init__(self, db_path):
        self._conn = self._create_connection(db_path)

    def _create_connection(self, db_path):
        try: 
            return sqlite3.connect(db_path)
        except Error as e:
            print(e)
        return None

    def create_table(self, table_sql):
        try:
            self._conn.execute(table_sql)
        except Error as e:
            print(e)

    def add_company(self, name, symbol, exchange, m_cap, industry=None, sector=None):
        sql = 'INSERT INTO company(c_name, symbol, exchange, market_cap, industry, sector) values (?,?,?,?,?,?)'
        try:
            self._conn.execute(sql, (name, symbol, exchange, m_cap, industry, sector))
        except Error as e:
            logging.error('Could not add company %s', name)

    def get_companys(self, sql):
        """
        Processes the SQL provided and returns the result in a pandas dataframe

        :param sql: The SQLite query to run
        :return: a pandas Dataframe with the requested information
        """
        return pd.read_sql_query(sql, self._conn)

    def add_data_series(self, name, id, source, frequency, oldest_date, company_ticker=None):
        sql = 'INSERT INTO data_series(s_name, s_id, source, frequency, oldest_date, company_ticker) values (?,?,?,?,?,?)'
        try:
            self._conn.execute(sql, (name, id, source, frequency, oldest_date, company_ticker))
        except Error as e:
            logging.error('Could not add data series %s', name)

    def add_data_single(self, id, date, value, ds_id):
        sql = 'INSERT INTO data(id, date, value, ds_id) values (?, ?, ?, ?)'
        try:
            self._conn.execute(sql, (id, date, value, ds_id))
        except Error as e:
            logging.error(e)

    def add_data_multiple(self, df):
        pass

def main():
    db_path = os.environ.get('DB_PATH')
    db = DB_Helper(db_path)

    company_create = """CREATE TABLE IF NOT EXISTS "company" (
        "symbol" varchar(5) NOT NULL PRIMARY KEY,
        "c_name" varchar(1000) NOT NULL,
        "exchange" varchar(6) NOT NULL,
        "market_cap" integer NOT NULL,
        "industry" varchar(300),
        "sector" varchar(100)
        );
        """

    data_series_create = """CREATE TABLE IF NOT EXISTS "data_series" (
        "s_id" varchar(50) NOT NULL PRIMARY KEY,
        "s_name" varchar(200) NOT NULL,
        "source" varchar(20) NOT NULL,
        "frequency" varchar(2) NOT NULL,
        "oldest_date" date NOT NULL,
        "company_ticker" varchar(5) REFERENCES "company" ("symbol")
        );
        """

    data_create = """CREATE TABLE IF NOT EXISTS "data" (
        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "date" date NOT NULL,
        "value" decimal NOT NULL,
        "ds_id" varchar(50) NOT NULL REFERENCES "data_series" ("series_id")
        );
        """

    db.create_table(company_create)
    db.create_table(data_series_create)
    db.create_table(data_create)
    
if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
