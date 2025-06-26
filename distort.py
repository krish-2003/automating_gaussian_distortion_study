# Developed By Krushna Shete
# The active modes list can be provided at the end of the file.

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import subprocess
import re
import glob
import shutil
from collections import defaultdict

plt.rcParams['font.family'] = 'serif'

def run_gaussian(com_file):
    
    command = f"g16 {com_file}"
    work_dir = os.path.dirname(com_file) or os.getcwd()
    
    try:
        subprocess.run(command, shell=True, check=True, cwd=work_dir)
        print(f"Gaussian job for {com_file} completed.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running Gaussian job: {e}")
        return False
        
    return True
    
def run_distort(distort_file,inp_file):

    if not os.path.isfile(distort_file):
        print(f"Error: File '{distort_file}' not found.")
        return False

    work_dir = os.path.dirname(distort_file) or os.getcwd()
    output_exe = os.path.join(work_dir, "distort")

    compile_cmd = f"gfortran {distort_file} -o {output_exe}"
    run_cmd = f"{output_exe} < {inp_file}"

    try:
        subprocess.run(compile_cmd, shell=True, check=True, cwd=work_dir)
        subprocess.run(run_cmd, shell=True, check=True, cwd=work_dir)
        print("Distortion process completed successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running distortion process: {e}")
        return False
       
def run_pysoc(com_file):

    work_dir = os.path.dirname(com_file)
    command = f"pysoc.py"
    
    try:
        subprocess.run(command, shell=True, check=True, cwd=work_dir,stdout=subprocess.DEVNULL)
        print("pysoc.py executed successfully in SOC folder.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pysoc.py: {e}")
        return False
        
    return True

def check_gaussian_log(log_file):
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    if lines:
        last_line = lines[-1]
    else:
        last_line = ""
    terminated = "Normal termination of Gaussian" in last_line
    
    if terminated:
        print("Calculation terminated normally")
    
    else:
        raise RuntimeError(f"Error: Normal termination not found in the last line of the log file {log_file}.")

def mv_file(direct,pattern,destn,recreate=True):

    mv_list = glob.glob(os.path.join(direct, pattern))
    wor_dir = direct
    destination_folder = os.path.join(wor_dir, destn)
    
    if recreate and os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
  
    os.makedirs(destination_folder, exist_ok=True)
    
    for file in mv_list :
        try:
            shutil.move(file, destination_folder)
            print(f"Moved {file} to {destination_folder}")
            
        except Exception as e:
            print(f"Error moving {file}: {e}")

    return True

def extrac_geom(log_file):

    with open(log_file, 'r') as file:
        lines = file.readlines()
        distort_geom = {}
    
        # Find indices for lines with distortion info and standard orientation
        normal_mode_indices = [i for i, line in enumerate(lines) if "Distortion along normal mode" in line]
        
        std_orient_indices = [i for i, line in enumerate(lines) if "Standard orientation" in line]
        
        if not normal_mode_indices:
            raise ValueError("No 'Distortion along normal modes' found in the log file.")
            
        if not std_orient_indices:
            raise ValueError("No 'Standard orientation' found in the log file.")
    
        for mode_index in normal_mode_indices:
            mode_line = lines[mode_index]
            match = re.search(r"normal mode N (\d+) by ([+-])\s*([\d.]+)", mode_line)
            if match:
                mode_num = match.group(1)
                sign = match.group(2)
                distortion_value = match.group(3)
                key = f"{mode_num}_{sign}{distortion_value}"
            else:
                continue  
            
            std_index = next(i for i in std_orient_indices if i > mode_index)
            coord_start = std_index + 5
            
            # Find the end of the coordinate table: stop at an empty line or a line with dashes
            coord_end = coord_start
            while coord_end < len(lines) and lines[coord_end].strip() and "-----" not in lines[coord_end]:
                coord_end += 1
            
            # Extract coordinate lines and parse them.
            coords = lines[coord_start:coord_end]
            parsed_coords = []
            
            for line in coords:
                parts = line.split()
                if len(parts) >= 6 and parts[0].isdigit():
                    # Center, Atomic Number, Type, X, Y, Z
                    center = int(parts[0])
                    atomic_num = int(parts[1])
                    atomic_type = int(parts[2])
                    x, y, z = map(float, parts[3:6])
                    
                    parsed_coords.append((atomic_num,x, y, z))
            
            # Store the parsed coordinates in the dictionary.
            distort_geom[key] = parsed_coords
            
    return distort_geom
   
def generate_energy_com_file(direct,energy_com_file, geometry,state,method_basis,memory,cores):

    atomic_symbols = {
        1: 'H',  6: 'C', 7: 'N', 8: 'O', 9: 'F', 15: 'P', 16: 'S', 17: 'Cl'
    }
    com_content = f"""%nprocshared={cores}
%mem={memory}GB
%chk={energy_com_file}.chk
# td=({state},nstates=10) {method_basis} 

{energy_com_file}

0 1
"""
    # Formating the new coordinates properly
    formatted_coords = "\n".join(
        f" {(atomic_symbols.get(A, str(A))):<2} {x:>24.5f} {y:>11.5f} {z:>11.5f}" 
        for i, (A, x, y, z) in enumerate(geometry)
    )
    
    # Write new .com file
    with open(os.path.join(direct,f"{energy_com_file}.com"), 'w') as file:
        file.writelines(com_content)  
        file.write(formatted_coords + "\n\n")  # Add optimized geometry + empty line
    print(f".com file for energy{state} is completed")
    return 0
    
    
def generate_soc(direct,file,geometry,method_basis,init_path,memory,cores):

    atomic_symbols = {
        1: 'H',  6: 'C', 7: 'N', 8: 'O', 9: 'F', 15: 'P', 16: 'S', 17: 'Cl'
    }
    
    soc_dir = os.path.join(direct, file)
    os.makedirs(soc_dir,exist_ok=True)
    soc_file = file+'_soc'
    soc_initial = f"""%rwf=gaussian.rwf
%nprocshared={cores}
%mem={memory}GB
%chk=gaussian.chk
# td=(50-50,nstates=10) {method_basis} nosymm gfinput 
10f 6d

{soc_file}

0 1
"""
    formatted_coords = "\n".join(
        f" {(atomic_symbols.get(A, str(A))):<2} {x:>24.5f} {y:>11.5f} {z:>11.5f}" 
        for i, (A, x, y, z) in enumerate(geometry)
    )
    
    with open(os.path.join(soc_dir,'gaussian.com'),'w') as file:
        file.writelines(soc_initial)
        file.write(formatted_coords + "\n\n")
        
    print(f"gaussian.com file is written in {soc_dir}")
    shutil.copy(init_path, soc_dir)
    
    print(f"Copied init.py to {soc_dir}")
    return soc_dir

def generate_distort_mode(direct, dist_file, mode):

	with open(dist_file, 'r') as file:
		lines = file.readlines()

	base = os.path.splitext(os.path.basename(dist_file))[0]
	blocks = []
	start = None

	pattern = re.compile(rf"Distortion along normal mode N\s+{mode}\b")
	
	for i, line in enumerate(lines):

		if pattern.search(line):

			start = i - 4  # Assumes 4 lines before header
		elif "--Link1--" in line and start is not None:

			end = i - 1

			blocks.append(lines[start:end])
			start = None  # reset for next block

    # Handle case where file ends without final --Link1--
	if start is not None:
		blocks.append(lines[start:])

    # Write each block to a separate file
	files = []
	for idx, block in enumerate(blocks):
		distortion_line = next((line for line in block if "Distortion along normal mode" in line), "")
		sign = "+" if "+" in distortion_line else "-"

		outfile = f"{base}_{mode}_{sign}.com"
		with open(os.path.join(direct, outfile), 'w') as f:
			f.writelines(block)
		print(f"Generated: {outfile}")
		files.append(outfile)

	return files


def check_file_exists(file_path):

    if os.path.isfile(file_path):
        return True
    else:
    	return False
        
def get_soc(ref_soc_file):
    
    check_file_exists(ref_soc_file) # checking file exists or not at given path
    
    soc = {} # in cm-1 
    with open(ref_soc_file,'r') as file:
        lines = file.readlines()
    
        for line in lines:
            soc_val = line.split(":")[1].strip().split()[0]
            soc_val = float(soc_val)
            
            parts = line.split("<")[1].split(">")[0]
            states = parts.split('|')
            singlet_state = states[0] 
            triplet_state = states[2].split(",")[0] 
    
            soc[singlet_state,triplet_state] = soc_val 
    return soc
    
def get_top_transitions(ref_soc_file, top_n=5):

    """
    return the top_n transitions (state pairs) with highest SOC values.
    """
    soc_dict = get_soc(ref_soc_file)
    # Sort transitions by SOC value (descending) and pick the top ones
    sorted_transitions = sorted(soc_dict.items(), key=lambda x: x[1], reverse=True)
    top_transitions = [trans for trans, val in sorted_transitions[:top_n]]
    return top_transitions
    
def get_transitions(soc_file):
    soc_dict = get_soc(soc_file)
    transitions = []
    singlets = ['S1','S2','S3','S4','S5','S6']
    for key,value in soc_dict.items():
        if key[0] in singlets:
            if key[1] =='T*':
                key = (key[0], 'T10')
                transitions.append(key)
            else:
                transitions.append(key)
    return transitions
    
def parse_distortion_amplitude(folder_name):
    """
    Extracts the distortion amplitude from the folder name.
    """
    try:
        amp_str = folder_name.split('_')[-1]  # e.g. "1+" or "0.5-"
        if amp_str.endswith('+'):
            amp = float(amp_str[:-1])
        elif amp_str.endswith('-'):
            amp = -float(amp_str[:-1])
        else:
            amp = float(amp_str)
            
    except Exception as e:
        print(f"Could not parse distortion amplitude from folder '{folder_name}': {e}")
        amp = 0.0
    return amp
 
 
def plot_soc_vs_distortion(folder, normal_modes, get_soc, parse_distortion_amplitude):
    """
    For each mode in 'folder', create 6 plots (one for each singlet state S1 to S6) and similarly for triplets.
    Each plot shows SOC vs. distortion amplitude for transitions starting from that singlet.
    """
    singlets = ['S1','S2','S3','S4','S5','S6']
    wor_dir = os.path.basename(folder)
    
    # Loop over each mode.
    for m in  normal_modes:
        # Find all folders corresponding to the current mode
        soc_folders = glob.glob(os.path.join(folder, f'*soc_dis_{m}_*'))
        
        # Data structure: for each state, store a dictionary mapping
        # each transition (tuple) to a list of (distortion amplitude, SOC value) pairs.
        data = {s: defaultdict(list) for s in singlets}

        for fold in soc_folders:
            # Extract the distortion amplitude from the folder name
            amp = parse_distortion_amplitude(os.path.basename(fold))
            dat_file = os.path.join(fold, 'soc_out.dat')
            
            # Read the SOC dictionary from the file
            soc = get_soc(dat_file)
            for key, value in soc.items():
                # Only consider transitions where the singlet is in our list
                if key[0] in singlets:
                    # Adjust the triplet state if necessary (replace 'T*' with 'T10')
                    if key[1] == 'T*':
                        key = (key[0], 'T10')
                    # Append the amplitude and SOC value under the appropriate singlet's data
                    data[key[0]][key].append((amp, value))
        
        # Now, for each singlet state, create a separate plot.
        for singlet in singlets:
            transitions = data[singlet]
            if not transitions:
                # If no transitions for this singlet in the current mode, skip plotting.
                continue
            
            plt.figure(figsize=(8, 5))
            # Create a colormap with enough distinct colors for the transitions
            #colors = plt.colormaps.get_cmap("tab10")(np.linspace(0, 1, len(transitions)))
            colors = plt.get_cmap("tab10")(np.linspace(0, 1, len(transitions)))

            # Plot each transition's data
            for idx, (trans, points) in enumerate(sorted(transitions.items())):
                # Sort the points by amplitude so the line plot is smooth
                points = sorted(points, key=lambda x: x[0])
                x_vals = [p[0] for p in points]
                y_vals = [p[1] for p in points]
                plt.plot(x_vals, y_vals, marker='o', linestyle='--', color=colors[idx],label = rf"$\langle \mathrm{{{trans[0]}}}|\hat{{\mathrm{{H}}}}|\mathrm{{{trans[1]}}} \rangle$")
            
            # Format the plot
            plt.xlabel("Distortion Amplitude",fontsize=20)
            plt.ylabel("SOC Value (cm⁻¹)",fontsize=20)
            plt.xticks(fontsize=16)
            plt.yticks(fontsize=16)

            #plt.title(f"SOC vs Distortion for {singlet} in Mode {m} ({wor_dir})")
            
            plt.legend(title = f'Mode {m}',title_fontsize=16,bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=14)
            plt.tight_layout()
            
            # Save and display the plot
            out_filename = os.path.join(folder, f"soc_vs_disto_mode{m}_{singlet}_{wor_dir}.svg")
            plt.savefig(out_filename)
            #plt.show()
            plt.close() 


def main(distort_file,inp_sing_file,normal_modes,method_basis,init_path,memory,cores):

	run_distort(distort_file,inp_sing_file)
	
	#mv_file(cwd,'*dist_sing*','singlets',recreate=False)
	
	sing_folder = os.path.join(cwd,'singlets')
	os.makedirs(sing_folder, exist_ok=True)
	sing_list = glob.glob(os.path.join(cwd,'*dist_sing*'))
	print("sing_list",sing_list) #debugging
	for idx,file in enumerate (sing_list,start=1):
		print("file",file)
		for mode in normal_modes:
			print("mode",mode)
			files = generate_distort_mode(sing_folder,file,mode)
			print(files)
			for dist_file in files:
				print("dist_file",dist_file)
				file_log = os.path.join(sing_folder,dist_file).replace('.com','.log')
				
				if (check_file_exists(file_log)):
					check_gaussian_log(file_log)
					
				else:
					run_gaussian(os.path.join(sing_folder,dist_file))
					check_gaussian_log(file_log)
				
				print("Geometry Extraction")
				distort_geom = extrac_geom(os.path.join(sing_folder,file_log))

				key, value = next(iter(distort_geom.items()))
				generate_energy_com_file(sing_folder,f"energy_dis_{key}",value,'singlets',method_basis,memory,cores)
				ergy_file = f'energy_dis_{key}.com'
				mode = key.split('_')[-2]
				dist_val = key.split('_')[-1]
				
				vee_folder = os.path.join(sing_folder, f'VEE{key.split("_")[-1]}')
				os.makedirs(vee_folder, exist_ok=True)
				log_file = os.path.join(vee_folder,ergy_file).replace('.com','.log')
				
				if (check_file_exists(log_file)):
					check_gaussian_log(log_file)					
				else:
					print(f"\n{log_file} doesnt exists")
					run_gaussian(os.path.join(sing_folder,ergy_file))
					mv_file(sing_folder,f'*energy_dis_{key}*',f'VEE{dist_val}',recreate=False)
					check_gaussian_log(log_file)
					
				generate_soc(sing_folder,f"soc_dis_{key}",value,method_basis,init_path,memory,cores)
					
				log_file = os.path.join(sing_folder, f"soc_dis_{key}", "gaussian.com").replace('.com','.log')
				if (check_file_exists(log_file)):
					
					check_gaussian_log(log_file)
						
				else:
						
					run_gaussian(os.path.join(sing_folder, f"soc_dis_{key}", "gaussian.com"))
					check_gaussian_log(log_file)

				run_pysoc(os.path.join(sing_folder, f"soc_dis_{key}", "gaussian.com"))
				
	
	plot_soc_vs_distortion(sing_folder, normal_modes, get_soc, parse_distortion_amplitude)
	
	print("\n***********************************************************")
	print("Done !!!!!!!")

cwd = os.getcwd()

if __name__ == "__main__":

    distort_file = "distort.f90"
    
    #normal_modes = [75,83,84] # Enter all the active normal modes
    
    # if you want to study all the modes, comment out above line
    # and uncomment followinhg block,  -->
    #
    total_mode = 10
    normal_modes = np.arange(1,total_mode+1,1)
    #
    
    inp_sing_file = "inp_sing.txt"
    method_basis = "b3lyp/6-311++g" # Enter the level of theory and basis set
    init_path = "/home/apogean/sharan/init.py" # Add path of the init.py file from your system
    memory = 60 # Memory in GB
    cores = 25 # no of cores to use for gaussian 
    
    main(distort_file,inp_sing_file,normal_modes,method_basis,init_path,memory,cores)	
