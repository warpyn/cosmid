# CoSMID: Corpus of Symbolic Music for Information Dynamics

CoSMID is a meta-corpus of symbolic music curated to capture a wide range of information-dynamic behaviors across diverse genres and styles,
enabling more comprehensive modelling of musical information dynamics.
Through an accompanying python package named `cosmid`, this code repository can:

- read subcorpora of symbolic music (in kern/humdrum format) into a `pandas` dataframe in python
- generate harmony annotations (in roman numerals)
- compute information content and entropy of harmony annotations using an IDyOM-esque model design  
- save the pandas dataframe with all saved data to a parquet file

Note: This meta-corpus focuses on symbolic data annotations for **harmony**.
Other musical attributes are not officially supported, but future improvements include support for custom annotation processing. 

## Prerequisites

- [R](https://www.r-project.org/)
    - (install Development branch from source) [humdrumR](https://github.com/Computational-Cognitive-Musicology-Lab/humdrumR/tree/Development) 
    - [ppm](https://github.com/pmcharrison/ppm/tree/master)

CoSMID uses the `humdrumR` package to read kern/humdrum files and the `ppm` package to create the IDyOM-esque model for information theory computations.
The `cosmid` python package uses the `rpy2` package under the hood to interface with R packages through python code.

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

This repository uses `uv` to manage python project dependencies and the corresponding virtual environment.

## Usage

CoSMID consists of a set of supported subcorpora, whose data lives in this repository.
To see the list of supported subcorpora, see `cosmid.constants.supported_subcorpora`.

To generate a `pandas` dataframe with symbolic data from subcorpora and computed information theory data,
see the example code in `examples/generate_corpus_dataframe.py`.
Run the code using uv with the following command: `uv run examples/generate_corpus_dataframe.py`

## Symbolic Music Data for Subcorpora

The `cosmid` package reads subcorpora in kern/humdrum files; however, symbolic music is often not already in this format.
If a subcorpus in CoSMID is not originally formatted in kern/humdrum, the original raw data is located in `data_raw/<subcorpus_name>`,
and data converted to kern/humdrum (cleaned data) is located in `data_clean/<subcorpus_name>`.
For _supported subcorpora_, any data cleaning processes used are located in `cosmid/data_cleaning/`.
If a subcorpus is already in kern/humdrum, the raw data will be directly read. 
See the paths in `cosmid.constants.supported_subcorpora_paths` for the path to humdrum data for each subcorpus.
These are the exact paths given to the `humdrumR::readHumdrum` function.

To add a new _natively supported_ subcorpus within this repository:

1. Add raw data to `data_raw/<corpus_name>/`
2. Implement a module in `cosmid/data_cleaning/` that cleans the raw data to valid kern/humdrum files in `data_clean/<corpus_name>/`.
3. In `cosmid.core.write_subcorpus_harmony_viewpoint_observations`, implement a case to parse the humdrum files to generate harmony annotations
   in a new column of the pandas dataframe, where the column name is the value of `cosmid.constants.HARMONY_VIEWPOINT_LABEL`.
