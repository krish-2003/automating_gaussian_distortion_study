## automating_gaussian_distortion_study

These codes are useful to reduce the manual work while using the Gaussian software. 
kisc.py and kisc_calc.py are used to calculate the kisc rate from the singlet-triplet energies and the SOC value. 
kisc.py is for individual transitions, while kisc_calc.py calculates the rate for all transitions.
calc.py does sequential calculations for Opt+Freq, Vertical Excitation Energy, binary file, and finally PySOC for SOC values.

For studying the SOC value dependence on distorting the normal modes of the molecule, distort.py can be used. This uses the distort.f90 file to distort all the normal modes of the molecules by some value, and then does the sequential calculations for all possible distorted geometries and provides the output plots where we can compare how the SOC value is varying with distortions of normal modes.
