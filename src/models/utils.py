import numpy as np

def train_tune_test_split(data, train=0.7, tune=0.15, test=0.15):
    """
    Spliting the data into training, tuning, and test sets
    using the proportions given. Train + Tune + Test MUST
    equal 1

    :param data: The dataframe with the whole dataset
    :param train: The proportion of the dataset to be used for training
    :param tune: The proportion of the dataset to be used for tuning (IE, early stopping)
    :param test: The proportion of the dataset to be used for testing

    :return: train, tune, test DataFrames
    """
    cutoff = 0.0001
    if abs(1 - (train + tune + test)) > cutoff:
        raise ValueError('Train + Tune + Test must add up to 1')

    first_split = int(train * data.shape[0])
    second_split = int((tune * data.shape[0]) + first_split)

    train_data = data[:first_split]
    tune_data = data[first_split:second_split]
    test_data = data[second_split:]
    return train_data, tune_data, test_data

def xy_split(df):
    """
    splits the dataframe into X (input) and Y (target) data, 
    expecting the target to be called 'label'
    """
    x = df.drop('label', axis=1).values
    y = df['label'].values

    # reshaping for the LSTM
    x = np.reshape(x, (x.shape[0], 1, x.shape[1]))
    return x, y

