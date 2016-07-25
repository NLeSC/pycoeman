 #!/usr/bin/python
import os, argparse, shutil
import multiprocessing
from lxml import etree
from pycoeman import utils_execution

def runChild(childIndex, commandsQueue, resultsQueue, dataAbsPath, executionFolderAbsPath, onlyShowCommands):
    kill_received = False
    while not kill_received:
        job = None
        try:
            job = commandsQueue.get()
        except:
            kill_received = True
        if job == None:
            kill_received = True
        else:
            [commandId, command, requiredListFile, requiredElements, outputElements] = job

            listRequired = utils_execution.getRequiredList(dataAbsPath + '/' + requiredListFile)

            # Create a working directory using the specified remoteExeDir
            executionFolderCommandAbsPath = executionFolderAbsPath + '/' + commandId
            utils_execution.initExecutionFolder(dataAbsPath, executionFolderCommandAbsPath, requiredElements + listRequired)
            os.chdir(executionFolderCommandAbsPath)

            # Run the execution of the command (which includes cpu, mem and disk monitoring)
            utils_execution.executeCommandMonitor(commandId, command, dataAbsPath, onlyShowCommands)

            resultsQueue.put([commandId,])

def run(dataDir, exeDir, configFile, numProc, onlyShowCommands):
    dataAbsPath = os.path.abspath(dataDir)
    executionFolderAbsPath = os.path.abspath(exeDir)

    if os.path.isdir(executionFolderAbsPath):
        raise Exception(executionFolderAbsPath + ' already exists!')

    if dataAbsPath == executionFolderAbsPath:
        raise Exception('Execution folder must be different than the data directory')

    # Read configuration of commands to execute
    e = etree.parse(configFile).getroot()
    mmComponents = e.findall('Component')

    commandsQueue = multiprocessing.Queue()

    for mmComponent in mmComponents:
        # Run component of workflow
        commandId = mmComponent.find("id").text.strip()
        if commandId.count(' '):
            raise Exception('Command IDs cannot contain whitespaces!')
        command = mmComponent.find("command").text.strip()
        requiredListFile = mmComponent.find("requirelist").text.strip()
        requiredElements= mmComponent.find("require").text.strip().split()
        outputElements = mmComponent.find("output").text.strip().split()
        commandsQueue.put([commandId, command, requiredListFile, requiredElements, outputElements])
    for i in range(numProc):
        commandsQueue.put(None)

    resultsQueue = multiprocessing.Queue()
    children = []
    for i in range(numProc):
        children.append(multiprocessing.Process(target=runChild, args=(i, commandsQueue, resultsQueue, dataAbsPath, executionFolderAbsPath, onlyShowCommands)))
        children[-1].start()

    results = []
    for mmComponent in mmComponents:
        [commandId,] = resultsQueue.get()
        print(commandId + ' finished!')

    for i in range(numProc):
        children[i].join()

def argument_parser():
   # define argument menu
    description = "Runs a set of commands in parallel. The commands are specified by a XML configuration file. During the execution of each command there is monitoring of the used CPU/MEM/disk by the system."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dataDir',default='', help='Data directory that contains all the required data (if using relative paths in <require> and <requirelist) in the XML configuration file, those path will be relative to the data directory specified with this option)', type=str, required=True)
    parser.add_argument('-c', '--configFile',default='', help='XML configuration file with the several commands.', type=str, required=True)
    parser.add_argument('-e', '--exeDir',default='', help='Execution folder path. The execution of the commands will be done this folder. Each command will be executed in its own subfolder <exeDir>/<commandId>', type=str, required=True)
    parser.add_argument('-n', '--numProc',default='', help='Numper of processes to use', type=int, required=True)
    parser.add_argument('--onlyShowCommands', default=False, help='If enabled, it does not execute the initialization of the execution folder (create links) and it only shows the commands without execute them [default is disabled]', action='store_true')
    return parser

if __name__ == "__main__":
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.dataDir, a.exeDir, a.configFile, a.numProc, a.onlyShowCommands)
    except Exception as e:
        print(e)
