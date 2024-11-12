#Write me a python file that will read my code files I specify and write to a local text file all the code with the filename identified

import os
# Specify the directory containing the code files
directory = 'D:/projects/auto-resume-updates/'

files = [
     'backend/ResumeUpdateProcessor.py',
     'backend/cosmosdb.py',
     'backend/testing.py',
     'frontend/src/components/ResumeReview.js',


]

# Specify the output file path
output_file = 'D:/temp/tmp_codebase/codebase.txt'

# Open the output file in write mode
with open(output_file, 'w') as f:
    # Iterate over all files in the directory
    for filename in files:
        # Open the file in read mode
        with open(os.path.join(directory, filename), 'r') as code_file:
            # Write the filename to the output file
            f.write(f"<File: {filename}>\n")
            # Write the code from the file to the output file
            f.write(code_file.read())
            # Add a separator between files
            f.write('\n' + '-'*80 + '\n')