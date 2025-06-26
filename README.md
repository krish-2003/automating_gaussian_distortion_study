# Automating Gaussian Distortion Study

This repository contains a few codes which will be useful while working with the Gaussical Software while studying the intersystem crossing rates and molecular distortion studies. These scripts help to reduce the manual work and time consumption.

## Scripts Overview

- **kisc.py**
  Calculates the intersystem crossing rate for a transition; it requires the user input of energies and the SOC value.

- **kisc_calc.py**
  This script needs the paths for the log files of singlet and triplet energies, and the path for the soc_out.dat file. It gives the output file     
  containing the intersystem crossing rates for all transitions.

- **calc.py**
  This script automates the full sequential calculations from
  - Optimization + Frequency(Opt+Freq)
  - Energy 

  
kisc.py and kisc_calc.py are used to calculate the kisc rate from the singlet-triplet energies and the SOC value. 
kisc.py is for individual transitions, while kisc_calc.py calculates the rate for all transitions.
calc.py does sequential calculations for Opt+Freq, Vertical Excitation Energy, binary file, and finally PySOC for SOC values.

For studying the SOC value dependence on distorting the normal modes of the molecule, distort.py can be used. This uses the distort.f90 file to distort all the normal modes of the molecules by some value, and then does the sequential calculations for all possible distorted geometries and provides the output plots where we can compare how the SOC value is varying with distortions of normal modes.
