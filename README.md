# gfemgl-gli

Main coupling code:
 - coupler.py: contains the coupler classe. A coupler between Abaqus and INSANE is implemented for demonstration.
 - model.py: contains the classes model, global and local. Global and local classes have been implemented for INSANE, and global class has been implemented for Abaqus.
 - toolbox.py: contains the linAlg and accelToolBox classses. linAlg is an auxiliary class. accelToolBox concerns acceleration tecniques. Static and dynamic acceleration have been implemented and tested. Quasi-Newton has been implemented but not tested.


The file 'InsaneByFile.jar' is a modified version of INSANE able to run analysis from prompt command. 'insane.xsd' is used by INSANE to validade xml files.

All the files starting with 'Abaqus_...' are used to integrate the code with Abaqus software. It is required an Abaqus instalation in order to these files work properly.

simulation1.py, simulation2.py and simulation3.py are examples of how the coupler can be used.

Finally, 'Model files' folder contains the models used for the validation of the code.
