 #!/usr/bin/python
import os, argparse
import matplotlib.pyplot as plt
import numpy
from pycoeman import utils_execution

def run(inputArgument, outputFile):
    if outputFile != None:
        if os.path.exists(outputFile):
            raise Exception('Specified output file name already exists')

    lines = open(inputArgument, 'r').read().split('\n')

    t = []
    tots = []
    useds = []

    for line in lines:
        fields = line.split()
        if len(fields) == 4:
            t.append(float(fields[0]))
            tots.append(int(fields[1]) / 1048576)
            useds.append(int(fields[2]) / 1048576)

    t = numpy.array(t)
    t = t - t[0]

    fig = plt.figure()
    l1, = plt.plot(t, tots, 'r--')
    l2, = plt.plot(t, useds, 'b.-')

    plt.legend((l1, l2), ('Total Disk', 'Used Disk'), loc='upper right', shadow=True)
    plt.xlabel('Time [s]')
    plt.ylabel('Disk [MB]')

    if outputFile == None:
        plt.show()
    else:
        fig.savefig(outputFile)

def argument_parser():
   # define argument menu
    description = "Plot the disk usage of a command executed pycoeman"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input',default='', help='Input .mon.disk file', type=str, required=True)
    parser.add_argument('-o', '--output',default=None, help='Output image name [Optional]. By default the plot is interactive', type=str, required=False)
    return parser

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.input, a.output)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
