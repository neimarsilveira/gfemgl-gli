# Imports
from abaqus import *
from odbAccess import *
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

    # Getting displacements 'U'
    disp = lastFrame.fieldOutputs['U']

    # Writing displacements into file
    output = "displacementsAbaqus.txt"
    with open(output, 'w') as file:
        file.write("{nodeID:>7} {dx:>24} {dy:>24}\n".format(nodeID="Node ID", dx="x", dy="y"))
        for value in disp.values:
            label = value.nodeLabel
            dx = value.dataDouble[0]
            dy = value.dataDouble[1]
            # dz = value.data[2]
            file.write("{nodeID:7d} {dx:24.15e} {dy:24.15e}\n".format(nodeID=label, dx=dx, dy=dy))

    odb.close()
if __name__=="__main__":
    main(sys.argv)