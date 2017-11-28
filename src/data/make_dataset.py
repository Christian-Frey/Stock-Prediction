# -*- coding: utf-8 -*-
import os, sys
import click
import logging
from dotenv import find_dotenv, load_dotenv
from sklearn.preprocessing import MinMaxScaler

import pandas as pd

# add the 'src' directory as one where we can import modules
src_dir = os.path.join(os.getcwd(), 'src')
sys.path.append(src_dir)
from features.build_features import spread, add_autoregressive


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed)
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    df = pd.read_csv(input_filepath)
    
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    df = spread(df, 'DGS10', 'DGS5')
    df = add_autoregressive(df, 'label')

    df['FF'] = df['FF'].interpolate(method='polynomial', order=3)
    df.dropna(inplace=True)

    scaler = MinMaxScaler(feature_range=(0.1,0.9))
    df[df.columns] = scaler.fit_transform(df[df.columns])

    df.to_csv(output_filepath)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
