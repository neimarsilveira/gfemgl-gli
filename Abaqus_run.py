from abaqus import *
import job
import sys

def main(argv):
    # inputs
    args = argv[-3:]

    fileName = args[0]
    jobName = args[1]
    cpus = int(args[2])

    mdb = openMdb(fileName)
    mdb.jobs[jobName].setValues(numCpus=cpus)
    mdb.jobs[jobName].submit()
    mdb.jobs[jobName].waitForCompletion()

if __name__=="__main__":
    main(sys.argv)