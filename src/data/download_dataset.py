import logging
import os

import pandas as pd
import pandas_datareader as pdr
from dotenv import find_dotenv, load_dotenv
from fredapi import Fred

def main():
    fred_api_key = os.environ.get('FRED_API_KEY')
    path_root = os.environ.get('PATH_ROOT')

    ticker = 'CYS'
    series_ids = ['SP500', 'DGS10', 'DGS5', 'USD3MTD156N', 'USD1WKD156N', 'FF']

    fred = Fred(api_key=fred_api_key)
    
    df = {}
    for id in series_ids:
        df[id] = fred.get_series(id)
    df['label'] =  pdr.get_data_yahoo('CYS')['Close']
    df = pd.DataFrame(df)
    
    df.to_csv('{0}/data/raw/{1}-prediction-data.csv'.format(path_root, ticker))
    

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
