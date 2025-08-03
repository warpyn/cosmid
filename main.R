library(humdrumR)
library(stringr)
library(ppm)
library(data.table)
library(dplyr)
library(ggplot2)
# assumes humdrum toolkit is installed and the cloned repository is in the home directory

main <- function() {
  
  setwd(project_dir)
  
  # to add a new corpus:
  # 1. add raw data to data_raw/<corpus_name>/
  # 2. implement a clean data function that converts to valid kern/humdrum files in data_clean/<corpus_name>/
  # 3. implement a generate data function that takes a humdrumR corpus object and creates a field in it with the desired data for each piece
  # 4. implement a generate observations function that reads a humdrumR piece and returns a vector of observations, reading the field generated in the prior step
  
  # iRb
  # irb_clean_data()
  validateHumdrum("data_clean/iRb_v1-0/*") # 162 errors in 6 files, omitting for now
  irb_corpus <- readHumdrum("data_clean/iRb_v1-0/*")
  irb_corpus <- irb_generate_harmony_data(irb_corpus)
  
  # cocopops
  # billboard_clean_data()
  # rollingstone_clean_data()
  billboard_corpus <- readHumdrum("data_clean/billboard/*") # 6 errors in 1 file, omitting for now
  rollingstone_corpus <- readHumdrum("data_clean/rollingstone/*") # 82 errors in 1 file, omitting for now
  billboard_corpus <- cocopops_generate_harmony_data(billboard_corpus)
  rollingstone_corpus <- cocopops_generate_harmony_data(rollingstone_corpus)
  
  
  irb_IT_table <- generate_IT_table(irb_corpus, irb_generate_harmony_observations)
  billboard_IT_table <- generate_IT_table(billboard_corpus, billboard_generate_harmony_observations)
  rollingstone_IT_table <- generate_IT_table(rollingstone_corpus, rollingstone_generate_harmony_observations)
  
  dt_sampled <- billboard_IT_table[sample(.N, min(300000, .N))]
  ggplot(dt_sampled, aes(x = Entropy, y = InformationContent)) + geom_point() + ggtitle('Billboard (CoCoPops) Information Content vs Entropy (ppm simple)')
  ggplot(dt_sampled, aes(x = Entropy)) + geom_histogram() + ggtitle('Billboard (CoCoPops) Entropy Distrobution (ppm simple)')
  ggplot(dt_sampled, aes(x = InformationContent)) + geom_histogram() + ggtitle('Billboard (CoCoPops) InformationContent Distrobution (ppm simple)')
  
  
  dt_sampled <- rollingstone_IT_table[sample(.N, min(300000, .N))]
  ggplot(dt_sampled, aes(x = Entropy, y = InformationContent)) + geom_point() + ggtitle('Rollingstone (CoCoPops) Information Content vs Entropy (ppm simple)')
  ggplot(dt_sampled, aes(x = Entropy)) + geom_histogram() + ggtitle('Rollingstone (CoCoPops) Entropy Distrobution (ppm simple)')
  ggplot(dt_sampled, aes(x = InformationContent)) + geom_histogram() + ggtitle('Rollingstone (CoCoPops) InformationContent Distrobution (ppm simple)')
  
  dt_sampled <- irb_IT_table[sample(.N, min(300000, .N))]
  ggplot(dt_sampled, aes(x = Entropy, y = InformationContent)) + geom_point() + ggtitle('iRealB Pro Jazz Corpus Information Content vs Entropy (ppm simple)')
  ggplot(dt_sampled, aes(x = Entropy)) + geom_histogram() + ggtitle('iRealB Pro Jazz Corpus Entropy Distrobution (ppm simple)')
  ggplot(dt_sampled, aes(x = InformationContent)) + geom_histogram() + ggtitle('iRealB Pro Jazz Corpus Information Content Distrobution (ppm simple)')
  
  # plot(billboard_IT_table$Entropy, billboard_IT_table$InformationContent)
    
  # aggregate_IT_table <- list(irb_IT_table, billboard_IT_table, rollingstone_IT_table) |> rbindlist()
  # aggregate_IT_table[, c('Entropy', 'InformationContent')] |> plot(xlim = c(0, 8), ylim = c(0, 20))
  # aggregate_IT_table |> plot()
}

# ========================================
#
#   HELPER FUNCTIONS
#
# ========================================

command_copy_file <- function(srcpath, targetpath) {
  result <- system(paste("cp", srcpath, targetpath), intern = T)
  print(paste("copied to", targetpath))
  return()
}


create_data_clean_subdir <- function(subcorpus_name) {
  data_clean_subdir <- file.path("data_clean", subcorpus_name)
  if (!dir.exists(data_clean_subdir)) {
    dir.create(data_clean_subdir)
  }
}

remove_consecutive_duplicates <- function(vec) {
  return(vec |> rle() |> index2('values'))
}

calculate_ppm_info <- function(pieceObj, observations, alphabet) {
  if (length(observations) == 0) {
      return(
        data.frame(
          Observation = character(), 
          InformationContent = character(),
          Entropy = character(),
          Filepath = character()
        )
      )
  }
  print(observations)
  print(alphabet)
  model <- new_ppm_simple(alphabet_size = length(alphabet))
  seq <- factor(observations, alphabet)
  ppm_piece_res <- model_seq(
    model = model,
    seq = seq
  )
  filepath <- pieceObj$Filepath |> unique() |> unlist()
  return(
    data.frame(
      Observation = ppm_piece_res$symbol, 
      InformationContent = ppm_piece_res$information_content, 
      Entropy = ppm_piece_res$entropy,
      Filepath = rep(filepath, length(ppm_piece_res$symbol))
    )
  )
}

generate_IT_table <- function(corpusObj, observationsFUN) {
  # TODO: make this function and nested functions accept arguments to shape the data and route output
  # shaping data: consecutive duplicates, reduce harmony
  # consecutive duplicates should be removed in the humdrumR piece object itself to retain continuity with other fields
  # output routing: ppm, idyom
  # pass other information into the final dataframe such as filepath, record number, token, etc.
  
  observations <- corpusObj |> observationsFUN()
  alphabet <- observations |> unlist() |> as.vector() |> unique()
  corpusObj |>
    calculate_ppm_info(
      observations = observations |> unlist() |> as.vector(),  
      alphabet = alphabet
    ) |>
    list() -> results
    
  
  # observations_corpus <- corpusObj |> observationsFUN() 
  # alphabet <- observations_corpus |> unlist() |> as.vector() |> unique()
  # results <- lapply(observations_corpus, function(observations_piece) {
  #   if (length(observations_piece) == 0) {
  #     return(
  #       data.frame(
  #         Observation = character(),
  #         InformationContent = character(),
  #         Entropy = character()
  #       )
  #     )
  #   }
  #   model <- new_ppm_simple(alphabet_size = length(alphabet))
  #   seq <- factor(observations_piece, alphabet)
  #   ppm_piece_res <- model_seq(
  #     model = model,
  #     seq = seq
  #   )
  #   data.frame(
  #     Observation = alphabet[ppm_piece_res$symbol], 
  #     InformationContent = ppm_piece_res$information_content, 
  #     Entropy = ppm_piece_res$entropy
  #   )
  # })
  return(rbindlist(results))
}

# ========================================
#
#   IRB-SPECIFIC FUNCTIONS
#
# ========================================

irb_clean_data <- function() {
  create_data_clean_subdir("iRb_v1-0")
  system("python3 scripts/clean_iRb.py", intern = T)
}

irb_generate_harmony_data <- function(corpusObj) {
  # iRb: generate roman numerals
  # kern spine contains the root note
  # exten spine contains any extensions on top of the root
  # if kern and exten are joined by a colon (:), it resembles harte syntax which we can convert to harm
  # to see this harm data, retrieve the Harm field by piping to select(Harm) or pull(Harm)
  corpusObj |> 
    cleave(c('kern', 'exten')) |>  # join the kern and exten spines creates an Exten field
    filter(Spine == 2) |> # isolate this joined spine
    mutate(
      # create a Harm field that uses the kern and exten data to create the "harte" syntax which can be converted back to harm
      Harm = paste(Token, Exten, sep = ":") |> harm(Exclusive = 'harte')
    ) |>
    unfilter() |> # restoring original data in the corpus object
    select() -> corpusObj
  return(corpusObj)
}

irb_generate_harmony_observations <- function(corpusObj) {
  harmlists <- corpusObj |>
    filter(Exclusive == 'kern') |>
    group_by(Piece) |>
    summarize(
      HarmList = Harm |> reduceHarmony() |> na.omit() |> list()
    )
  return(harmlists$HarmList)
}
# ========================================
#
#   COCOPOPS (BILLBOARD + ROLLINGSTONE)
#
# ========================================

billboard_clean_data <- function() {
  create_data_clean_subdir("billboard")
  billboard_data_filepaths <- list.files("data_raw/CoCoPops/BillBoard/Data", full.names = T)
  sapply(billboard_data_filepaths, function(x) command_copy_file(srcpath = x, targetpath = "data_clean/billboard/"))
  return()
}

rollingstone_clean_data <- function() {
  create_data_clean_subdir("rollingstone")
  billboard_data_filepaths <- list.files("data_raw/CoCoPops/RollingStone/Data", full.names = T)
  sapply(billboard_data_filepaths, function(x) command_copy_file(srcpath = x, targetpath = "data_clean/rollingstone/"))
  return()
}

cocopops_generate_harmony_data <- function(corpusObj) {
  # use the harte spine to convert to roman numerals using harm()
  # data is located in the Harm field
  corpusObj |> 
    filter(Exclusive == 'harte') |>
    mutate(Harm = harm(Token)) |>
    unfilter() |> # restoring original data in the corpus object
    select() -> corpusObj
  return(corpusObj)
}
  
billboard_generate_harmony_observations <- function(corpusObj) {
  harmLists <- corpusObj |>
    filter(Exclusive == 'harte') |>
    group_by(Piece) |>
    summarize(
      HarmList = Harm |> reduceHarmony() |> na.omit() |> list()
    )
  return(harmLists$HarmList)
}

rollingstone_generate_harmony_observations <- function(corpusObj) {
  harmLists <- corpusObj |>
    filter(Spine == 4) |> # 2nd annotator's harte spine
    group_by(Piece) |>
    summarize(
      HarmList = Harm |> reduceHarmony() |> na.omit() |> list()
    )
  return(harmLists$HarmList)
}

# ========================================
#
#   MUSICXML CONVERSIONS
#
# ========================================

file_convert_musicxml_2_humdrum <- function(filename, subcorpus_name) {
  srcpath <- file.path("data_raw", subcorpus_name, filename)
  targetfilename <- paste0(tools::file_path_sans_ext(filename), ".hum")
  targetpath <- file.path("data_clean", subcorpus_name, targetfilename)
  command_musicxml_2_humdrum(srcpath, targetpath)
  return()
}

command_musicxml_2_humdrum <- function(srcpath, targetpath) {
  result <- system(paste("~/humdrum-tools/humextra/bin/xml2hum", srcpath, ">", targetpath), intern = T)
  print(paste("converted", targetpath))
  return()
}

convert_musicxml_corpus_2_humdrum <- function(subcorpus_name) {
  # this function assumes musicxml data is in ./data_raw/<subcorpus_name>/
  # converts the data to humdrum text format
  # saves the converted file to ./data_clean/<subcorpus_name>/
  # (note: filenames are preserved except extension is changed to .hum)
  
  # check if raw data exists
  raw_data_subdir_path <- file.path("data_raw", subcorpus_name)
  if (!dir.exists(raw_data_subdir_path)) {
    stop(paste("raw data does not exist for this subcorpus", subcorpus_name))
  }
  
  # create clean data subdirectory
  create_data_clean_subdir(subcorpus_name = subcorpus_name)
  clean_data_subdir_path <- file.path("data_clean", subcorpus_name)
  
  # get data filenames and filter for files that have an xml extension
  data_filenames <- list.files(raw_data_subdir_path, full.names = F)
  data_filenames <- data_filenames[tools::file_ext(data_filenames) == "xml"]
  
  # convert all raw data files from musicxml to humdrum
  sapply(data_filenames, function(x) file_convert_musicxml_2_humdrum(filename = x, subcorpus_name = subcorpus_name))
  return()
}


# ========================================
#
#   DEPRECATED THINGS
#
# ========================================

# charlie parker omnibook - musicxml
# convert_musicxml_corpus_2_humdrum("charlie-parker-omnibook")
# validateHumdrum("data_clean/charlie-parker-omnibook/*") 
# charlie_parker_omnibook_corpus <- readHumdrum("data_clean/charlie-parker-omnibook/*") 

main()
