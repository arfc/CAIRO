import numpy as np
from pyESN.pyESN import ESN


def MSE(yhat, y):
    '''
    This function calculates the mean squared error between
    a predicted and target vector.

    Parameters:
    -----------
    yhat : numpy array
        The predicted, approximated, or calculated vector
    y : numpy array
        The target vector

    Returns:
    --------
    mse : float
        The mean squared error between yhat and y.
    '''
    mse = np.sqrt(np.mean((yhat.flatten() - y.flatten())**2))

    return mse


def optimal_values(loss, xset, yset):
    """
    This function returns the optimal set of values given
    a matrix of error values. The optimal set is the pair
    of values that minimizes the error.

    Parameters:
    -----------
    loss : numpy matrix
        The matrix of loss values.

    Returns:
    --------
    x, y : float
        The optimal set of values
    """

    minLoss = np.min(loss)
    index_min = np.where(loss == minLoss)
    x_optimal = xset[int(index_min[0])]
    y_optimal = yset[int(index_min[1])]

    return x_optimal, y_optimal


def esn_prediction(data, params):
    """
    This function generates a prediction with an ESN over
    the specified time range. Currently, only n_inputs=n_outputs
    is supported.

    Parameters:
    -----------
    data : numpy array
        This is the dataset that the ESN should train and predict.
        If the training length plus the future total exceed the
        length of the data, an error will be thrown.
        **The shape of the transpose of the data will determine
        the number of inputs and outputs.**

        E.g. Two datasets trained together

        >>> X_in = np.concatenate([[set1, set2]], axis=1)
        >>> pred = esn_prediction(X_in.T, params)

    params : dictionary
        A dictionary containing all of the parameters required to
        initialize an ESN.
        Required parameters are:
            "n_reservoir" : int, the reservoir size
            "sparsity" : float, the sparsity of the reservoir
            "rand_seed" : int or None, specifies the initial seed
            "rho" : float, the spectral radius
            "noise" : the noise used for regularization
            "trainlen" : int, the training length
            "future" : int, the total prediction length
            "window" : int or None, the window size

    Return:
    -------
    prediction : numpy array
        The prediction generated by the ESN. Should have the
        same second dimension as data.
    """

    # get the shape
    ndims = len(data.shape)
    if ndims > 1:
        n_vars = data.shape[1]
    else:
        n_vars = 1

    esn = ESN(n_inputs=n_vars,
              n_outputs=n_vars,
              n_reservoir=params['n_reservoir'],
              sparsity=params['sparsity'],
              random_state=params['rand_seed'],
              spectral_radius=params['rho'],
              noise=params['noise'])

    trainlen = params['trainlen']
    futureTotal = params['future']
    pred_tot = np.ones((futureTotal, n_vars))

    # train the ESN
    pred_training = esn.fit(np.ones((trainlen, n_vars)),
                            data[-trainlen-futureTotal:-futureTotal])
    prediction = esn.predict(pred_tot)

    return prediction


if __name__ == "__main__":
    x = np.array([-1, 0, 0])
    y = np.array([1, 0, 0])
    b = np.outer(x, y)
    min_set = (-1, 1)

    opt_set = optimal_values(b, x, y)
