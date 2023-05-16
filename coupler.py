import model
import toolbox
import shutil
import os
import datetime as dt
import copy
from abc import ABC, abstractmethod


class coupler(ABC):
    def __init__(self, globalModel: model.globalModel, mesoModel: model.mesoModel, tolerance=1e-5 , relax=("Static", 1.0)) -> None:
        self.firstRun = True
        
        self.gm = globalModel
        self.mm = mesoModel
        self.lmPath = mesoModel.getLocalModelPath()

        self.gin = self.gm.inodes
        self.gie = self.gm.ielem
        self.lin = self.mm.inodes
        self.lie = self.mm.ielem
        
        self.epsilon = tolerance
        self.relaxType = relax[0]
        self.relaxFactor = relax[1]

        self.n = 0
        self.residualForcesAcc = {}
        self.rNormRef = None
        self.results = []
    
        self.iwd = os.getcwd()
        self.insaneDir = os.getcwd()
        self.makeFolders()

    def couple(self):
        self.prepareFiles()
        u = self.solveGlobalModel()
        rtb = self.createRelaxationToolBox(u)
        fG = self.getGlobalReaction(u)
        while True:
            self.printIterationMsg()
            if self.n > 0:
                self.sendToGlobal(r)
                du = self.solveGlobalModel() 
                u = toolbox.linAlg.getLinearCombFromDict(1.0, u, 1.0, du)
                u = rtb.relaxation(u=u, du=du, r=r)
                dfG = self.getGlobalReaction(u) 
                fG = toolbox.linAlg.getLinearCombFromDict(1.0, fG, 1.0, dfG)
            self.sendToLocal(u)
            self.solveLocalModel()
            fL = self.getLocalReaction()
            r = self.calculateResidualReaction(fG, fL)

            self.saveFiles()
            self.saveResults(self.n, rtb.beta, toolbox.linAlg.getNormFromDict(r)/self.rNormRef, r["7"][0], r["7"][1])

            if self.checkConvergence(r):
                break
            self.n += 1
        
        self.finalSolution(u)
        self.writeResults('Iteration', 'Relaxation factor', 'Relative residue', 'Node 7 fx', 'Node 7 fy')
    
    def createRelaxationToolBox(self, u:dict) -> toolbox.accelToolBox:
        if self.relaxType == "STATIC":
            return toolbox.staticRelax(self.relaxType, self.relaxFactor, u)
        elif self.relaxType == "DYNAMIC":
            return toolbox.dynamicRelax(self.relaxType, self.relaxFactor, u, self.gin)
        elif self.relaxType == "QNA":
            return toolbox.QNAccelaration(self.relaxType, self.relaxFactor, u)
        else:
            raise RuntimeError("No valid acceleration technique was selected: 'STATIC' (static relaxation), 'DYNAMIC' (dynamic relaxation) or 'QNA' (Quasi-Newton Acceleration).")
    
    def makeFolders(self):
        d = dt.date.today().strftime("%y-%m-%d")
        h = dt.datetime.now().strftime("%Hh%Mm%Ss")
        self.outputFolder = f"{d} {h} - {self.epsilon:.0e} - {self.relaxType[:3]:3} - {self.relaxFactor:.3f}\\"
        
        self.inputFolder = f"{self.outputFolder}Input files\\"
        self.tempFolder = f"{self.outputFolder}temp\\"

        os.mkdir(self.outputFolder)
        os.mkdir(self.inputFolder) 
        os.mkdir(self.tempFolder)

    def calculateResidualReaction(self, globalForces: dict, localReaction: dict) -> dict:
        r = {}
        for node in self.gin:
            fG = globalForces[node]

            position = self.gin.index(node)
            linID = self.lin[position]
            fL = localReaction[linID]

            diff = []
            for fGi, fLi in zip(fG, fL):
                fGi = -1 * fGi # force to reaction
                diff.append(-1*(fGi + fLi))

            r[node] = diff
        
        if self.rNormRef is None:
            self.rNormRef = toolbox.linAlg.getNormFromDict(r)
        
        return r

    def updateResidualForcesAcc(self, r:dict) -> None:
        if self.residualForcesAcc:
            self.residualForcesAcc = toolbox.linAlg.getLinearCombFromDict(1.0, self.residualForcesAcc, 1.0, r)
        else:
            self.residualForcesAcc = dict(r)            


    def checkConvergence(self, r):
        print(f"\nIteration {self.n:003d} completed." +
              f"\nChecking convergence...", end =" ")
        
        rNorm = toolbox.linAlg.getNormFromDict(r)
        if toolbox.linAlg.getNormFromDict(r) >= self.epsilon * self.rNormRef:
            print("Not ok.\n" + 
                  "Relative residual: {:.3e}".format(rNorm/self.rNormRef))
            return False
        else:
            print("Ok.\n" + 
                  "Relative residual: {:.3e}".format(rNorm/self.rNormRef))
            return True

    def printIterationMsg(self):
        txt = " I T E R A T I O N   {:3d} ".format(self.n)
        print("\n{msg:{c}^{n}}".format(msg=txt, c='=', n=60))

    def printFinalMsg(self):
        txt = " F I N A L   S O L U T I O N "
        print(f"{txt:{'='}^{60}}")
        print(f"Relaxation type: {self.relaxType[:3]:.3}\n" +
              f"Relative residue criteria: {self.epsilon:.3e}\n")
        print("Running final solution of the global model...")

    def saveResults(self, *args) -> None:
        self.results.append(args)

    def writeResults(self, *args):
        resultFile = self.iwd + "\\" + self.outputFolder + 'results.csv'
        with open(resultFile, 'w') as file:
            for word in args:
                file.write(f"{word:>20};")
            file.write('\n')
            
            for line in self.results:
                for value in line: 
                    file.write(f"{value:>20};")
                file.write('\n')       

    @abstractmethod
    def saveFiles(self, final=False) -> None:
        pass
    
    @abstractmethod
    def prepareFiles(self) -> None:
        pass

    @abstractmethod
    def sendToGlobal(self, f:dict, final=False) -> None:
        pass
    
    @abstractmethod
    def solveGlobalModel(self) -> None:
        pass

    @abstractmethod
    def sendToLocal(self, u:dict) -> None:
        pass

    @abstractmethod
    def solveLocalModel(self) -> None:
        pass

    @abstractmethod
    def getLocalReaction(self) -> dict:
        pass

    @abstractmethod
    def getGlobalReaction(self, u:dict) -> dict:
        pass

    @abstractmethod
    def finalSolution(self, u:dict) -> None:
        pass

class abaqus(coupler):
    def __init__(self, globalModel: model.abaqusModel, mesoModel: model.insaneModel, abaqusData: list, tolerance=1e-5 , relax=("Static", 1.0)) -> None:
        super().__init__(globalModel, mesoModel, tolerance, relax)
        self.gm = globalModel
        self.mm = mesoModel

        self.stepName = abaqusData["stepName"]
        self.jobName = abaqusData["jobName"]
        self.modelName = abaqusData["modelName"]
        self.instanceName = abaqusData["instanceName"]
        self.IGLnodesSetName = abaqusData["IGLnodesSetName"]
        self.cpus = abaqusData["nCPUs"]

    def copyAbaqusScripts(self):
        shutil.copy("Abaqus_getDisplacements.py", self.tempFolder)
        shutil.copy("Abaqus_getElementNodalForces.py", self.tempFolder)
        shutil.copy("Abaqus_run.py", self.tempFolder)
        shutil.copy("Abaqus_setForces.py", self.tempFolder)
        shutil.copy("Abaqus_setDisplacements.py", self.tempFolder)
    
    def copyXSD(self):
        shutil.copy(self.insaneDir + "\\insane.xsd", self.tempFolder)
    
    def prepareFiles(self):
        self.copyXSD()
        self.copyAbaqusScripts()

        gM_path_input = self.inputFolder + "\\Global Model.cae" 
        shutil.copyfile(self.gm.modelPath, gM_path_input)

        mM_path_input = self.inputFolder + "\\Meso Model.xml"
        shutil.copyfile(self.mm.modelPath, mM_path_input)
        
        if self.mm.isGFEMgl():
            lM_path_input = self.inputFolder + "\\Local Model.xml"
            shutil.copyfile(self.lmPath, lM_path_input)

        gmPath_temp = self.iwd + "\\" + self.tempFolder + "Global Model.cae" 
        shutil.copyfile(self.gm.modelPath, gmPath_temp)
        self.gm.modelPath = gmPath_temp
        
        mmPath_temp = self.iwd + "\\" + self.tempFolder + "Local Model.xml"
        shutil.copyfile(self.mm.modelPath, mmPath_temp)
        self.mm.modelPath = mmPath_temp
        
        if self.mm.isGFEMgl():
            self.lmPath_temp = self.iwd + "\\" + self.tempFolder + "\\Local Model-1.xml"
            shutil.copyfile(self.lmPath, self.lmPath_temp)
        
    def saveFiles(self, final=False) -> None:
        if final:
            folder = f"{self.outputFolder}\\Final\\"
        else:
            folder = f"{self.outputFolder}\\Iteration {self.n:003d}\\"
            
        os.chdir(self.iwd)
        os.mkdir(folder)

        shutil.copyfile(self.gm.modelPath,  f"{folder}\\Global model.cae")
        shutil.copyfile(self.lmPath_temp,  f"{folder}\\Local model.xml")
        shutil.copyfile(self.gm.getResults(self.jobName),  f"{folder}\\Global results.odb")
        shutil.copyfile(self.mm.getResults(),  f"{folder}\\Local Results-LOAD_COMBINATION-001.xml")
    
    def solveGlobalModel(self) -> list:
        os.chdir(os.getcwd() + f"\\{self.tempFolder}")
        print("Running Abaqus (Global scale)...", end=" ")
        self.gm.run(stepName=self.stepName, 
                    jobName=self.jobName, 
                    cpus= self.cpus)
        print("OK!")
        return self.gm.getDisp(self.jobName, self.stepName, nodeSet=[])
       
    def sendToLocal(self, u:dict) -> None:
        u_local = {}
        for node in self.gin:
            position = self.gin.index(node)
            linNode = self.lin[position]
            u_local[linNode] = u[node]
        self.mm.setPreDisp(u_local)
    
    def solveLocalModel(self) -> None:
        print("Running INSANE (Meso scale)...", end=" ")
        self.mm.run(self.insaneDir)
        print("OK!")

    def getLocalReaction(self) -> dict:
        return self.mm.getReactions(self.lin)

    def sendToGlobal(self, f: dict, final=False) -> None:
        shutil.copyfile(self.iwd + "\\" + self.inputFolder + "Global Model.cae", self.gm.modelPath)
        if final:
            suppress = False
        else:
            self.updateResidualForcesAcc(f)
            suppress = True
        self.gm.setForces(self.stepName, self.modelName, self.IGLnodesSetName, self.instanceName, f, suppress)

    def getGlobalReaction(self, u:dict, suppress=True) -> dict:
        # self.gm.setDisp(self.stepName, self.modelName, self.instanceName, u, suppress)
        # self.gm.run(stepName=self.stepName, 
        #             jobName=self.jobName, 
        #             cpus= self.cpus)
        nodal_forces_path = self.iwd + "\\" + self.tempFolder + "forcesAbaqus.txt" 
        return self.gm.getElemForces(nodal_forces_path, self.gie, self.gin) 
    
    def finalSolution(self, u:dict) -> None:
        self.printFinalMsg()
        shutil.copy(self.inputFolder + "\\Global Model.cae", self.gm.modelPath)
        self.gm.setDisp(self.stepName, self.modelName, self.instanceName, u)
        self.solveGlobalModel()
        self.saveFiles(final=True)
        txt = " D O N E "
        print(f"{txt:{'='}^{60}}")
        # TODO completar com código para construir uma solução unificada MODELO GLOBAL + MESO + LOCAL 
