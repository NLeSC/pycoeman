 #!/usr/bin/python
import os, argparse
import multiprocessing
from lxml import etree
import paramiko
from scp import SCPClient
from pycoeman import utils_execution

def runCommand(commandConfFile):
    try:
        e = etree.parse(commandConfFile).getroot()
        commandId =  e.find("id").text.strip()
        command =  e.find("command").text.strip()
        executionFolderCommandAbsPath =  e.find("exedir").text.strip()
        onlyShowCommands = e.find("onlyshow").text.strip() == 'True'

        # Change directory to be in the working dir
        os.chdir(executionFolderCommandAbsPath)
        (logFile, monitorFile, monitorDiskFile) = utils_execution.executeCommandMonitor(commandId, command, executionFolderCommandAbsPath, onlyShowCommands)
        print()
        print('COMMANDID ' + commandId + ' LOG ' + logFile)
        print('COMMANDID ' + commandId + ' MON ' + monitorFile)
        print('COMMANDID ' + commandId + ' MONDISK ' + monitorDiskFile)
    except Exception as err:
        print()
        print('COMMANDID ' + commandId + ' KO')
        print(err)

def writeCommandXMLFile(confFileAbsPath, commandId, command, executionFolderCommandAbsPath, onlyShowCommands):
    confFile = open(confFileAbsPath, 'w')
    confFile.write('<RemoteCommand>\n')
    confFile.write('  <id>' + commandId + '</id>\n')
    confFile.write('  <command>' + command + '</command>\n')
    confFile.write('  <exedir>' + executionFolderCommandAbsPath + '</exedir>\n')
    confFile.write('  <onlyshow>' + str(onlyShowCommands) + '</onlyshow>\n')
    confFile.write('</RemoteCommand>\n')
    confFile.close()


def runChild(hostName, childIndex, commandsQueue, resultsQueue, dataAbsPath, localExeDirAbsPath, localOutDirAbsPath, hostUser, hostSetenv, hostExeDir, onlyShowCommands):
    # Create a SSH and a SCP client for this child.
    # This child is running in the local machine and is used to run the remote commands in the core <childIndex> in host <hostName>
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostName, username=hostUser)
    scp = SCPClient(ssh.get_transport())

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
            [commandId, command, requiredElements, outputElements] = job
            message = ""
            statusOk = True

            # Create a execution dir in the local machine to put th erequired files for the remote execution
            commandLocalExeDirAbsPath = localExeDirAbsPath + '/' + commandId
            os.makedirs(commandLocalExeDirAbsPath)

            # Create a output directory in the local machine to copy back the results
            commandLocalOutDirAbsPath = localOutDirAbsPath + '/' + commandId
            os.makedirs(commandLocalOutDirAbsPath)

            # Remote execution folder for this command
            executionFolderCommandAbsPath = hostExeDir + '/' + commandId

            # Create a working directory for the current command using the specified remoteExeDir
            # First we remove it
            result = utils_execution.sshExecute(ssh, 'rm -rf ' + executionFolderCommandAbsPath)
            if result != '':
                statusOk = False
                message += result
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue
            result = utils_execution.sshExecute(ssh, 'mkdir -p ' + executionFolderCommandAbsPath)
            if result != '':
                statusOk = False
                message += result
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue

            # Create a file locally with configuration to run the remote command
            confFileAbsPath = commandLocalExeDirAbsPath + '/' + commandId + '.xml'
            writeCommandXMLFile(confFileAbsPath, commandId, command, executionFolderCommandAbsPath, onlyShowCommands)
            # SCP the command configuration file to the remote execution folder
            remoteConfFileAbsPath = executionFolderCommandAbsPath + '/' + os.path.basename(confFileAbsPath)
            try:
                scp.put(confFileAbsPath, remoteConfFileAbsPath)
            except Exception as err:
                statusOk = False
                message += str(err)
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue

            # Create local file with script to run remotely
            exeFileAbsPath = commandLocalExeDirAbsPath + '/' + commandId + '.sh'
            exeFile = open(exeFileAbsPath, 'w')
            exeFile.write('#!/bin/bash\n')
            exeFile.write('source ' + hostSetenv + '\n')
            exeFile.write('python -c "from pycoeman.parcommands import run_parcommands_ssh; run_parcommands_ssh.runCommand(\'' + remoteConfFileAbsPath + '\')"\n')
            exeFile.close()
            os.system('chmod u+x ' + exeFileAbsPath)
            # SCP the script for executing the command to the remote execution folder
            remoteExeFileAbsPath = executionFolderCommandAbsPath + '/' + os.path.basename(exeFileAbsPath)
            try:
                scp.put(exeFileAbsPath, remoteExeFileAbsPath)
            except Exception as err:
                statusOk = False
                message += str(err)
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue

            # Copy required files and folders in the data directory
            for requiredElement in requiredElements:
                requiredElementRemoteAbsPath = executionFolderCommandAbsPath + '/' + os.path.basename(requiredElement)
                try:
                    scp.put(requiredElement, requiredElementRemoteAbsPath, recursive=True)
                except Exception as err:
                    statusOk = False
                    message += str(err)
                    resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                    # Something went wrong with this command, proceed with next one
                    continue

            # Run the execution of the command (which includes cpu, mem and disk monitoring)
            try:
                result = utils_execution.sshExecute(ssh, remoteExeFileAbsPath)
                lines = result.split('\n')
                (logFile, monitorFile, monitorDiskFile) = (None,None,None)
                for line in lines:
                    if line == 'COMMAND ID ' + commandId + ' KO':
                        break
                    elif line.startswith('COMMANDID ' + commandId + ' LOG '):
                        logFile = line.split(' ')[-1]
                    elif line.startswith('COMMANDID ' + commandId + ' MON '):
                        monitorFile = line.split(' ')[-1]
                    elif line.startswith('COMMANDID ' + commandId + ' MONDISK '):
                        monitorDiskFile = line.split(' ')[-1]

                if logFile == None:
                    statusOk = False
                    message += 'ERROR: remote execution log could not be parsed!'
                    message += '\n'.join(lines)
                    resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                    # Something went wrong with this command, proceed with next one
                    continue

                # Copy the monitor files back to the output dir in the shared folder
                for f in (logFile, monitorFile, monitorDiskFile) + tuple(outputElements):
                    fRemoteAbsPath = executionFolderCommandAbsPath + '/' + f
                    fLocalAbsPath = commandLocalOutDirAbsPath + '/' + f
                    if f.count('/'):
                        # The element is somehow defined in a output folder, so we need to create the folder locally
                        os.makedirs(commandLocalOutDirAbsPath + '/' + '/'.join(f.split('/')[:-1]))
                    scp.get(fRemoteAbsPath, fLocalAbsPath, recursive=True)
            except Exception as err:
                statusOk = False
                message += str(err)
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue

            # Clean the local working dir
            result = utils_execution.sshExecute(ssh, 'rm -rf ' + executionFolderCommandAbsPath)
            if result != '':
                statusOk = False
                message += result
                resultsQueue.put([commandId, hostName, childIndex, statusOk, message])
                # Something went wrong with this command, proceed with next one
                continue

            # Put the result in the results queue
            resultsQueue.put([commandId,hostName, childIndex, statusOk, message])

    # Close the SSH and SCP clients
    scp.close()
    ssh.close()

def run(dataDir, configFile, hostsConfigFile, localExeDir, localOutDir, onlyShowCommands):
    dataAbsPath = os.path.abspath(dataDir)
    localExeDirAbsPath = os.path.abspath(localExeDir)
    localOutDirAbsPath = os.path.abspath(localOutDir)

    #Check folders
    if not os.path.isdir(dataAbsPath):
        raise Exception(dataAbsPath + ' does not exist!')
    if os.path.exists(localExeDirAbsPath):
        raise Exception(localExeDirAbsPath + ' already exists!')
    if os.path.exists(localOutDirAbsPath):
        raise Exception(localOutDirAbsPath + ' already exists!')

    # Read configuration of commands to execute and hosts to use
    componentsInfo = etree.parse(configFile).getroot().findall('Component')
    hostsInfo = etree.parse(hostsConfigFile).getroot().findall('Host')

    # Create queue for the commands
    commandsQueue = multiprocessing.Queue()

    #Compute total number of used cores (adding up all the hosts)
    numProcTotal = 0
    for hostInfo in hostsInfo:
        (_, _, _, hostNumCommands, _) = utils_execution.parseHost(hostInfo)
        numProcTotal += int(hostNumCommands)

    # Check uniqueness of commandId and add all the commands to the commands queue
    commandsIds = []
    for componentInfo in componentsInfo:
        (commandId, command, requiredElements, outputElements) = utils_execution.parseComponent(componentInfo, dataAbsPath)
        if commandId in commandsIds:
            raise Exception('Duplicated commandId ' + commandId + '. commandId must be unique!')
        commandsIds.append(commandId)
        commandsQueue.put([commandId, command, requiredElements, outputElements])
    # For each core (of the total) we add a None to indicate each child to die
    for i in range(numProcTotal):
        commandsQueue.put(None)

    # Create a child for every core in every hosts
    resultsQueue = multiprocessing.Queue()
    children = []
    for hostInfo in hostsInfo:
        (hostName, hostUser, hostSetenv, hostNumCommands, hostExeDir) = utils_execution.parseHost(hostInfo)
        for i in range(hostNumCommands):
            children.append(multiprocessing.Process(target=runChild, args=(hostName, i, commandsQueue, resultsQueue, dataAbsPath, localExeDirAbsPath, localOutDirAbsPath, hostUser, hostSetenv, hostExeDir, onlyShowCommands)))
            children[-1].start()

    for i in range(len(commandsIds)):
        [commandId, hostName, childIndex, statusOk, message] = resultsQueue.get()
        if statusOk:
            print(commandId + ' finished OK in ' + hostName + '[' + str(childIndex) + '] !')
        else:
            print(commandId + ' did NOT finished OK in ' + hostName + '[' + str(childIndex) + ']. Error message:')
        if message != '':
            print(message)

    for i in range(numProcTotal):
        children[i].join()

def argument_parser():
   # define argument menu
    description = "Runs a set of commands in parallel in remote hosts. The remote hosts MUST be ssh-reachable and have been configured for password-less access using ssk keys (ssh-keygen in local computer and add ~/.ssh/[key].pub to ~/.ssh/authorized_keys in each of the remote hosts). The commands are specified by a XML configuration file. During the execution of each command there is monitoring of the used CPU/MEM/disk by the system."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dataDir',default='', help='Data directory that contains all the required data (if using relative paths in <require> and <requirelist) in the XML configuration file, those path will be relative to the data directory specified with this option)', type=str, required=True)
    parser.add_argument('-c', '--configFile',default='', help='XML configuration file with the several commands.', type=str, required=True)
    parser.add_argument('-r', '--remoteHosts',default='', help='XML configuration file for the remote hosts.', type=str, required=True)
    parser.add_argument('-e', '--localExeDir',default='', help='Local execution folder. Some files need to be written in the local computer regarding the synchronization of the remote jobs.', type=str, required=True)
    parser.add_argument('-o', '--localOutDir',default='', help='Local output folder. The execution of each command will be done in a remote folder in a remote host, but the output specified in the configuration XML will be copied to a local folder <localOutDir>/<commandId>', type=str, required=True)
    parser.add_argument('--onlyShowCommands', default=False, help='If enabled, it does not execute the initialization of the execution folder (create links) and it only shows the commands without execute them [default is disabled]', action='store_true')
    return parser

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.dataDir, a.configFile, a.remoteHosts, a.localExeDir, a.localOutDir, a.onlyShowCommands)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
