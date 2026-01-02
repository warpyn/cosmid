"""
set CFFI mode to ABI
ABI is default but rpy2 tries to load in API mode first
(API mode doesn't work for me)
"""
import os
os.environ["RPY2_CFFI_MODE"] = "ABI"

import numpy as np
import pandas as pd

from .constants import HARMONY_VIEWPOINT_LABEL
from .data_utils import (
    clean_subcorpus,
    read_subcorpus_to_df,
    df_filter,
    df_remove_consecutive_duplicates,
    harm,
    reduce_harmony
)
from .model_utils import (
    get_harmony_viewpoint_alphabet,
    train_ltm,
    compute_piece_idyom_predictions,
)

class Cosmid:

    def __init__(self) -> None:
        self.df = pd.DataFrame({"Token": pd.Series()})

    def clean_subcorpora(self, subcorpora_names: list[str]) -> None:
        for subcorpus_name in subcorpora_names:
            clean_subcorpus(subcorpus_name)
        return

    def ingest_subcorpora(self, subcorpora_names: list[str]) -> None:
        for subcorpus_name in subcorpora_names:
            subcorpus_df = read_subcorpus_to_df(subcorpus_name)
            self.df = subcorpus_df if self.df.empty else pd.concat([self.df, subcorpus_df], ignore_index=True)
            print(f"ingested subcorpus: {subcorpus_name}")
        return

    def write_subcorpus_harmony_viewpoint_observations(self, subcorpus_name: str, inversions: bool, extensions: bool) -> None:

        subcorpus_df = df_filter(self.df, "subcorpus_name", subcorpus_name)
        harm_data, harm_data_index = None, None

        match subcorpus_name:
            case "billboard":
                df_filtered = df_filter(subcorpus_df, "Exclusive", "harte")
                harm_data = harm(df_filtered["Token"], df_filtered["Key"], inversion=inversions)
                if not extensions:
                    harm_data = reduce_harmony(harm_data)
                harm_data_index = df_filtered.index
            case "rollingstone":
                df_filtered = df_filter(subcorpus_df, "Spine", 4)
                harm_data = harm(df_filtered["Token"], df_filtered["Key"], inversion=inversions)
                if not extensions:
                    harm_data = reduce_harmony(harm_data)
                harm_data_index = df_filtered.index
            case "iRb_v1-0":
                kern_filtered = df_filter(subcorpus_df, "Exclusive", "kern")
                exten_filtered = df_filter(subcorpus_df, "Exclusive", "exten")
                kern_spine = list(kern_filtered["Token"])
                exten_spine = list(exten_filtered["Token"])
                harte_joined_spine = [f"{kern}:{exten}" for kern, exten in zip(kern_spine, exten_spine)]
                key_field_data = list(kern_filtered["Key"])
                harm_data = harm(harte_joined_spine, key_field_data, inversion=inversions)
                if not extensions:
                    harm_data = reduce_harmony(harm_data)
                harm_data_index = kern_filtered.index
            case "star_wars_thematic_corpus":
                # only use pieces with a harm spine. 
                # if there is only a harte spine, the piece does not have a tonal center.
                df_filtered = df_filter(subcorpus_df, "Exclusive", "harm")
                harm_data = harm(df_filtered["Token"], df_filtered["Key"], inversion=inversions)
                if not extensions:
                    harm_data = reduce_harmony(harm_data)
                harm_data_index = df_filtered.index
            case "weimar":
                df_filtered = df_filter(subcorpus_df, "Exclusive", "harte")
                harm_data = harm(df_filtered["Token"], df_filtered["Key"], inversion=inversions)
                if not extensions:
                    harm_data = reduce_harmony(harm_data)
                harm_data_index = df_filtered.index
            case _:
                raise Exception(f"unsupported subcorpus: {subcorpus_name}")

        assert harm_data is not None and harm_data_index is not None
        if HARMONY_VIEWPOINT_LABEL not in self.df.columns:
            self.df[HARMONY_VIEWPOINT_LABEL] = pd.NA
        self.df.update(pd.DataFrame({HARMONY_VIEWPOINT_LABEL: harm_data}, index=harm_data_index))
        print(f"wrote harmony viewpoint observations: {subcorpus_name}")
        return

    def write_harmony_viewpoint_observations(self, subcorpora_names: list[str], inversions: bool, extensions: bool) -> None:
        for subcorpus_name in subcorpora_names:
            self.write_subcorpus_harmony_viewpoint_observations(subcorpus_name, inversions, extensions)
        return

    def get_piece_df_with_harmony_viewpoint_observations(self, filename: str, remove_consecutive_duplicates: bool) -> pd.DataFrame:
        harm_labels_df = self.df.loc[(self.df["Filename"] == filename) & (self.df[HARMONY_VIEWPOINT_LABEL].notna())]
        if remove_consecutive_duplicates:
            harm_labels_df = df_remove_consecutive_duplicates(harm_labels_df, HARMONY_VIEWPOINT_LABEL)
        return harm_labels_df

    def compute_harmony_viewpoint_idyom(self, remove_consecutive_duplicates: bool = True, verbose: bool = False) -> None:

        alphabet = get_harmony_viewpoint_alphabet(self.df)
        filenames = list(self.df.Filename.unique())

        # train LTM
        print("ltm training started")
        ltm = None
        for filename in filenames:
            if verbose:
                print(filename)
            harm_labels_df = self.get_piece_df_with_harmony_viewpoint_observations(filename, remove_consecutive_duplicates)
            harm_labels = np.array(harm_labels_df[HARMONY_VIEWPOINT_LABEL], dtype=str)
            if len(harm_labels) == 0:
                continue
            ltm = train_ltm(harm_labels, alphabet, ltm)
        print("ltm training finished")

        # train STM & idyom prediction (LTM + STM)
        print("ltm + stm prediction started")
        assert ltm is not None
        for filename in filenames:
            if verbose:
                print(filename)
            harm_labels_df = self.get_piece_df_with_harmony_viewpoint_observations(filename, remove_consecutive_duplicates)
            harm_labels = np.array(harm_labels_df[HARMONY_VIEWPOINT_LABEL], dtype=str)
            if len(harm_labels) == 0:
                continue
            results = compute_piece_idyom_predictions(harm_labels, alphabet, ltm)
            for column_name in results.columns:
                if column_name not in self.df.columns:
                    self.df[column_name] = pd.NA
            self.df.update(results.set_axis(harm_labels_df.index, axis="index"))
        print("ltm + stm prediction finished")

        return

    def to_parquet(self, output_path: str) -> None:
        self.df.to_parquet(output_path)
        return

    def read_parquet(self, source_path: str) -> None:
        self.df = pd.read_parquet(source_path)
        return
