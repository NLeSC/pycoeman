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

def initExecutionFolderLocal(executionFolder, elementsAbsPaths, resume = False):
    # Create directory for this execution
    executionFolderAbsPath = os.path.abspath(executionFolder)

    if os.path.exists(executionFolderAbsPath):
        if not resume:
            raise Exception(executionFolder + ' already exists!')
    else:
        os.makedirs(executionFolderAbsPath)

    # Create links for the files/folder specifed in require and requirelist XML
    for elementAbsPath in elementsAbsPaths:
        # Existance of the elementAbsPath has been checked before
        os.symlink(elementAbsPath , os.path.join(executionFolderAbsPath, os.path.basename(elementAbsPath)))


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

def parseComponent(componentInfo, dataAbsPath):
    # Mandatory tags
    commandId = componentInfo.find("id").text.strip()
    if commandId.count(' '):
        raise Exception('Command IDs cannot contain whitespaces!')

    command = componentInfo.find("command").text.strip()

    # Optional tags
    requiredTag = componentInfo.find("require")
    requiredElements = []
    if requiredTag != None:
        requiredElements = requiredTag.text.strip().split()

    requiredListTag = componentInfo.find("requirelist")
    if requiredListTag != None:
        requiredListFile = requiredListTag.text.strip()
        requiredElements.extend(getRequiredList(dataAbsPath + '/' + requiredListFile))

    for i, requiredElement in enumerate(requiredElements):
        if requiredElement.endswith('/'):
            requiredElement = requiredElement[:-1]
        if requiredElement.startswith('/'):
            requiredElementAbsPath = requiredElement
        else:
            requiredElementAbsPath = dataAbsPath + '/' + requiredElement

        if not os.path.exists(requiredElementAbsPath):
            raise Exception(requiredElementAbsPath + ' does not exist!')

        requiredElements[i] = requiredElementAbsPath

    outputTag = componentInfo.find("output")
    outputElements = []
    if outputTag != None:
        outputElements = outputTag.text.strip().split()
        for i, outputElement in enumerate(outputElements):
            if outputElement.startswith('/'):
                raise Exception('outputElements must use relative paths!')
            if outputElement.endswith('/'):
                outputElements[i] = outputElement[:-1]

    return (commandId, command, requiredElements, outputElements)


def parseHost(hostInfo):
    hostName = hostInfo.find("name").text.strip()
    hostUser = hostInfo.find("user").text.strip()
    hostSetenv = hostInfo.find("setenv").text.strip()
    hostNumCommands = int(hostInfo.find("numcommands").text.strip())
    hostExeDir = hostInfo.find("exedir").text.strip()
    if hostExeDir[0] != '/':
        raise Exception('remoteexedir must be an absolute path!')
    if hostSetenv[0] != '/':
        raise Exception('setenv must be an absolute path!')
    return (hostName, hostUser, hostSetenv, hostNumCommands, hostExeDir)

def sshExecute(ssh, command):
    _, stdout, stderr = ssh.exec_command(command)
    return '\n'.join(stderr.readlines() + stdout.readlines())
