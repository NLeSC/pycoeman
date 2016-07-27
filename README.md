# pycoeman

Python Commands Execution Manager

pycoeman is a Python toolkit for executing command-line commands. It allows the execution of:

- Sequential commands: this is a chain of command-line commands which will be executed one after the other. In other words, this is a set of commands that you would traditionally execute in a Bash script. Normally there is IO dependencies between commands (one command requires the output from one or previous ones).

- Parallel commands: this is a set of command-line commands which are executed in parallel. In other words, this is a set of commands that you would traditionally execute in a Bash script with all the commands as background jobs (with the & at the end). There can not be IO dependencies between commands. This is can be useful for tools which are single-core at programming level but can be parallelized at data level and usually require some final merging process, i.e. the processing of a large dataset can be tackled doing multiple processing of small chunks of the large dataset and in the end combining the outputs.

pycoeman adds CPU/MEM/disk monitoring during the execution of the commands and it allows to create clean execution environments for easier management of your executions (the commands will be executed in different folders separated from where the input data is). pycoeman has tools to run both sequential and parallel commands locally (in the local computer), and also to run parallel commands in SGE clusters (computer clusters with Sun Grid Engine batch-queuing system). pycoeman is configured using XML files.

pycoeman is used by pymicmac (https://github.com/ImproPhoto/pymicmac)

## Installation

Clone this repository and install it with pip (using a virtualenv is recommended):

```
git clone https://github.com/oscarmartinezrubi/pycoeman
cd pycoeman
pip install .
```

Python dependencies: numpy, tabulate, matplotlib, lxml, pandas. These are automatically installed by `pip install .` but some system libraries have to be installed (for example freetype is required by matplotlib and may need to be installed by the system admin)

For now pycoeman works only in Linux systems. Requires Python 3.5.

## Sequential commands

Sequential commands can be executed with pycoeman. Which commands are executed is specified with a XML configuration file. Then, the tool `seqcommands/run_seqcommands_local.py` can be used to run the sequence of commands in the local machine.

The sequential commands XML configuration file must contain a root tag `<SeqCommands>`. Then, for each command we have to add a XML element `<Component>` which must have as child elements at least a `<id>` and a `<command>` elements.

Since the commands will be executed in an independent execution folder, if a command requires some files/folders, these have to be specified with `<require>` or `<requirelist>` tags. (Soft) links are created in the execution folder for the specified files/folders. Using `<require>` is recommended for small number of required files/folders, and they are specified comma-separated. Using `<requirelist>` is recommended when the number of required files/folders is large. In this case they are specified in a separate ASCII file, one file/folder per line. Both `<require>` and `<requirelist>` can be simultaneously used.  

It is important to notice that since all the commands are executed in the same execution folder, if a command in the sequence already 'linked' a file/folder (using `<require>` or `<requirelist>`) there is no need to do it again. An example XML configuration file:

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

## Parallel commands

Parallel commands can be executed with pycoeman. Which commands are executed is specified with a XML configuration file. Then, the tool `parcommands/run_parcommands_local.py` can be used to run the sequence of commands in the local machine. There are also tools in `parcommands/run_parcommands_sge_cluster` to for running the commands in a SGE cluster.

The parallel commands XML configuration file must contain a root tag `<ParCommands>`. Then, for each commands we have to add a XML element `<Component>` which must have as child elements the `<id>` and a `<command>` elements. This is the same as the sequential commands XML configuration file format. However, in this case each `<Component>` tag must also contain a `<output>`, which determines which files or folder are the output. Like in the sequential commands XML configuration file format, `<requirelist>` and `<require>` are also used to define the required data by each command.

When running a parallel commands with pycoeman using `parcommands/run_parcommands_local.py` or `parcommands/run_parcommands_sge_cluster`, each command is executed in a different execution folder and possibly in a different computer. For each command, the required data is copied/linked from the location where the pycoeman tool is launched run is lunched to the remote execution folder, and then the command is executed. When the command is finished the elements indicated in `<output>` are copied back to the location where the pycoeman tool was launched. How the data is copied from the location where the pycoeman tool is launched to the remote execution folders (and viceversa) depends on the used hardware systems.

Note that in this case, the data indicated by `<require>` and `<requirelist>` is not shared between different commands execution. So, in each command `<require>` and `<requirelist>` must indicate ALL the required data. This is different than in the sequential commands execution where the required data can be shared by other commands since they are all executed in the same execution folder. An example XML configuration file:

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


### Parallel commands locally

It is possible to use the local computer to run parallel commands specified by the XML configuration files. Use the tool in `parcommands/run_parcommands_local.py` and specify the number of processes you wish to use. In this case, (soft) links will be created for each of the commands, which will be executed in their own execution folder.

### Parallel commands in SGE clusters

The tools in `parcommands/run_parcommands_sge_cluster` are used to run parallel commands specified by the XML configuration files in SGE clusters. SGE clusters usually have a shared folder where all the nodes can access. However, since massive simultaneous access to the shared folder is discouraged, usually local storage in the execution nodes is used when possible. For pycomean to work properly, the required data must be in a location that can be accessed from all the cluster nodes computers.

The tool `parcommands/run_parcommands_sge_cluster/create_parcommands_sge_jobs.py` creates the submission script. This tool requires to specify the data directory, a setenv file and local output directory. All these files and folders and the XML configuration file must be in a shared folder. The tool also requires to specify a remote execution directory. This is the directory in each remote node where the execution of the commends will be done. To submit the different jobs to the queueing system, run the produced submission script.

It is assumed that the software locations are shared between all the nodes and that the setenv file will set the environment properly in all the nodes.

### Parallel commands in remote hosts with ssh

The tool `parcommands/run_parcommands_ssh.py` is used to run parallel commands in remote hosts. The commands to run are specified by the parallel commands XML configuration file. And the hosts to use are specified by the hosts XML file. An example of the hosts XML file follows:

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

For each remote host we want to use we need to add a `<Host>` XML element. The `<name>` is its host name. `<user>` is the user in the remote host, `<setenv>` is a file in the remote host that is "sourced" before the execution of any command. `<numcommands>` is the number of commands that we want to simultaneously run in the remote host, and `<exedir>` is the directory in the remote host where the commands will be executed. Each command will be executed in `<exedir>/<commandId>`.

IMPORTANT:
 - The host name must be a valid ssh-reachable host name. It is assumed that password-less connections are possible with all the involved hosts. So, before running `parcommands/run_parcommands_ssh.py` make sure this is the case. To set password-less connections with remote hosts use SSH keys: generate a key locally with `ssh-keygen` and add a line with the public key in the local machine in `~/.ssh/<key>.pub` to the `~/.ssh/authorized_keys` file in each of the remote hosts.
  - It is assumed that pycoeman and the rest of software which is used by the executed commands is installed in each of the remote hosts. The file specified by `<setenv>` is used to load the environment, so at lest this file must load pycoeman.


### Monitoring

For both sequential and parallel commands, during the execution of each command of the specified in the XML configuration file, the CPU, memory and disk usage of the system are monitored. Note that this include monitoring of ALL the processes running at the system while the command is executed. Monitoring files are created in the execution folder. Concretely a .mon file, a .mon.disk and a .log file. The first one contains CPU/MEM usage monitoring, the second one contains disk usage monitoring and the third one is the log produced by the executed command. To get statistics of .mon files use `monitor/get_monitor_nums.py` and to get a plot use `monitor/plot_cpu_mem.py`. To plot the .mon.disk use `monitor/plot_disk.py`.
