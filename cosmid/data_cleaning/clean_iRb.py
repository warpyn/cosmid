"""
Clean the data from the iRb jazz corpus.

Raw data is located in data_raw/iRb_v1-0/*.
This directory contains .jazz files along with various shell scripts and extra data files.
To my knowledge, the .jazz files on their own are valid kern/humdrum files (after deleting the extra line at the end of the file).
However, there is a jazzparser.sh script that preps the .jazz files by extracting various information into separate spines.

This python script will clean the raw data by running the raw .jazz files through the jazzparser.sh script
and save the output in the cleaned data subdirectory data_clean/iRb_v1-0/*.

Note: Currently there are still errors in 6 files. Look in the err/ directory for more information.
"""

import os
import shutil
import subprocess

from ..constants import PROJECT_ROOT

def main():

    RAW_DATA_IRB_DIR_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "data_raw/iRb_v1-0"))
    CLEAN_DATA_IRB_DIR_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "data_clean/iRb_v1-0"))
    assert os.path.isdir(RAW_DATA_IRB_DIR_PATH), RAW_DATA_IRB_DIR_PATH
    assert os.path.isdir(CLEAN_DATA_IRB_DIR_PATH), CLEAN_DATA_IRB_DIR_PATH
    JAZZPARSER_PATH = os.path.join(RAW_DATA_IRB_DIR_PATH, "jazzparser.sh")

    # get a list of filepaths to .jazz files
    jazz_filepaths = []
    for filename in os.listdir(RAW_DATA_IRB_DIR_PATH):
        if filename[-5:] == ".jazz":
            jazz_filepaths.append(os.path.join(RAW_DATA_IRB_DIR_PATH, filename))
    
    # run jazzparser.sh on each .jazz file
    for jazz_filepath in jazz_filepaths:
        subprocess.run(["bash", JAZZPARSER_PATH, jazz_filepath])

    # clean the parsed .jazz file
    for filename in os.listdir(os.path.join(RAW_DATA_IRB_DIR_PATH, "jazzparser_cache")):
        cached_prepped_jazz_filepath = os.path.join(RAW_DATA_IRB_DIR_PATH, "jazzparser_cache", filename)
        with open(cached_prepped_jazz_filepath, "r") as f:
            prepped_jazz_lines = f.readlines()
        with open(cached_prepped_jazz_filepath, "w") as f:
            # remove the last 2 lines
            cleaned_jazz_lines = prepped_jazz_lines[:-2]
            f.writelines(cleaned_jazz_lines)

    # create the clean data subdirectory if it doesn't already exist
    os.makedirs(CLEAN_DATA_IRB_DIR_PATH, exist_ok=True)

    # copy parsed .jazz files from the jazzcache subdirectory to the respective clean data subdirectory
    for filename in os.listdir(os.path.join(RAW_DATA_IRB_DIR_PATH, "jazzparser_cache")):
        cached_prepped_jazz_filepath = os.path.join(RAW_DATA_IRB_DIR_PATH, "jazzparser_cache", filename)
        clean_data_jazz_filepath = os.path.join(CLEAN_DATA_IRB_DIR_PATH, filename)
        shutil.copy2(cached_prepped_jazz_filepath, clean_data_jazz_filepath)

if __name__ == "__main__":
    main()
