import numpy as np
import os
import re
import glob
import subprocess

cwd = os.getcwd()
sing_folder = os.path.join(cwd,'singlets')

pattern = os.path.join(sing_folder,'*soc_dis*')
soc_folder_list = glob.glob(pattern)

def check_file(path, file_name):
    file_path = os.path.join(path,file_name)

    if os.path.isfile(file_path):
        return True
    print(f"{file_name} File is not there")    
    return False
   
files = ['gaussian.chk', 'gaussian.rwf']

for f in soc_folder_list:
	for file_name in files:
		file_path = os.path.join(f,file_name)
		print(file_path)
		
		if check_file(f,file_name):    
			subprocess.run(["sudo", "rm", file_path], check=True)
	
		else :
			continue
       

