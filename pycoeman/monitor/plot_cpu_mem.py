 #!/usr/bin/python
import os, argparse
import numpy
import pandas
import matplotlib.pyplot as plt
from pycoeman import utils_execution
from pycoeman.monitor import get_monitor_nums

def run(inputArgument, resampling, ignoreLargeJumps):
    availMap = {}
    if os.path.isfile(inputArgument):
        (df, hostname, numcores, memtotal)  = get_monitor_nums.readFile(inputArgument, resampling, ignoreLargeJumps)
        availMap[hostname] = (numcores, memtotal)
    else:
        if resampling == None or resampling < 2:
            raise Exception('Resampling must at least 2 seconds if combining monitor files!')

        monFiles = [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(inputArgument)
            for f in files if f.endswith('.mon')]

        dfMap = {}
        for i, monFile in enumerate(monFiles):
            (df_mon, hostname, numcores, memtotal)  = get_monitor_nums.readFile(monFile, resampling, ignoreLargeJumps)
            availMap[hostname] = (numcores, memtotal)
            df_inter = df_mon.interpolate(method='time')
            # print(str(df_inter.index[0]) + ' ' + str(df_inter.index[-1]))
            if hostname in dfMap:
                dfConcat = df_inter.drop(df_inter.index.intersection(dfMap[hostname].index))
                dfMap[hostname] = pandas.concat((dfMap[hostname], dfConcat))
            else:
                dfMap[hostname] = df_inter

        hostnames = list(dfMap.keys())
        df = None
        for i, hostname in enumerate(hostnames):
            if i == 0:
                df = dfMap[hostname]
            else:
                df = df.add(dfMap[hostname], fill_value=0)

    print('Elapsed time: ' + str((df.index.max() - df.index.min()).total_seconds()))
    print('Avg. CPU: ' + '%0.2f' % df['CPU'].mean())
    print('Avg. MEM [GB]: ' + '%0.2f' % df['MEM'].mean())
    print('Numger used hosts: ' + str(len(availMap)))
    (availCPU, availMEM) = numpy.array(list(availMap.values())).sum(axis=0)
    print('Avail. CPU: ' + '%0.2f' % (100. * availCPU))
    print('Avail. MEM [GB]: ' + '%0.2f' % availMEM)

    _, ax1 = plt.subplots()
    df['CPU'].plot(ax=ax1)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('CPU [%]', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')
    ax2 = ax1.twinx()
    df['MEM'].plot(ax=ax2, color='r')
    ax2.set_ylabel('MEM [GB]', color='r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
    plt.show()

def argument_parser():
   # define argument menu
    description = "Plot the CPU/MEM usage of a command executed using pycoeman (it is possible to combine .mon files of Distributed Tool execution)"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input',default='', help='Input argument. It can be a single .mon file or a folder that contain .mon files. In the case of a folder, the .mon files are searched recursively, and the time-series are resampled/interpolated/combined to display a single graph with the aggregated CPU/MEM usage', type=str, required=True)
    parser.add_argument('-r', '--resampling',default=None, help='Resampling in seconds of the time series (it input is a folder, resampling must be higher than 2 seconds)', type=int, required=False)
    parser.add_argument('--ignoreLargeJumps', default=False, help='If enabled, it ignores large (> 5 seconds) time jumps in the monitor files. Use this for example when you were running your processes in a Virtual Machine and you had to suspend it for a while [default is disabled]', action='store_true')
    return parser

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.input, a.resampling, a.ignoreLargeJumps)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
