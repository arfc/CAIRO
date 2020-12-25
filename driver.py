import numpy as np
import pandas as pd
import sys, getopt
import time

from tools import esn_prediction, optimal_values, param_string
from optimizers import grid_optimizer
from lorenz import generate_L96
from sunrise import generate_elevation_series

# Optimization Sets
# radius_set = [0.5, 0.7, 0.9, 1, 1.1,1.3,1.5]
# noise_set = [ 0.0001, 0.0003,0.0007, 0.001, 0.003, 0.005, 0.007,0.01]

radius_set = [0.1, 0.5, 1]
noise_set = [0.001, 0.0007, 0.003]

# reservoir_set = [600, 800, 1000, 1500, 2000, 3000, 4000]
# sparsity_set = [0.005, 0.01, 0.03, 0.05, 0.1, 0.15, 0.2]

reservoir_set = [600, 800, 1000]
sparsity_set = [0.005, 0.01, 0.2]

# This must change depending on the length of available data
trainingLengths = np.arange(4000,25000,300)

params = {'n_reservoir':1000,
          'sparsity':0.1,
          'rand_seed':85,
          'rho':1.5,
          'noise':0.0001,
          'future':96,
          'window':96,
          'trainlen':8000}

SOLAR_PATH = "./data/solarfarm_data.csv"
WIND_PATH = "./data/railsplitter_data.csv"
DEMAND_PATH = "./data/"

def main():
    pass


if __name__ == "__main__":

# =============================================================================
# Set Up the Training Data
# =============================================================================
    X_in = []
    data_norms = []
    df = None
    wdf = None
    list_keys = None
    sun_elevation = None
    save_prefix = None
    options_dict = {'-u':'windspeed',
                    '-w':'wettemp',
                    '-d':'drytemp',
                    '-p':'pressure',
                    '-h':'humidity',
                    }

    # get arguments

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'uwdpheH:i:f:oS:',
                                   ['infile=', 'altfile','outfile=',
                                   'save_prefix='])
    except getopt.GetoptError:
        print(f'Valid options are: {options_dict}')
        sys.exit(1)
    # print(args)
    for opt, arg in opts:
        if opt in ('-i', '--infile'):
            try:
                df = pd.read_csv(arg,
                                 usecols=['time', 'kw'],
                                 index_col='time',
                                 parse_dates=True)
            except FileNotFoundError:
                print(f"Data file {arg} not found")

        if opt in ('-f', '--altfile'):
            assert (df is not None), "No data to predict"
            try:
                wdf = pd.read_csv(arg,
                                  index_col='time',
                                  parse_dates=True)
            except FileNotFoundError:
                print(f"Data file {arg} not found")

            list_keys = []
            for key in options_dict.keys():
                if any(key in option for option in opts):
                    # print(f'option present {options_dict[key]}')
                    list_keys.append(options_dict[key])

        if opt in ('-e'):
            # print('adding sun')
            assert (df is not None), "No data to predict"
            sun_elevation = generate_elevation_series(df.index, timestamps=True)

        if opt in ('-S', '--save_prefix'):
            save_prefix = arg

        if opt in ('-H'):
            params['window'] = int(arg)


    # Align the two dataframes
    if wdf is not None:
        # print('dataframes must be aligned')
        xdf = pd.concat([df, wdf], axis=1, join='inner')
        xdf.interpolate('linear', inplace=True)
        # print(xdf.head())
    else:
        xdf = df

    # Get the training data
    power = np.array(xdf.kw).astype('float64')
    power_norm = np.linalg.norm(power)
    data_norms.append(power_norm)
    X_in.append(power/power_norm)


    if sun_elevation is not None:
        # print("Adding sun elevation")
        elevation_norm = np.linalg.norm(sun_elevation)
        data_norms.append(elevation_norm)
        X_in.append(sun_elevation/elevation_norm)

    if list_keys is not None:
        for key in list_keys:
            if key is '-e':
                pass
            else:
                # "Aspect" refers to data for a particular aspect of "weather"
                aspect_data = np.array(xdf[key]).astype('float64')
                aspect_norm = np.linalg.norm(aspect_data)
                data_norms.append(aspect_norm)
                X_in.append(aspect_data/aspect_norm)

    X_in = np.array(X_in)
    print(X_in.shape, len(X_in.shape))


# =============================================================================
# ESN Optimization
# =============================================================================
    MAX_TRAINLEN = int(len(xdf) - params['future'])
    print(f"Maximum training length is {MAX_TRAINLEN}")

    # pred = esn_prediction(X_in.T, params)
    print('Optimizing spectral radius and regularization')
    tic = time.perf_counter()
    radiusxnoise_loss = grid_optimizer(X_in.T,
                        params,
                        args=['rho', 'noise'],
                        xset=radius_set,
                        yset=noise_set,
                        verbose=True,
                        save_path=save_prefix)

    toc = time.perf_counter()
    elapsed = toc - tic
    print(f"This simulation took {elapsed:0.02f} seconds")
    print(f"This simulation took {elapsed/60:0.02f} minutes")

    opt_radius, opt_noise = optimal_values(radiusxnoise_loss,
                                           radius_set,
                                           noise_set)
    params['rho'] = opt_radius
    params['noise'] = opt_noise

    print('Optimizing network size and sparsity')
    tic = time.perf_counter()
    sizexsparsity_loss = grid_optimizer(X_in.T,
                         params,
                         args=['n_reservoir', 'sparsity'],
                         xset=reservoir_set,
                         yset=sparsity_set,
                         verbose=True,
                         save_path=save_prefix)

    toc = time.perf_counter()
    elapsed = toc - tic
    print(f"This simulation took {elapsed:0.02f} seconds")
    print(f"This simulation took {elapsed/60:0.02f} minutes")

    opt_size, opt_sparsity = optimal_values(sizexsparsity_loss,
                                            reservoir_set,
                                            sparsity_set)
    params['n_reservoir'] = opt_size
    params['sparsity'] = opt_sparsity

    trainingLengths = np.arange(5000, MAX_TRAINLEN, 2000)

    print('Optimizing training length')
    tic = time.perf_counter()
    trainlen_loss = grid_optimizer(X_in.T,
                                   params,
                                   args=['trainlen'],
                                   xset=trainingLengths,
                                   verbose=True,
                                   save_path=save_prefix)
    toc = time.perf_counter()
    elapsed = toc - tic
    print(f"This simulation took {elapsed:0.02f} seconds")
    print(f"This simulation took {elapsed/60:0.02f} minutes")

    minloss = np.min(trainlen_loss)
    index_min = np.where(trainlen_loss == minloss)
    l_opt = trainingLengths[index_min][0]
    params['trainlen'] = l_opt
