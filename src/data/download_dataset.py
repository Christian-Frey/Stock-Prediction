import logging
import os

import pandas as pd
import pandas_datareader as pdr
from dotenv import find_dotenv, load_dotenv
from fredapi import Fred
import db_helper as db

def main():
    fred_api_key = os.environ.get('FRED_API_KEY')
    fred = Fred(api_key=fred_api_key)

    db = db.DB_Helper(os.environ.get('DB_PATH'))

    ticker = 'CYS'
    series_ids = ['SP500', 'DGS10', 'DGS5', 'USD3MTD156N', 'USD1WKD156N', 'FF']
    
    # Ticker download
    if db.have_data_for_series(ticker):
        logging.info('have data for {0} - not downloading'.format(ticker))
    else:
        ds = pdr.data.DataReader(ticker, 'yahoo')
        db.add_data_series_and_data_yahoo(ds, ticker)
        logging.info('Added data for %s', ticker)

    # Series download
    for id in series_ids:
        if db.have_data_for_series(id):
            logging.info('have data for {0} - not downloading'.format(id))
        else:
            ds_meta = fred.get_series_info(id)
            db.add_data_series_fred(ds_meta)
            
            ds_data = fred.get_series(id)
            db.add_data_fred(ds_data, id)
            logging.info('added data for %s', id)
    

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
