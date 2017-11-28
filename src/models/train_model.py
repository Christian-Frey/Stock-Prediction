# -*- coding: utf-8 -*-
import os
import logging
import click
from dotenv import load_dotenv, find_dotenv

import numpy as np
import pandas as pd
from keras.callbacks import EarlyStopping
from keras.layers import LSTM, Dense, Input
from keras.models import Model
from keras.optimizers import SGD
from sklearn.metrics import mean_squared_error, r2_score

from utils import train_tune_test_split, xy_split

@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
def main(input_filepath):
    df = pd.read_csv(input_filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    train, tune, test = train_tune_test_split(df, 0.7, 0.15, 0.15)

    train_x, train_y = xy_split(train)
    tune_x, tune_y = xy_split(tune)
    test_x, test_y = xy_split(test)

    model = init_model(train_x.shape[-1])
    logging.info(model.summary())

    epochs = 500
    early_stop = EarlyStopping(monitor='val_loss', patience=30, mode='auto')
    if tune_x is None and tune_y is None:  # No early stopping
        model.fit(train_x, train_y, batch_size=32, epochs=epochs, shuffle=False)
    else:
        model.fit(train_x, train_y, validation_data=(tune_x, tune_y), batch_size=32, epochs=epochs, shuffle=False) 


def init_model(input_y):
    sgd = SGD(lr=0.5)

    in_layer = Input(shape=(None, input_y))
    lstm_1 = LSTM(48, return_sequences=True)(in_layer)
    lstm_2 = LSTM(48, return_sequences=True)(lstm_1)
    lstm_3 = LSTM(48)(lstm_2)
    out_layer = Dense(1)(lstm_3)

    model = Model(inputs=in_layer, outputs=out_layer)
    model.compile(loss='mse', optimizer=sgd, metrics=['mean_squared_error'])
    return model
  
if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
