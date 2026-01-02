import os
import shutil
from typing import Any, Iterable

import pandas as pd
from rpy2 import robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.methods import RS4

from .constants import PROJECT_ROOT, supported_subcorpora_paths, humdrumR

# -------------------- data cleaning -------------------- #
def clean_subcorpus(subcorpus_name: str, overwrite: bool = False) -> None:
    clean_data_subdir = os.path.join(PROJECT_ROOT, "data_clean", subcorpus_name)
    if os.path.isdir(clean_data_subdir) and not overwrite:
        return
    match subcorpus_name:
        case "iRb_v1-0":
            from .data_cleaning import clean_iRb
            clean_iRb.main()
        case "weimar":
            from .data_cleaning import weimar_to_hum
            weimar_to_hum.main()
        case _:
            raise Exception(f"no data cleaning process found for this subcorpus: {subcorpus_name}")
    return

def copy_files_between_dirs(src_dir: str, dest_dir: str) -> None:
    for filename in os.listdir(src_dir):
        src_filepath = os.path.join(src_dir, filename)
        dest_filepath = os.path.join(dest_dir, filename)
        shutil.copy2(src_filepath, dest_filepath) 

# -------------------- dataframe helpers -------------------- #
def df_filter(df: pd.DataFrame, field: str, value: Any) -> pd.DataFrame:
    """Filter the given dataframe where the column "field" is equal to the given "value"."""
    # return df[df[field] == value].astype({col: df[col].dtype for col in df.columns}) # type: ignore
    return df.loc[df[field] == value]

def df_remove_consecutive_duplicates(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    return df.loc[df[column_name] != df[column_name].shift()]

def fix_humtable_df_type_conversion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.convert_dtypes()
    df = df.infer_objects()
    # df = df.astype({"Exclusive": "category", "Key": "category", "KeySignature": "category"})
    return df

# -------------------- reading from humdrum -------------------- #
def read_subcorpus_to_df(subcorpus_name: str) -> pd.DataFrame:
    data_src_path = os.path.join(PROJECT_ROOT, supported_subcorpora_paths[subcorpus_name])
    corpus = humdrumR.readHumdrum(data_src_path, recursive = True)
    df = humdrumr_obj_to_humtable_df(corpus)
    df = fix_humtable_df_type_conversion(df)
    df["subcorpus_name"] = subcorpus_name
    return df

def humdrumr_obj_to_humtable_df(humdrumr_obj: RS4) -> pd.DataFrame:
    r_df = robjects.DataFrame(humdrumr_obj.slots['Humtable'])
    return r_df_to_pandas_df(r_df)

def r_df_to_pandas_df(r_df: robjects.DataFrame) -> pd.DataFrame:
    with (robjects.default_converter + pandas2ri.converter).context():
        pd_df = robjects.conversion.get_conversion().rpy2py(r_df)
        pd_df[pd_df == robjects.NA_Character] = pd.NA
    return pd_df

# -------------------- harmony computation -------------------- #
def reduce_harmony(token_list: list) -> list:
    for idx, token in enumerate(token_list):
        if token == "-IVM7M9M13": # an edge case for humdrumR.reduceHarmony
            token_list[idx] = "-IV"
    token_list = [convert_NA_pd_to_rpy(token) for token in token_list]
    results = list(humdrumR.reduceHarmony(robjects.StrVector(token_list)))
    results = [convert_NA_rpy_to_pd(x) for x in results]
    return results

def harm(token_list: Iterable[Any], key_list: Iterable[Any], inversion: bool) -> list[str]:
    if not isinstance(token_list, list):
        token_list = list(token_list)
    if not isinstance(key_list, list):
        key_list = list(key_list)
    assert len(token_list) == len(key_list)
    token_list = [convert_NA_pd_to_rpy(token) for token in token_list]
    key_list = [convert_NA_pd_to_rpy(key) for key in key_list]
    results = list(humdrumR.harm(
        robjects.StrVector(token_list), 
        Key = robjects.StrVector(key_list),
        inversion = inversion
    ))
    results = [convert_NA_rpy_to_pd(x) for x in results]
    return results

def convert_NA_rpy_to_pd(item: Any) -> Any:
    return pd.NA if item == robjects.NA_Character else item 

def convert_NA_pd_to_rpy(item: Any) -> Any:
    return robjects.NA_Character if pd.isna(item) else item 
