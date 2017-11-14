**This repository is currently not maintained. We welcome people to fork this repository for further development and maintenance.** 


# pycoeman

[![Build Status](https://travis-ci.org/NLeSC/pycoeman.svg?branch=master)](https://travis-ci.org/NLeSC/pycoeman)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/41716b834df24626a8cce742ac068fce)](https://www.codacy.com/app/omrubi/pycoeman?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NLeSC/pycoeman&amp;utm_campaign=Badge_Grade)
[![DOI](https://zenodo.org/badge/22553/NLeSC/pycoeman.svg)](https://zenodo.org/badge/latestdoi/22553/NLeSC/pycoeman)

Python Commands Execution Manager

pycoeman is a Python toolkit for executing command-line commands. It allows the execution of:

- Sequential commands: this is a chain of command-line commands which will be executed one after the other. In other words, this is a set of commands that you would traditionally execute in a Bash script. Normally there are IO dependencies between commands (one command requires the output from one or previous ones).

- Parallel commands: this is a set of command-line commands which are executed in parallel. In other words, this is a set of commands that you would traditionally execute in a Bash script with all the commands as background jobs (with the & at the end). There cannot be IO dependencies between commands. This is can be useful for pleasingly parallel solutions, i.e. tools which are single-core at programming level but can be parallelized at data level and usually require some final merging process.

pycoeman adds CPU/MEM/disk monitoring during the execution of the commands and it allows to create clean execution environments for easier management of your executions (the commands will be executed in different folders separated from where the input data is). pycoeman has tools to run both sequential and parallel commands locally (in the local computer), and also to run parallel commands in a set of remote hosts accessible via SSH as well as in SGE clusters (computer clusters with Sun Grid Engine batch-queuing system). pycoeman is configured using XML files.

pycoeman is used by pymicmac (https://github.com/ImproPhoto/pymicmac)

## Installation

For now pycoeman only works in Linux systems. It requires Python 3.5 and it is installed using pip.
If Python 3.5 is not the default Python on user's system, the user should use **pip3** to install *pycoeman*.
To avoid issues with dependencies and versions, and indirectly permissions, the use should use [**virtualenv**](https://virtualenv.pypa.io/en/stable/).

* Installing system package dependencies
```
sudo apt-get install freetype libssl-dev libffi-dev
```

* Installing *pycoeman* from sources:
```
git clone https://github.com/NLeSC/pycoeman
cd pycoeman

#If virtualenv is not installed:
sudo apt-get install virtualenv

virtualenv pycoeman_env
. pycoeman_env/bin/activate

pip3 -r requirements.txt install .
```

* Installing *pycoeman* package:
```
#If virtualenv is not installed:
sudo apt-get install virtualenv

virtualenv pycoeman_env
. pycoeman_env/bin/activate

pip3 -r requirements.txt install pycoeman
```

The installation makes the following command-line tools available: `coeman-seq-local`, `coeman-par-local`, `coeman-par-ssh` and `coeman-par-sge`

## Deployment

With *Pycoeman* user's commands are executed either in *sequential mode* or *parallel mode*. The commands, their arguments and the required files/directories
are listed in a XML configuration file. Independent from the execution mode, the commands are either executed at the user's computer (commands with *-local*
suffix) or distributed among a set of machines (commands with either *-ssh* or *-sge* suffix). The ones with *-ssh* suffix use **ssh** to run commands at the
remote hosts. The ones with *-sge* suffix submit the commands as jobs to a Sun Grid Engine queuing system.

### Sequential mode

The sequential commands XML configuration file must contain a root tag `<SeqCommands>` and for each command a XML element `<Component>` is added with two
mandatory nested XML elements, `<id>` and `<command>`. Dependencies on files/directories should be specified with `<require>` or `<requirelist>` tags. (Soft)
links are created in the execution folder for the specified files/folders. Using `<require>` is recommended for small number of required files/folders, and
they are specified comma-separated. Using `<requirelist>` is recommended when the number of required files/folders is large. In this case they are specified in
a separate ASCII file, one file/folder per line. Both `<require>` and `<requirelist>` can be simultaneously used.  

Once the sequential mode XML configuration file is defined the user should use the tools `coeman-seq-[local | ssh | sge]` to execute them. For
local executions, it is important to notice that since all the commands are executed in the same execution folder file/folders already linked
for one of the commands (using `<require>` or `<requirelist>`) they don't need to be linked again. In the following example, *inputfile1* and
*inputfile2* are linked for *Executable1* and re-used for *Executable2*.
```
<SeqCommands>
  <Component>
    <id> Executable1 </id>
    <requirelist>listimages.txt</requirelist>
    <require> inputfile1 inputfile2</require>
    <command> Executable1 *jpg inputfile1 inputfile2 -o outputfile1 </command>
  </Component>
  <Component>
    <id> Executable2 </id>
    <command> Executable2 inputfile1 outputfile1 </command>
  </Component>
</SeqCommands>
```

### Parallel mode

The parallel commands XML configuration file must contain a root tag `<ParCommands>` and for each command a XML element `<Component>` is added with three
mandatory nested XML elements, `<id>`, `<command>` and `<output>`. The latter determines which files and directories should be collected as output. Dependencies
on files/directories should be specified with `<require>` or `<requirelist>` tags. (Soft) links are created in the execution folder for the specified
files/folders. Using `<require>` is recommended for small number of required files/folders, and they are specified comma-separated. Using `<requirelist>`
is recommended when the number of required files/folders is large. In this case they are specified in a separate ASCII file, one file/folder per line.
Both `<require>` and `<requirelist>` can be simultaneously used.  

Once the parallel mode XML configuration file is defined the user should use the tools `coeman-par-[local | ssh | sge]` to execute them. When running in
parallel mode, commands are executed in a different execution folder and possibly in a more than one computer. For each command, the required data is
copied/linked from the location where the pycoeman tool is launched to the remote execution folders. After a successful execution of the commands, the
files listed under the tag `<output>` are copied back to the location where the pycoeman tool was launched. 

For data availability the execution model is share-nothing, i.e., the data indicated by `<require>` and `<requirelist>` is not shared between different
commands execution. Hence, in each command `<require>` and `<requirelist>` must indicate ALL the required data. This is different than in the sequential
commands execution where the required data from a *command A* can be shared with the other commands since they are all executed in the same execution folder.
In the following example, *listimage.list* needs to be specified as *<requirelist>* for both *Executable1* and *Executable2* command.
```
<ParCommands>
  <Component>
    <id>Executable1</id>
    <requirelist>listimages.list</requirelist>
    <require>ParallelConfig/0_Config.xml</require>
    <command>Executable1 *jpg 0_Config.xml -o output1</command>
    <output>output1</output>
  </Component>
  <Component>
    <id>Executable1</id>
    <requirelist>listimages.list</requirelist>
    <require>ParallelConfig/1_Config.xml</require>
    <command>Executable1 *jpg 1_Config.xml -o output2</command>
    <output>output2</output>
  </Component>
</ParCommands>
```

### Remote execution


The tools either with the `-ssh` or `-sge` suffix are used to run commands at remote hosts. In addition to the XML configuration file, the user needs
to specify the hosts XML file. The host XML file has a `<Host>` XML element per each host and five nested XML elements: the `<name>` to define host
name, `<user>` user name at the remote host, `<setenv>` to set environment before each command execution at the remote host, `<numcommands>` to
define the number of commands executed in simultaneously, and `<exedir>` specifies the root directory for each command's execution directory
(each command will then use `<exedir>/<commandId>` as execution directory). An example of the hosts XML file follows:

```
<Hosts>
  <Host>
    <name> localhost </name>
    <user> oscarr </user>
    <setenv> /home/oscarr/.bashrc </setenv>
    <numcommands> 4 </numcommands>
    <exedir> /home/oscarr/test_remote_ssh </exedir>
  </Host>
</Hosts>
```

**IMPORTANT:**
* All the required data is sent to the remote nodes using SCP, therefore, the host name must be a valid ssh-reachable host name. It is assumed that
password-less ssh connections are possible with all the involved hosts. So, before running `coeman-par-ssh` make sure this is the case. To set password-less
connections with remote hosts use SSH keys: generate a key locally with `ssh-keygen` and add the local public key to the remote machine with `ssh-copy-id <remotehost>`.
* It is assumed that pycoeman and all software required by each commands is installed on all remote hosts.
* The file specified by `<setenv>` is used to load the environment at the remote hosts. Hence, the user should make sure all the dependencies, including
*pycoeman* are loaded through `<setenv>`. The same holds for environment variables.

#### SGE clusters

The tools with the suffix `-sge` run commands in clusters with Sun Grid Engine (SGE) queuing system. SGE clusters should have all a shared folder accessable on all the nodes. Having all nodes simultaneously reading and writing to the shared storage is discouraged. Hence, for performance reasons the user should
copy the input data from the shared storage to the node's local storage and use a local directory to store command's outputs.

The *setenv* file and the XML configuration file should be placed at the shared folder. The output of the tools with `-sge` suffix is a submission script.
The user should run it to submit the different jobs to a SGE queuing system. It is assumed that the software locations are shared between all the nodes
and that the setenv file will set the environment properly in all the nodes.

### Monitoring

For both sequential and parallel commands, during the execution of each command of the specified in the XML configuration file, the CPU and memory and usage of the involved processes are monitored (child processes from any of the executed commands are also considered). There is also monitoring of the disk usage (free vs. used file system storage of the data directory). Monitoring files are created in the execution folder. Concretely a .mon file, a .mon.disk and a .log file. The first one contains CPU/MEM usage monitoring, the second one contains disk usage monitoring and the third one is the log produced by the executed command. To get statistics of CPU and memory usage use the tool `coeman-mon-stats`, to plot the CPU and memory usage use the tool`coeman-mon-plot-cpu-mem`, and to plot the disk usage use the tool `coeman-mon-plot-disk`.
