import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cosmid import Cosmid
from cosmid.constants import supported_subcorpora

output_filepath = "results.parquet"

c = Cosmid()
c.ingest_subcorpora(supported_subcorpora)
c.write_harmony_viewpoint_observations(supported_subcorpora, inversions=False, extensions=True)
c.compute_harmony_viewpoint_idyom(remove_consecutive_duplicates=True, verbose=True)
c.to_parquet(output_filepath)
print("saved corpus dataframe")
