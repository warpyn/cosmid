from typing import NewType

import numpy as np
import pandas as pd
from rpy2 import robjects
from rpy2.robjects import Vector
from rpy2.robjects.methods import RS4

from .constants import HARMONY_VIEWPOINT_LABEL, ppm

# custom types
ppmModel = NewType("ppmModel", RS4)
ppmResult = NewType("ppmResult", Vector)


def compute_entropy(dist: np.ndarray) -> float:
    """Compute the shannon entropy (base 2 aka bits) of the given distribution."""
    assert len(np.shape(dist)) == 1, f"distribution is not a 1D array: {np.shape(dist)}"
    assert np.isclose(np.sum(dist), 1), f"distribution does not sum to 1: {np.sum(dist)}"
    return np.sum(-dist * np.log2(dist))

def get_harmony_viewpoint_alphabet(df: pd.DataFrame) -> np.ndarray:
    return np.array(df.loc[df[HARMONY_VIEWPOINT_LABEL].notna()][HARMONY_VIEWPOINT_LABEL].unique(), dtype=str)

def train_ltm(observations: list | np.ndarray, alphabet: list | np.ndarray, ltm: ppmModel | None = None) -> ppmModel:
    """
    Train a long-term ppm model for the given observation sequence in the given alphabet.
    Use the R ppm package, found here: https://github.com/pmcharrison/ppm
    If an existing long-term model is given, continue training this model on the given observations.
    """
    if ltm is None:
        ltm = ppm.new_ppm_simple(alphabet_levels = robjects.StrVector(alphabet))
    assert ltm is not None
    # ipdb.set_trace()
    ppm.model_seq(
        model = ltm,
        seq = robjects.FactorVector(robjects.StrVector(observations), robjects.StrVector(alphabet)),
        train = True,
        predict = False
    )
    return ltm

def compute_piece_idyom_predictions(
    observations: list | np.ndarray,
    alphabet: list | np.ndarray,
    ltm: ppmModel,
    bias: int = -1
) -> pd.DataFrame:
    """
    For a single piece, compute the information content and entropy under the IDyOM software
    design for the given observations under the given alphabet. Return the prediction data for
    the combined distribution of the short-term and long-term model predictions.

    Combine prediction results for all symbols in the sequence
    from the long-term and short-term models using a weighted geometric mean,
    where the weights are inversely proportional to the entropies of the models'
    distributions, as is the default implementation in IDyOM.

    This requires that a long-term model is already trained and passed in as an input.
    Use the R ppm package, found here: https://github.com/pmcharrison/ppm
    """
    assert np.array(observations).size > 0, "empty observations input"
    assert np.array(alphabet).size > 0, "empty alphabet input"

    # === model predictions ===
    ltm_res: ppmResult = ppm.model_seq(
        model = ltm,
        seq = robjects.FactorVector(robjects.StrVector(observations), robjects.StrVector(alphabet)),
        train = False,
        predict = True
    )
    stm = ppm.new_ppm_simple(alphabet_levels = robjects.StrVector(alphabet))
    stm_res: ppmResult = ppm.model_seq(
        model = stm,
        seq = robjects.FactorVector(robjects.StrVector(observations), robjects.StrVector(alphabet)),
        train = True,
        predict = True
    )

    # === combine model predictions ===
    assert list(ltm_res.rx2("symbol")) == list(stm_res.rx2("symbol")), "symbol factor indexes are not the same between LTM and STM"
    ltm_dists = np.array(ltm_res.rx2("distribution"), dtype=np.float64)
    stm_dists = np.array(stm_res.rx2("distribution"), dtype=np.float64)
    # subtract 1 to move from R's 1-based indexing to Python's 0-based indexing
    symbol_factor_idxs = np.array(stm_res.rx2("symbol"), dtype=np.int32) - 1 
    symbol_sequence_length = symbol_factor_idxs.size

    # weight = entropy ^ (-bias) 
    # weights are inversely related to entropy,
    # so low entropy model as greater influence to composite model for each distribution
    # below arrays have shape (symbol_sequence_length, 1)
    ltm_weights_unnormalized = np.pow(np.sum(ltm_dists * -np.log2(ltm_dists), axis=-1, keepdims=True), -bias)
    stm_weights_unnormalized = np.pow(np.sum(stm_dists * -np.log2(stm_dists), axis=-1, keepdims=True), -bias)

    # normalize ltm and stm weights at each symbol prediction
    stacked_weights = np.hstack([ltm_weights_unnormalized, stm_weights_unnormalized])
    stacked_weights_normalized = stacked_weights / np.sum(stacked_weights, axis=-1, keepdims=True)
    ltm_weights_normalized = stacked_weights_normalized[:,0].reshape((symbol_sequence_length, 1))
    stm_weights_normalized = stacked_weights_normalized[:,1].reshape((symbol_sequence_length, 1))

    # compute composite distributions and renormalize at each symbol prediction
    # (symbol_sequence_length, alphabet_size) = 
    #   (symbol_sequence_length, alphabet_size) ^ (symbol_sequence_length, 1) *
    #   (symbol_sequence_length, alphabet_size) ^ (symbol_sequence_length, 1)
    composite_dists = np.pow(ltm_dists, ltm_weights_normalized) * np.pow(stm_dists, stm_weights_normalized)
    composite_dists = composite_dists / np.sum(composite_dists, axis=-1, keepdims=True)

    # compute composite entropy and information content values
    composite_dists_entropy = np.sum(composite_dists * -np.log2(composite_dists), axis=-1)
    composite_dists_information_content = -np.log2(composite_dists[np.arange(symbol_sequence_length),symbol_factor_idxs])

    return pd.DataFrame({
        "entropy": composite_dists_entropy,
        "information_content": composite_dists_information_content,
        "ltm_entropy": np.array(ltm_res.rx2("entropy"), dtype=np.float64),
        "stm_entropy": np.array(stm_res.rx2("entropy"), dtype=np.float64),
        "ltm_information_content": np.array(ltm_res.rx2("information_content"), dtype=np.float64),
        "stm_information_content": np.array(stm_res.rx2("information_content"), dtype=np.float64),
        "ltm_model_order": np.array(ltm_res.rx2("model_order"), dtype=np.float64),
        "stm_model_order": np.array(stm_res.rx2("model_order"), dtype=np.float64)
    })
