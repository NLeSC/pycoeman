 #!/usr/bin/python
import os, argparse
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
            [commandId, command, requiredElements, _] = job

            # Create a working directory using the specified remoteExeDir
            executionFolderCommandAbsPath = executionFolderAbsPath + '/' + commandId
            utils_execution.initExecutionFolderLocal(executionFolderCommandAbsPath, requiredElements)
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
    componentsInfo = e.findall('Component')

    # create Queue for the commands to be executed
    commandsQueue = multiprocessing.Queue()

    # Check unique commandsIds and add commands to Queue
    commandsIds = []
    for componentInfo in componentsInfo:
        # Add component to run in the Queue
        (commandId, command, requiredElements, outputElements) = utils_execution.parseComponent(componentInfo, dataAbsPath)
        if commandId in commandsIds:
            raise Exception('Duplicated commandId ' + commandId + '. commandId must be unique!')
        commandsIds.append(commandId)
        commandsQueue.put([commandId, command, requiredElements, outputElements])
    # For each core (of the total) we add a None to indicate each child to die
    for i in range(numProc):
        commandsQueue.put(None)

    resultsQueue = multiprocessing.Queue()
    children = []
    for i in range(numProc):
        children.append(multiprocessing.Process(target=runChild, args=(i, commandsQueue, resultsQueue, dataAbsPath, executionFolderAbsPath, onlyShowCommands)))
        children[-1].start()

    for i in range(len(commandsIds)):
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

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.dataDir, a.exeDir, a.configFile, a.numProc, a.onlyShowCommands)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
