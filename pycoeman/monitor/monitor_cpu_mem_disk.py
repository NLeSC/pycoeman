#!/usr/bin/env python
import subprocess,sys,time,multiprocessing,os

def executeScript(osExeCommand, logFile):
    sys.stdout = open(logFile,'w')
    sys.stderr = sys.stdout
    subprocess.Popen(osExeCommand, shell = True, stdout=sys.stdout, stderr=sys.stdout).communicate()

def disk_usage(path):
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return (total, used, free)

def getHostName():
    return os.popen('hostname').read().strip()

def getNumCores():
    return int(os.popen('nproc').read())

def getTotalMemGB():
    return int(os.popen('free -b').read().split('\n')[1].split()[1]) / 1073741824

def addMonitorUsage(monFile, parentpid = None):
    ti = time.time()
    if parentpid != None:
        command = "ps --forest --no-headers -o %cpu,%mem -g $(ps -o sid= -p " + str(parentpid) + ") | awk '{sumC+=$1; sumM+=$2} END {print sumC,sumM}'"
    else:
        command = "ps aux | awk '{sumC+=$3; sumM+=$4} END {print sumC,sumM}'"
    (out,_) = subprocess.Popen(command, shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    (c,m) = out.decode("utf-8").split()
    c = float(c)
    m = float(m)
    monFile.write(("%0.2f" % ti) + ' ' + ("%0.2f" % c) + ' ' + ("%0.2f" % m) + '\n')
    monFile.flush()

def addMonitorDiskUsage(monFile, diskMountPoint):
    ti = time.time()
    (total, used, free) = disk_usage(diskMountPoint)
    monFile.write(("%0.2f" % ti) + ' ' + str(total) + ' ' + str(used) + ' ' + str(free) + '\n')
    monFile.flush()

def run(osExeCommand, logFile, monitorFile, monitorDiskFile, diskMountPoint):
    o = open(monitorFile,'w')
    o2 = open(monitorDiskFile,'w')

    o.write('#Host name: ' + str(getHostName()) + '\n')
    o.write('#Number cores: ' + str(getNumCores()) + '\n')
    o.write('#System memory [GB]: ' + str(getTotalMemGB()) + '\n')

    parentpid = os.getpid()

    # Add one usage before starting launching command
    addMonitorUsage(o, parentpid)
    addMonitorDiskUsage(o2,  diskMountPoint)

    child = multiprocessing.Process(target=executeScript, args=(osExeCommand,logFile))
    child.start()
    counter = 0
    while child.is_alive():
        addMonitorUsage(o, parentpid)
        if (counter % 50) == 0:
            addMonitorDiskUsage(o2, diskMountPoint)
        child.join(1)
        counter+=1

    # Add one usage after finishing launching command
    addMonitorUsage(o, parentpid)
    addMonitorDiskUsage(o2, diskMountPoint)

    o.close()
    o2.close()

if __name__ == "__main__":
    osExeCommand = sys.argv[1]
    logFile = sys.argv[2]
    monitorFile = sys.argv[3]
    monitorDiskFile = sys.argv[4]
    diskMountPoint = sys.argv[5]
    run(osExeCommand, logFile, monitorFile, monitorDiskFile, diskMountPoint)
