 #!/usr/bin/python
import os, argparse
from lxml import etree
from pycoeman import utils_execution

def run(dataDir, exeDir, configFile, onlyShowCommands, resume):
    cwd = os.getcwd()
    dataAbsPath = os.path.abspath(dataDir)
    executionFolderAbsPath = os.path.abspath(exeDir)

    if dataAbsPath == executionFolderAbsPath:
        raise Exception('Execution folder must be different than the data directory')

    # Read configuration of commands to execute
    e = etree.parse(configFile).getroot()
    componentsInfo = e.findall('Component')

    # Check for duplicated commandIds and compile list of all required elements
    commandsIds = []
    commands = []
    requiredElementsAll = []
    for componentInfo in componentsInfo:
        (commandId, command, requiredElements, _) = utils_execution.parseComponent(componentInfo, dataAbsPath)
        if commandId in commandsIds:
            raise Exception('Duplicated commandId ' + commandId + '. commandId must be unique!')
        commandsIds.append(commandId)
        commands.append(command)
        requiredElementsAll.extend(requiredElements)

    # Initialize execution folder (i.e. create links)
    utils_execution.initExecutionFolderLocal(executionFolderAbsPath, requiredElementsAll, resume)

    if not onlyShowCommands:
        # Change directory to execution folder
        os.chdir(executionFolderAbsPath)

    for i, commandId in enumerate(commandsIds):
        # Run component
        utils_execution.executeCommandMonitor(commandId, commands[i], dataAbsPath, onlyShowCommands)

    # Change directory to initial folder
    os.chdir(cwd)

def argument_parser():
   # define argument menu
    description = "Run a set of commands sequentially (one after the other). The commands are specified by a XML configuration file. During the execution of each command there is monitoring of the used CPU/MEM/disk by the system."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dataDir',default='', help='Data directory that contains all the required data (if using relative paths in <require> and <requirelist) in the XML configuration file, those path will be relative to the data directory specified with this option)', type=str, required=True)
    parser.add_argument('-c', '--configFile',default='', help='XML configuration file with the several commands.', type=str, required=True)
    parser.add_argument('-e', '--exeDir',default='', help='Execution folder path. The execution of the commands will be done in a folder where links to required data will be made.', type=str, required=True)
    parser.add_argument('--onlyShowCommands', default=False, help='If enabled, it does not execute the initialization of the execution folder (create links) and it only shows the commands without execute them [default is disabled]', action='store_true')
    parser.add_argument('--resume', default=False, help='If enabled, it does not raise exception if the execution folder exists. This is useful when you want to redo some of the commands. If you use this option be sure to update the <require> and <requirelist> accordingly to avoid trying to link data that is already in the execution folder [default is disabled]', action='store_true')
    return parser

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.dataDir, a.exeDir, a.configFile, a.onlyShowCommands, a.resume)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
