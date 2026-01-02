import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cosmid import Cosmid
from cosmid.constants import supported_subcorpora

subcorpora_names = ["rollingstone"]
output_filepath = "results.parquet"

for subcorpus_name in subcorpora_names:
    assert subcorpus_name in supported_subcorpora, f"unsupported subcorpus: {subcorpus_name}"

c = Cosmid()
c.ingest_subcorpora(subcorpora_names)
c.write_harmony_viewpoint_observations(subcorpora_names, inversions=False, extensions=True)
c.compute_harmony_viewpoint_idyom(remove_consecutive_duplicates=True, verbose=True)
c.to_parquet(output_filepath)
print("saved corpus dataframe")
