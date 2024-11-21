#Script to extract the codebase of a project and save it to a text file
import os
# Specify the directory containing the code files
directory = 'D:/projects/auto-resume-builder/'

files = [
    'backend/ResumeUpdateProcessor.py',
    #'backend/cosmosdb.py',
    'backend/testing.py',
    'backend/app.py',
    'backend/recurring_notifications.py',
    'frontend/src/components/ResumeReview/EmptyScreen.js',
    'frontend/src/components/ResumeReview/ErrorScreen.js',
    'frontend/src/components/ResumeReview/LoadingScreen.js',
    'frontend/src/components/ResumeReview/ReviewScreen.js',
    'frontend/src/components/ResumeReview/ReviewChecklist.js',
    'frontend/src/components/ResumeReview/SuccessScreen.js',
    'frontend/src/components/ResumeReview/api.js',
    'frontend/src/components/ResumeReview/index.js',
    'frontend/src/components/ResumeReview/ProjectCard.js',
    'frontend/src/App.js',
    'frontend/src/components/ResumeReview/Header.js'
    'frontend/src/components/ResumeReview/FeedbackFeature.js',


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