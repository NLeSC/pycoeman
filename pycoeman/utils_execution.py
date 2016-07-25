 #!/usr/bin/python
import os
from pycoeman.monitor import monitor_cpu_mem_disk

def executeCommandMonitor(commandId, command, diskPath, onlyPrint=False):
    # Define the names of the script that executes the command, the log file and the monitor file
    logFileName = commandId + '.log'
    monitorLogFileName = commandId + '.mon'
    monitorDiskLogFileName = commandId + '.mon.disk'

    #Remove log file if already exists
    for f in (logFileName,monitorLogFileName,monitorDiskLogFileName):
        if os.path.isfile(f):
            os.system('rm ' + f)

    if onlyPrint:
        print(command)
        os.system('touch ' + logFileName)
        os.system('touch ' + monitorLogFileName)
        os.system('touch ' + monitorDiskLogFileName)
    else:
        monitor_cpu_mem_disk.run(command, logFileName, monitorLogFileName, monitorDiskLogFileName, diskPath)
        # TODO: if execution folder is in different file system that source data, right now we only monitor raw data usage
    return (logFileName,monitorLogFileName,monitorDiskLogFileName)

def initExecutionFolder(dataDir, executionFolder, elements, resume = False):
    # Create directory for this execution
    executionFolderAbsPath = os.path.abspath(executionFolder)

    if os.path.exists(executionFolderAbsPath):
        if not resume:
            raise Exception(executionFolder + ' already exists!')
    else:
        os.makedirs(executionFolderAbsPath)

    # Create links for the files/folder specifed in require and requirelist XML
    for element in elements:
        if element.endswith('/'):
            element = element[:-1]
        if element.startswith('/'):
            elementAbsPath = element
        else:
            elementAbsPath = dataDir + '/' + element
        if os.path.isfile(elementAbsPath) or os.path.isdir(elementAbsPath):
            os.symlink(elementAbsPath , os.path.join(executionFolderAbsPath, os.path.basename(elementAbsPath)))
        else:
            raise Exception(element + ' does not exist!')

def getRequiredList(requiredListFile):
    required = []
    if not os.path.isfile(requiredListFile):
        raise Exception(requiredListFile + ' does not exist!')
    for line in open(requiredListFile, 'r').read().split('\n'):
        if line != '':
            required.append(line)
    return required

def apply_argument_parser(argumentsParser, options=None):
    """ Apply the argument parser. """
    if options is not None:
        args = argumentsParser.parse_args(options)
    else:
        args = argumentsParser.parse_args()
    return args
