"""
Basic setuptools configuration.
"""

import json
import os

from setuptools import find_packages, setup  # type: ignore

recipe = os.environ.get("RECIPE_DIR", "../recipe")
with open(os.path.join(recipe, "meta.json"), "r", encoding="utf-8") as f:
    meta = json.load(f)

name_conda = meta["name"]
name_py = name_conda.replace("-", "_")

setup(
    name=name_conda,
    package_data={name_py: ["resources/*"]},
    packages=find_packages(
        exclude=["%s.tests" % name_py],
        include=[name_py, "%s.*" % name_py],
    ),
    version=meta["version"],
)
