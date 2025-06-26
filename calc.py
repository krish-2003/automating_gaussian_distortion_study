import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import re
import shutil

def extract_opt_geometry(log_file):
    
    atomic_symbols = {
        1: 'H',  6: 'C', 7: 'N', 8: 'O', 9: 'F', 15: 'P', 16: 'S', 17: 'Cl'
    }
    
    with open(log_file, 'r') as file:
        lines = file.readlines()
    
    # find all occurrences of "Standard orientation"
    std_orient_indices = [i for i, line in enumerate(lines) if "Standard orientation" in line]
    
    if not std_orient_indices:
        raise ValueError("No 'Standard orientation' found in a log file.")
    
    last_index = std_orient_indices[-1]  # Take the last std orientation
    start = last_index + 5  # Skip 5 lines after "Standard orientation:"
    
    geometry = []
    
    for line in lines[start:]:
        if "-----" in line:  # End of orientation block
            break
        parts = line.split()
        if len(parts) >= 6:
            atomic_num = int(parts[1])
            x, y, z = parts[3], parts[4], parts[5]
            element = atomic_symbols.get(atomic_num, str(atomic_num))  # Converting atomic number to element symbol
            geometry.append(f"{element}  {x}  {y}  {z}")
    
    return geometry

def generate_energy_com_file(opt_freq_com_file, energy_com_file, geometry):
    
    com_content = f"""%nprocshared=3
%mem=2GB
%chk={energy_com_file}.chk
# td=(50-50,nstates=10) b3lyp/6-31g(d) geom=connectivity

{energy_com_file}

0 1
"""
    with open(opt_freq_com_file, 'r') as file:
        lines = file.readlines()

    # flags for coordinates section starts and ends
    start_index = None
    end_index = None

    for i, line in enumerate(lines):
        if start_index is None and len(line.strip().split()) == 4:  
            start_index = i
        elif start_index is not None and line.strip() == "":  
            end_index = i
            break

    if start_index is None or end_index is None:
        raise ValueError("Could not find coordinate block in the input .com file.")

    # Extract additional numbers after the coordinates
    additional_data = lines[end_index + 1 :]

    # Formating the new coordinates properly
    formatted_coords = "\n".join(
        f" {atom:<2} {x:>24} {y:>11} {z:>11}" for atom, x, y, z in 
        (coord.split() for coord in geometry)
    )

    # Write new .com file
    with open(f"{energy_com_file}.com", 'w') as file:
        file.writelines(com_content)  
        file.write(formatted_coords + "\n\n")  # Add optimized geometry + empty line
        file.writelines(additional_data)  # Append the remaining lines after geometry
    print(".com file for energy is completed")

def soc_calculation(opt_freq_com_file, geometry,init_path):
    soc_file = opt_freq_com_file.replace('.com', '_soc')

    soc_initial = f"""%rwf=gaussian.rwf
%nprocshared=3
%mem=2GB
%chk=gaussian.chk
# td=(50-50,nstates=10) b3lyp/6-31g(d) nosymm geom=connectivity gfinput
10f 6d

{soc_file}

0 1
"""
    with open(opt_freq_com_file, 'r') as file:
        lines = file.readlines()

    # flags for coordinates section starts and ends
    start_index = None
    end_index = None

    for i, line in enumerate(lines):
        if start_index is None and len(line.strip().split()) == 4:  
            start_index = i
        elif start_index is not None and line.strip() == "":  
            end_index = i
            break

    if start_index is None or end_index is None:
        raise ValueError("Could not find coordinate block in the input .com file.")

    # Extract additional numbers after the coordinates
    additional_data = lines[end_index + 1 :]

    # Formating the new coordinates properly
    formatted_coords = "\n".join(
        f" {atom:<2} {x:>24} {y:>11} {z:>11}" for atom, x, y, z in 
        (coord.split() for coord in geometry)
    )
    
    soc_folder = f"../{soc_file}"

    # Create nested directories
    try:
        os.makedirs(soc_folder)
        print(f"{soc_folder} created successfully.")
    except FileExistsError:
        print(f"One or more directories in '{soc_folder}' already exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    
    # Write new .com file
    with open(os.path.join(soc_folder, "gaussian.com"), 'w') as file:
        file.writelines(soc_initial)  
        file.write(formatted_coords + "\n\n")  # Add optimized geometry + empty line
        file.writelines(additional_data)  # Append the remaining lines after geometry
    
    print(f"gaussian.com file is written in {soc_folder} ")

    init_py_path = init_path
    shutil.copy(init_py_path, soc_folder)
    print(f"Copied init.py to {soc_folder}")

    return soc_folder

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
    

def run_pysoc(com_file):
    work_dir = os.path.dirname(com_file)
    command = f"pysoc.py"
    try:
        subprocess.run(command, shell=True, check=True, cwd=work_dir)
        print("pysoc.py executed successfully in SOC folder.")
    except subprocess.CalledProcessError as e:
        print(f"Error running pysoc.py: {e}")
        return False
    return True
    
def main(input_com_file,init_path):
    # Run opt+freq calculations
    
    print(f"Running Gaussian for {input_com_file} (Opt+Freq)...")
    run_gaussian(input_com_file)
    
    # Extract optimized geometry from the .log file
    log_file = input_com_file.replace('.com', '.log')
    print(f"\nExtracting optimized geometry from {log_file}...")
    optimized_geometry = extract_opt_geometry(log_file)
    
    # Generating .com files for energy calculations
    energy_file = input_com_file.replace('.com', '_st-energy')
    generate_energy_com_file(input_com_file, energy_file, optimized_geometry)
    
    # Assuming soc_calculation is a function that handles the spin-orbit coupling
    soc_folder = soc_calculation(input_com_file, optimized_geometry,init_path)
    
    # Run the energy calculations
    print("\nRunning Gaussian for energy calculation...")
    run_gaussian(f"{energy_file}.com")
    
    print("\nRunning Gaussian for soc ...")
    run_gaussian(f"{soc_folder}/gaussian.com")
    
    print("\nRunning Pysoc for soc calculation...")
    run_pysoc(f"{soc_folder}/gaussian.com")
    
    print("\n\n\n*********************************************************")
    print("All calculations are done !!")
    print("\n*********************************************************")

if __name__ == "__main__":
    input_com_file = "sooos_opt+freq_b3lyp_631.com"  # Replace with your actual .com file
    init_path = "/home/krushnashete/semester_8/Minor/soc-trial/init.py"
    main(input_com_file,init_path)

