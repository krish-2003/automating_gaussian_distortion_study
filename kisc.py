#Calculating the kisc

import numpy as np
import math 

pi = np.pi

def cmiev(E):
    #Converting Energy from cm-1 to eV
    return (E/8065.54)
    
def rho_fc(delta_E, L, kbT):
    return ((1/np.sqrt(4*pi*L*kbT))*np.exp(-((delta_E + L)**2)/(4*L*kbT))) 
     
E1 = float(input("Enter the Excited energy of Singlet state in ev: "))
E2 = float(input("Enter the Excited energy of Triplet state in ev: "))

socme = float(input("Enter the SOC matrix element in cm-1: "))

delta_E = (E1-E2)
print(f"Energy difference in states is: {delta_E:.4f}")
socme = cmiev(socme)

L = 0.2 # re-organization energy in eV
kB = 8.62e-05 #Boltzman constant in eV
T = 300 # in K
kbT = kB*T # in ev
h = 4.14e-15 #Plancks constant in eV

k = (4*(pi**2)/h)*rho_fc(delta_E,L,kbT)*(socme**2)

k = "{:.4e}".format(k)

print(f"K_isc : {k}")
