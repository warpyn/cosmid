# constants
import os
HARMONY_VIEWPOINT_LABEL = "harmony_viewpoint"
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
supported_subcorpora = [
    "billboard",
    "rollingstone",
    "iRb_v1-0",
    "star_wars_thematic_corpus",
    "weimar"
]
supported_subcorpora_paths = {
    "billboard": "data_raw/CoCoPops/Billboard/Data/*",
    "rollingstone": "data_raw/CoCoPops/RollingStone/Data/*",
    "iRb_v1-0": "data_clean/iRb_v1-0/*",
    "star_wars_thematic_corpus": "data_raw/Star-Wars-Thematic-Corpus/*.krn",
    "weimar": "data_clean/weimar/*"
}

# R packages
from rpy2.robjects.packages import importr, Package
humdrumR: Package = importr("humdrumR")
ppm: Package = importr("ppm")
