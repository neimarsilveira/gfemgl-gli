from abaqus import *
from abaqusConstants import *
from symbolicConstants import *
import job
import sys
import ast
import regionToolset
import load

def main(argv):
    # inputs
    args = argv[-6:]

    fileName = args[0]
    stepName = args[1]
    modelName = args[2]
    instanceName = args[3]
    dispFile = args[4]
    sup = up = Boolean(int(args[5]))

    mdb = openMdb(fileName)

    a = mdb.models[modelName].rootAssembly
    inst = a.instances[instanceName]
    meshNodeArrayObj = inst.nodes

    if sup:
        for load in mdb.models[modelName].loads.keys():
            mdb.models[modelName].loads[load].suppress()
        for bc in mdb.models[modelName].boundaryConditions.keys():
            mdb.models[modelName].boundaryConditions[bc].suppress()

    disp = {}
    with open(dispFile, 'r') as file:
        lines = [line.rstrip() for line in file]
        for line in lines[1:]:
            l = line.split()
            node = l[0]
            dispValues = [float(i) for i in l[1:]]
            disp[node] = dispValues

    for n in meshNodeArrayObj:
        nodeLabel = str(n.label)
        d1 = float(disp[nodeLabel][0])
        d2 = float(disp[nodeLabel][1])
        name = 'Disp node '+ str(n.label)
        try:
            mdb.models[modelName].boundaryConditions[name].setValues(u1=d1, u2=d2)                 
        except Exception as e:
            meshNodeObj = meshNodeArrayObj.sequenceFromLabels((n.label,))
            region = regionToolset.Region(nodes=meshNodeObj)
            mdb.models[modelName].DisplacementBC(name=name, createStepName=stepName, 
                region=region, u1=d1, u2=d2, fixed=OFF, distributionType=UNIFORM, 
                fieldName='', localCsys=None) 

    mdb.save()
    mdb.close()


if __name__=="__main__":
    main(sys.argv)