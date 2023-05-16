# Imports
from abaqus import *
from odbAccess import *
import job
import sys

def main(argv):
    # inputs
    args = argv[-2:]

    filename = args[0]
    stepname = args[1]

    # Opening output data base
    odb = openOdb(path=filename)

    # Getting the last frame of the first step
    lastFrame = odb.steps[stepname].frames[-1]

    # Getting elements nodal forces
    f1 = lastFrame.fieldOutputs['NFORC1']
    f2 = lastFrame.fieldOutputs['NFORC2']
    # f3 = lastFrame.fieldOutputs['NFORC3']


    # Organizing data as each DoF is a diferent output field in Abaqus
    data = {}

    # looping over nodal force 1
    for f in f1.values:
        elementLabel = f.elementLabel
        nodeLabel = f.nodeLabel
        force = f.dataDouble
        try:
            elNodes = data[elementLabel]
            try:
                data[elementLabel][nodeLabel].append(force)
            except:
                data[elementLabel][nodeLabel] = [force,]
        except:
            data[elementLabel] = {nodeLabel: [force,]}

    # looping over nodal force 2
    for f in f2.values:
        elementLabel = f.elementLabel
        nodeLabel = f.nodeLabel
        force = f.dataDouble
        data[elementLabel][nodeLabel].append(force)

    # looping over nodal force 3
    # for f in f3.values:
    #     elementLabel = f.elementLabel
    #     nodeLabel = f.nodeLabel
    #     force = f.data
    #     data[elementLabel][nodeLabel].append(force)

    # printing the output out in INSANE's format
    output = "forcesAbaqus.txt"
    with open(output, 'w') as file:
        for el in data:
            file.write("Element {:>5}:\n".format(el))
            for node in data[el]:
                file.write("   Node {:>5}:".format(node))
                for gl in data[el][node]:
                    file.write("{:>23.15e}".format(gl))
                file.write('\n')
            file.write('\n')    

    odb.close()  

if __name__=="__main__":
    main(sys.argv)