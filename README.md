# CoSMID: Corpus of Symbolic Music for Information Dynamics

CoSMID is a meta-corpus of symbolic music curated to capture a wide range of information-dynamic behaviors across diverse genres and styles,
enabling more comprehensive modelling of musical information dynamics.

## Dependencies

- Python 3
- R

R packages:
- data.table
- dplyr
- stringr
- [humdrumR](https://github.com/Computational-Cognitive-Musicology-Lab/humdrumR/tree/Development)
    - install humdrumR from source by checking out the Development branch
- [ppm](https://github.com/pmcharrison/ppm/tree/master)

*Documentation In Progress*

## Setup

In an R environment, define a `project_dir` variable with the root path of the repository.
Then, run the `setwd(project_dir)` expressions in main.R

## Repository Structure

data_raw/
    raw data
data_clean/
    cleaned data (valid kern/humdrum files)
scripts/
    any cleaning data scripts
err/
    validation reporting outputs from humdrumR

## Adding a Corpus

1. add raw data to `data_raw/<corpus_name>/`
2. implement a clean data function that converts to valid kern/humdrum files in `data_clean/<corpus_name>/`
3. implement a generate data function that takes a humdrumR corpus object and creates a field in it with the desired data for each piece
4. implement a generate observations function that reads a humdrumR piece and returns a vector of observations, reading the field generated in the prior step
