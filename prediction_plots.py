import numpy as np
import os
import glob
import sys
import getopt
import matplotlib.pyplot as plt

import matplotlib as mpl
mpl.use("pgf")
plt.style.use('ggplot')
plt.rcParams['figure.edgecolor'] = 'k'
plt.rcParams['figure.facecolor'] = 'w'
plt.rcParams['pgf.texsystem'] = 'pdflatex'
plt.rcParams['savefig.dpi'] = 400
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = "serif"
plt.rcParams['pgf.rcfonts'] = False


start_dates = {'solar': 'Hours since 2016-01-01 00:00:00',
               'demand': 'Hours since 2015-01-01 00:00:00',
               'wind': 'Hours since 2016-11-01 01:00:00'}

norms = {'solar': 4733.25,
         'demand': 81602,
         'wind': 8800}

DATA_PATH = "./publications/forecasting-paper/data/"
IMAGE_PATH = "./publications/forecasting-paper/images/"


def get_prediction_data_list():
    """
    This function returns a list of paths to all .npy loss
    files.

    Returns
    -------
    path_list : list of strings
        The list of paths to output files
    """

    path = DATA_PATH + "*_prediction.npy"

    path_list = glob.glob(path, recursive=True)
    return path_list


def get_input_data_list():
    """
    This function returns a list of paths to all .npy loss
    files.

    Returns
    -------
    path_list : list of strings
        The list of paths to output files
    """

    path = DATA_PATH + "*_input.npy"

    path_list = glob.glob(path, recursive=True)
    return path_list


def get_metadata(data_file):
    """
    This function accepts a file name and returns the parameters
    for the simulation.

    Parameters
    ----------
    data_file : string
        The name of the file that contains the simulation data.
    """

    params = {'n_reservoir': 1000,
              'sparsity': 0.1,
              'rand_seed': 85,
              'rho': 1.5,
              'noise': 0.0001,
              'future': 48,
              'window': 48,
              'trainlen': 5000}

    param_names = {'Reservoir Size': 'n_reservoir',
                   'Sparsity': 'sparsity',
                   'Spectral Radius': 'rho',
                   'Noise': 'noise',
                   'Training Length': 'trainlen',
                   'Prediction Window': 'window'}

    splitstring = data_file.split('/')[-1]
    # print(splitstring)
    target_file = splitstring.replace('npy', 'pgf')
    simulation_name = splitstring.split('_prediction.npy')[0]
    # print(simulation_name)

    with open(DATA_PATH + "simulation_MD.txt", 'r') as file:
        metadata = file.readlines()

    for i, line in enumerate(metadata):
        if simulation_name in line:
            param_string = metadata[i + 1]
            break

    param_list = param_string.split(',')
    for p in param_list:
        splitp = p.split(':')
        name, value = splitp[0].strip(), splitp[1].strip()
        # print(name,value)
        key = param_names[name]
        if name in ['Reservoir Size', 'Training Length', 'Prediction Window']:
            params[key] = int(value)
        else:
            params[key] = float(value)

    # print(params)

    return params, param_string, target_file, simulation_name


if __name__ == "__main__":

    # get list of paths for prediction data and input data
    prediction_list = get_prediction_data_list()
    input_list = get_input_data_list()

    # for i,p in zip(input_list, prediction_list):
    #     print(i, p)

# Start of for loop

    for pfile in prediction_list:
        params, pstring, plot_target, simname = get_metadata(pfile)
        print(simname)

        idx = [i for i, v in enumerate(input_list) if simname in v][0]
        # print(idx, input_list[idx])
        input_file = input_list[idx]

        # open the input data
        input_data = np.load(input_file)

        # open the prediction
        prediction = np.load(pfile)

        # print(params)

        # ================================
        # Plot the Prediction
        # ================================
        futureTotal = params['future']
        colwidth = 3.07242 * 2
        height = 0.5 * colwidth
        hours = np.arange(0, len(input_data), 1)

        if 'lorenz63' in simname:
            height = 0.75 * colwidth
            plt.figure(figsize=(colwidth, height))
            futureTotal = 500
            t = np.arange(0, 100, 0.02)
            ax1 = plt.subplot(311)
            ax1.plot(t[-2 * futureTotal:],
                     input_data[-2 * futureTotal:, 0],
                     label='Ground Truth')
            ax1.plot(t[-futureTotal:],
                     prediction[:, 0], label='Prediction')
            ax2 = plt.subplot(312, sharex=ax1)
            ax2.plot(t[-2 * futureTotal:],
                     input_data[-2 * futureTotal:, 1],
                     label='Ground Truth')
            ax2.plot(t[-futureTotal:],
                     prediction[:, 1],
                     label='Prediction')
            ax3 = plt.subplot(313, sharex=ax1)
            ax3.plot(t[-2 * futureTotal:],
                     input_data[-2 * futureTotal:, 2],
                     label='Ground Truth')
            ax3.plot(t[-futureTotal:],
                     prediction[:, 2],
                     label='Prediction')

            ax3.set_xlabel("t")  # , fontsize=16)
            ax1.set_ylabel("x")  # , fontsize=16)
            ax2.set_ylabel("y")  # , fontsize=16)
            ax3.set_ylabel("z")  # , fontsize=16)
            plt.subplots_adjust(hspace=.5)
            plt.legend(loc=(1.02, 1.65), fancybox=True, shadow=True)
        else:
            plt.figure(figsize=(colwidth, height))
            if 'demand' in simname:
                plt.title(f"Demand Prediction with an ESN")
                plt.ylabel("Energy Demand [kW]")
                plt.xlabel(start_dates['demand'])
                norm = norms['demand']
                label = f'True Demand'
            elif 'solar' in simname:
                plt.title(f"Solar Generation Prediction with an ESN")
                plt.xlabel(start_dates['solar'])
                plt.ylabel("Solar Power [kW]")
                norm = norms['solar']
                label = f'True Solar Generation'

            # I don't think this will be a problem since I check wind last
            # but it *may* do this for 'demand_windspeed'.
            elif 'wind' in simname:
                plt.title(f"Wind Generation Prediction with an ESN")
                plt.ylabel("Wind Power [kW]")
                plt.xlabel(start_dates['wind'])
                norm = norms['wind']
                label = f'True Wind Generation'

            # plot the truth
            plt.plot(hours[-2 * futureTotal:],
                     input_data.T[0][-2 * futureTotal:] * norm,
                     'b',
                     label=f"{label}",
                     alpha=0.7,
                     color='k',
                     markersize=5,
                     marker='.')
            # plot the prediction
            plt.plot(hours[-futureTotal:], norm * prediction.T[0], alpha=0.8,
                     label='ESN Prediction',
                     color='red',
                     linestyle='-',
                     markersize=5,
                     marker='.')
            plt.legend(loc=(1.02, 0.45), fancybox=True, shadow=True)
            if any(prediction.T[0] < 0):
                x = hours[-futureTotal:]
                y1 = 0
                y2 = norm * prediction.T[0]
                plt.axhline(y=y1, alpha=0)
                plt.fill_between(x, y1, y2,
                                 where=(y2 <= y1),
                                 linestyle='-',
                                 color='gray',
                                 alpha=0.6)

        # save prefix should be something like "04_wind_elevation"
        plt.savefig(IMAGE_PATH + simname + '_prediction.pgf')
        plt.close()
        plt.show()
