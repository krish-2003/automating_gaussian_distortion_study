import numpy as np
import os

pi = np.pi
h = 4.1357e-15
    
def check_file_exists(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Error: File '{file_path}' not found.")
    if os.stat(file_path).st_size == 0:
        raise ValueError(f"Error: File '{file_path}' is empty.")
     

def cmiev(E):
    return E / 8065.54
    
def get_singlet_energies(singlet_file):

    check_file_exists(singlet_file) # checking file exists or not at given path
    
    with open(singlet_file,'r') as file:
        lines = file.readlines()

        singlet_count = 0 #Ground state included
        singlet_energies = {} # in eV
        
        for line in lines:
            line = line.strip().split()
        
            if "Excited" in line and "State" in line and "eV" in line:
                if (line[3].split('-')[0] == "Singlet"):
                    singlet_count+=1
                    sing_state = "S" + str(singlet_count)
                    sing_energy = float(line[4])
                    singlet_energies[sing_state] = sing_energy
                
    return singlet_energies
    
def get_triplet_energies(triplet_file):

    check_file_exists(triplet_file) # checking file exists or not at given path
    
    with open(triplet_file,'r') as file:
        lines = file.readlines()

        triplet_count = 0 #Ground state included
        triplet_energies = {} # in eV
        
        for line in lines:
            line = line.strip().split()
        
            if "Excited" in line and "State" in line and "eV" in line:
                if (line[3].split('-')[0] == "Triplet"):
                    triplet_count+=1
                    trip_state = "T" + str(triplet_count)
                    trip_energy = float(line[4])
                    triplet_energies[trip_state] = trip_energy
                
    return triplet_energies
 
def get_soc(soc_file):
    
    check_file_exists(soc_file) # checking file exists or not at given path
    
    soc = {} # in cm-1 
    with open(soc_file,'r') as file:
        lines = file.readlines()
    
        for line in lines:
            soc_val = line.split(":")[1].strip().split()[0]
            soc_val = cmiev(float(soc_val)) #in eV
            
            parts = line.split("<")[1].split(">")[0]
            states = parts.split('|')
            singlet_state = states[0] 
            triplet_state = states[2].split(",")[0] 
    
            soc[singlet_state,triplet_state] = soc_val 
    return soc
 
def get_delta_energy(soc,singlet_energies,triplet_energies):
    
    delta_energy = {}
    
    for (singlet_state, triplet_state), soc_val in soc.items():
        if singlet_state == 'S*':
            singlet_state = 'S10'
        if triplet_state == 'T*':
            triplet_state = 'T10'
            
        if (singlet_state in singlet_energies or singlet_state == 'S0') and triplet_state in triplet_energies:
            sing_energy = 0.0 if singlet_state == 'S0' else float(singlet_energies[singlet_state])
            trip_energy = float(triplet_energies[triplet_state])
            
            delta_energy[(singlet_state, triplet_state)] = round(np.abs(sing_energy - trip_energy), 4) # in eV
    
    return delta_energy

def rho_fc(delta_energy, L, kbT):
    return (1 / np.sqrt(4 * np.pi * L * kbT)) * np.exp(-((delta_energy + L) ** 2) / (4 * L * kbT))
 
def k_isc(singlet_file,triplet_file, soc_file,T=300, L = 0.2):
    
    kbT = 8.62e-05 * T 
    k_isc = {}
    
    singlet_energies = get_singlet_energies(singlet_file)
    triplet_energies = get_triplet_energies(triplet_file)
    soc = get_soc(soc_file)
    delta_energy = get_delta_energy(soc,singlet_energies,triplet_energies)
    
    for (singlet_state, triplet_state), soc_val in soc.items():
        if singlet_state == 'S*':
            singlet_state = 'S10'
        if triplet_state == 'T*':
            triplet_state = 'T10'
            
        del_e = delta_energy.get((singlet_state, triplet_state), None)
        if del_e is None:
            print(f"Skipping {(singlet_state, triplet_state)} due to missing delta energy.")
            continue
        #print(rho_fc(del_e, L, kbT))
        k = 4 * (pi**2)*(1/h)* rho_fc(del_e, L, kbT) * (soc_val ** 2)
        k_isc[(singlet_state, triplet_state)] = k
    return k_isc
 

  
def write_section(outfile, title, data, key_width=6, value_width=10):
    outfile.write("-" * 50)
    outfile.write(f"\n{title}:\n")
    outfile.write("-" * 50)
    
    for key, value in data.items():
        if isinstance(key, tuple):  # Handle (s, t) transitions
            outfile.write(f"\n{key[0]:<{key_width}} → {key[1]:<{key_width}} : {value:>{value_width}.3e}")
        else:  # Handle single states
            outfile.write(f"\n{key:<{key_width}} : {value:>{value_width}.3e}")
    
    outfile.write("\n\n")
      
def main():

    soc_file = r"soc_out.dat"
    singlet_file = r"/home/krushnashete/semester_8/Minor/sosos_opt/ososo_singlet_b3lyp_631.log"
    triplet_file = r"/home/krushnashete/semester_8/Minor/sosos_opt/ososo_triplet_b3lyp_631.log"

    singlet_energies = get_singlet_energies(singlet_file)
    triplet_energies = get_triplet_energies(triplet_file)
    soc = get_soc(soc_file)
    delta_energy = get_delta_energy(soc,singlet_energies,triplet_energies)
    
    k_isc_val = k_isc(singlet_file,triplet_file, soc_file, L=0.2, T=300)
    
    with open("results.out", "w") as outfile:
        write_section(outfile, "Singlet Energies", singlet_energies)
        write_section(outfile, "Triplet Energies", triplet_energies)
        write_section(outfile, "Delta Energies", delta_energy)
        write_section(outfile, "SOC Values", soc)
        write_section(outfile, "Intersystem Crossing Rate Constants (k_isc)", k_isc_val)
    	
    print("Results are saved in the file 'results.out'!!")

if __name__ == "__main__":
    main()


