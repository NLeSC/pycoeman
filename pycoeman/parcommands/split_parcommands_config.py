 #!/usr/bin/python
import os, argparse
from lxml import etree
from pycoeman import utils_execution

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def run(configFile, outputFolder, num):
    configFileAbsPath = os.path.abspath(configFile)
    outputFolderAbsPath = os.path.abspath(outputFolder)

    if os.path.isdir(outputFolderAbsPath):
        raise Exception(outputFolderAbsPath + ' already exists!')
    os.system('mkdir -p '  + outputFolderAbsPath)

    if not os.path.isfile(configFileAbsPath):
        raise Exception(configFileAbsPath + ' does not exist')

    # Read configuration of commands to execute
    e = etree.parse(configFileAbsPath).getroot()
    componentsInfo = list(e.findall('Component'))

    chunkId = 0
    for chunk in chunks(componentsInfo, num):
        ofile = open(outputFolderAbsPath + '/' + str(chunkId) + '_' + os.path.basename(configFileAbsPath), 'w')
        ofile.write('<ParCommands>\n')
        for componentInfo in chunk:
            ofile.write('  ' + etree.tostring(componentInfo, pretty_print=True, encoding='utf-8').decode('utf-8').strip() + '\n')
        ofile.write('</ParCommands>\n')
        ofile.close()
        chunkId+=1


def argument_parser():
   # define argument menu
    description = "Splits a XML configuration file for parallel commands in multiple XML configuration files, each having a maximum number of commads specified by the user"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--configFile',default='', help='XML configuration file with the several commands', type=str, required=True)
    parser.add_argument('-o', '--outputFolder',default='', help='Output folder', type=str, required=True)
    parser.add_argument('-n', '--num',default='', help='Number of commands per output XML configurafion file', type=int, required=True)
    return parser

def main():
    try:
        a = utils_execution.apply_argument_parser(argument_parser())
        run(a.configFile, a.outputFolder, a.num)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
