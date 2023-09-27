"""
A workflow for running MPAS.
"""

import datetime as dt
import logging
from functools import partial

from pathlib import Path
from typing import Tuple, Union

import f90nml
import requests
from iotaa import asset, external, ids, logcfg, run, task

PathT = Union[Path, str]

NAMELIST_WPS = "/home/pmwork/conda/envs/ungrib/etc/wps/namelist.wps"
UNGRIB = "/home/pmwork/conda/envs/ungrib/bin/ungrib"
VTABLE_GFS = "/home/pmwork/conda/envs/ungrib/etc/wps/Vtable.GFS"

logcfg()

# Tasks


@task
def ics(rootdir: PathT, cycle: str):
    fn = dt.datetime.fromisoformat(cycle).strftime("FILE:%Y-%m-%d_%H:00:00")
    rd = _rundir(rootdir, cycle)
    path = rd / fn
    taskname = "Initial conditions in %s" % rd
    yield taskname
    yield asset(path, path.exists)
    yield [gribfile_aaa(rootdir, cycle), namelist_wps(rootdir, cycle), vtable(rootdir, cycle)]
    run(taskname, "ungrib 2>&1 | tee ungrib.out", cwd=path.parent)


@task
def gribfile_aaa(rootdir: PathT, cycle: str):
    path = _rundir(rootdir, cycle) / "GRIBFILE.AAA"
    yield "GRIBFILE.AAA symlink %s" % path
    yield asset(path, path.exists)
    g = gfs_local(rootdir, cycle)
    yield g
    path.symlink_to(Path(ids(g)).name)


@task
def vtable(rootdir: PathT, cycle: str):
    path = _rundir(rootdir, cycle) / "Vtable"
    yield "Variable table file %s" % path
    yield asset(path, path.exists)
    yield rundir(rootdir, cycle)
    path.symlink_to(Path(VTABLE_GFS))


@task
def namelist_wps(rootdir: PathT, cycle: str):
    path = _rundir(rootdir, cycle) / "namelist.wps"
    yield "Edited WPS namelist file %s" % path
    yield asset(path, path.exists)
    yield rundir(rootdir, cycle)
    timestr = dt.datetime.fromisoformat(cycle).strftime("%Y-%m-%d_%H:00:00")
    f90nml.patch(NAMELIST_WPS, {"share": {"start_date": timestr, "end_date": timestr}}, path)


@task
def gfs_local(rootdir: PathT, cycle: str):
    url = _gfsurl(cycle)
    path = _rundir(rootdir, cycle) / Path(url).name
    taskname = "Local GFS file %s" % path
    yield taskname
    yield asset(path, path.exists)
    yield [rundir(rootdir, cycle), gfs_upstream(cycle)]
    logging.info("%s: Fetching %s", taskname, url)
    response = requests.get(url, timeout=60)
    with open(path, "wb") as f:
        f.write(response.content)


@external
def gfs_upstream(cycle: str):
    url = _gfsurl(cycle)
    yield "Upstream GFS file %s" % url
    yield asset(url, partial(requests.head, url))


@task
def rundir(rootdir: PathT, cycle: str):
    path = _rundir(rootdir, cycle)
    yield "Run directory %s" % path
    yield asset(path, path.exists)
    yield None
    path.mkdir(parents=True)


# Helpers


def _cycle(cycle: str) -> Tuple[str, str]:
    c = dt.datetime.fromisoformat(cycle)
    return c.strftime("%Y%m%d"), c.strftime("%H")


def _gfsurl(cycle: str) -> str:
    yyyymmdd, hh = _cycle(cycle)
    return (
        "https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/gfs.{yyyymmdd}/{hh}/atmos/"
        "gfs.t{hh}z.pgrb2.0p25.f000"
    ).format(yyyymmdd=yyyymmdd, hh=hh)


def _rundir(rootdir: PathT, cycle: str) -> Path:
    yyyymmdd, hh = _cycle(cycle)
    return Path(rootdir) / yyyymmdd / hh
