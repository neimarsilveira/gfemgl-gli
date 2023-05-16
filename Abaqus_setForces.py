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
    args = argv[-7:]

    fileName = args[0]
    stepName = args[1]
    modelName = args[2]
    IGLnodesSetName = args[3]
    instanceName = args[4]
    forces = ast.literal_eval(args[5])
    sup = Boolean(int(args[6]))

    mdb = openMdb(fileName)

    a = mdb.models[modelName].rootAssembly
    inst = a.instances[instanceName]
    meshNodeArrayObj = inst.nodes
    interface = a.sets[IGLnodesSetName]
    
    if sup:
        for load in mdb.models[modelName].loads.keys():
            mdb.models[modelName].loads[load].suppress()

    for n in interface.nodes:
        nodeLabel = str(n.label)
        f1 = float(forces[nodeLabel][0])
        f2 = float(forces[nodeLabel][1])
        loadName = 'IGL node '+ str(n.label)
        try:
            mdb.models[modelName].loads[loadName].setValues(cf1=f1, cf2=f2, 
                                                            distributionType=UNIFORM, field='')                 
        except Exception as e:
            meshNodeObj = meshNodeArrayObj.sequenceFromLabels((n.label,))
            region = regionToolset.Region(nodes=meshNodeObj)
            mdb.models[modelName].ConcentratedForce(name=loadName, createStepName=stepName, region=region, cf1=f1, cf2=f2, 
                                                    distributionType=UNIFORM, field='', localCsys=None) 

    mdb.save()
    mdb.close()


if __name__=="__main__":
    main(sys.argv)