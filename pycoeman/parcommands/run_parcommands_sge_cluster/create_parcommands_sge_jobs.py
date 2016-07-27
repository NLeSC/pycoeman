#!/usr/bin/python
import os, argparse, glob, os, sys
from lxml import etree
from pycoeman import utils_execution

def run(dataDir, configFile, setEnvironmentFileToSource, remoteExeDir, localOutDir, qsuboptions, qsubScript):
    e = etree.parse(configFile).getroot()
    componentsInfo = e.findall('Component')
    numComponents = len(componentsInfo)

    scriptsParentPath = os.path.dirname(os.path.realpath(__file__))
    executable = scriptsParentPath + '/run_parcommands_sge_job.sh'
    executable_python = scriptsParentPath + '/run_parcommands_sge_job.py'

    configFileAbsPath = os.path.abspath(configFile)
    dataAbsPath = os.path.abspath(dataDir)
    localOutDirAbsPath = os.path.abspath(localOutDir)

    if os.path.isfile(qsubScript):
        raise Exception(qsubScript + ' already exists!')

    # Check uniqueness of commandIds and write qsub commands in script
    commandsIds = []
    ofile = open(qsubScript, 'w')
    for componentInfo in componentsInfo:
        (commandId, _, _, _) = utils_execution.parseComponent(componentInfo, dataAbsPath)
        if commandId in commandsIds:
            raise Exception('Duplicated commandId ' + commandId + '. commandId must be unique!')
        commandsIds.append(commandId)
        ofile.write('qsub ' + qsuboptions + ' ' + executable + ' ' + setEnvironmentFileToSource + ' ' + executable_python + ' ' + configFileAbsPath + ' ' + commandId + ' ' + dataAbsPath + ' ' + remoteExeDir + ' ' + localOutDirAbsPath + '\n')
    ofile.close()

def argument_parser():
   # define argument menu
    description = "Creates the jobs to submit to a SGE cluster for the commands specified in the XML configuration file. During the execution of each command there is monitoring of the used CPU/MEM/disk by the system. This assumes that pycoeman and othe required software are installed in the nodes of the SGE cluster (a setenv file is used to set the environment)"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dataDir',default='', help='Data directory with the required data and the parallel configuration folder (this has to be shared and accessible from the cluster nodes)', type=str, required=True)
    parser.add_argument('-c', '--configFile',default='', help='XML configuration file with the several commands that will be executed in parallel through in SGE cluster. This file must be in the data directory', type=str, required=True)
    parser.add_argument('-s', '--source',default='', help='Set environment file (this file is sourced before the remote execution of any command, the file must be in a shared folder and be accessible from the cluster nodes)', type=str, required=True)
    parser.add_argument('-r', '--remoteExeDir',default='', help='Remote execution directory. Each command will be executed in a cluster node in a folder like <remoteExeDir>/<commandId>', type=str, required=True)
    parser.add_argument('-o', '--localOutDir',default='', help='Local output folder. The execution of each command will be done in a remote folder in a SGE node, but the output specified in the configuration XML will be copied to a local folder <localOutDir>/<commandId>', type=str, required=True)
    parser.add_argument('-q', '--qsubScript',default='', help='Output file that will contain the different qsubs commands. Execution this file will lunch (add to processing queue) the different commands in the SGE cluster', type=str, required=True)
    parser.add_argument('--qsuboptions',default='-l h_rt=00:15:00 -N disttool', help='Options to pass to qsub command. At least must include a -N <name> [default is "-l h_rt=00:15:00 -N disttool"]', type=str, required=False)
    return parser

if __name__ == "__main__":
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.dataDir, a.configFile, a.source, a.remoteExeDir, a.localOutDir, a.qsuboptions, a.qsubScript)
    except Exception as e:
        print(e)
