def spread(data, col1, col2):
    """
    Generates the difference between col1 and col2, and adds
    a third column with result, titled col1-col2

    :param data: Original DataFrame
    :param col1: The name of the first column
    :param col2: The name of the second column

    :return: An updated dataframe with the spread of the two columns
    """
    difference = data[col1] - data[col2]
    spread_name = '{0}-{1}'.format(col1, col2)
    return data.assign(**{spread_name: difference})

def add_autoregressive(data, column):
    """
    Adds an autoregressive term using the column specified. Names
    the new column 'column_ar', where column is the value passed
    in the column variable.

    :param data: A Pandas dataframe
    :param column: the column to use for the autoregressive term

    :return: A new dataframe
    """
    ar_term = getattr(data, column).shift(1)
    ar_name = '{0}_ar'.format(column)
    # Using dict unpacking to get around using a variable as a keyword argument
    return data.assign(**{ar_name: ar_term})