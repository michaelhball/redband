import bz2
import os
import pickle
import shutil
import tempfile
import yaml
from pathlib import Path
from typing import Any
from yaml import Loader

from cloudpathlib import CloudPath, GSPath
from contextlib import contextmanager
from google.api_core.exceptions import NotFound

from redband.typing import JSON

# TODO: sort out authentication —> is it reasonable to expect the user to use these environment variables?
# TODO: should be able to pickle directly to / from the cloud (i.e. without pickling) ?


def _is_gcs_path(file_path: str) -> bool:
    return file_path.startswith(GSPath.cloud_prefix)


def _is_cloud_path(file_path: str) -> bool:
    return _is_gcs_path(file_path)


def _is_local_path(file_path: str) -> bool:
    return not _is_cloud_path(file_path)


def file_exists(file_path: str) -> bool:
    """Checks whether a local or cloud `file_path` 'exists' (is a valid file or directory)."""
    if _is_cloud_path(file_path):
        return CloudPath(file_path).exists()
    else:
        return Path(file_path).exists()


@contextmanager
def _tmp_dir():
    """Opens a local temporary directory that is removed once outside the context"""
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir)


@contextmanager
def _tmp_copy_and_open(src_path: str):
    """This function allows opening a file from either local or remote source via first copying it to
    a tmp directory. Usage:
        with tmp_copy_and_open("gs://[...]") as tmp_path:
            df = pd.read_csv(tmp_path)
    """
    # we don't need to do any copying if the file is already local
    if _is_local_path(src_path):
        yield src_path

    # if it's a cloud path, copy to a local tmp directory & yield the new location
    else:
        with _tmp_dir() as tmp_dir:
            local_path = os.path.join(tmp_dir, os.path.basename(src_path))
            try:
                CloudPath(src_path).copy(local_path)
            except NotFound as nf:
                raise FileNotFoundError(f"File {src_path} does not exist.") from nf
            yield local_path


def load_pickle(file_path: str, **kwargs) -> Any:
    """Load a pickled object from a given file_path, either local or cloud."""

    if _is_cloud_path(file_path):
        with CloudPath(file_path).open("rb") as f:
            return pickle.load()

    with _tmp_copy_and_open(file_path) as tmp_file:
        if file_path.endswith(".pklz"):
            with bz2.BZ2File(tmp_file, "r") as f:
                return pickle.load(f, **kwargs)
        else:
            with open(tmp_file, "rb") as f:
                return pickle.load(f, **kwargs)


def load_yaml(yaml_path: str) -> JSON:
    """Loads a YAML file to"""
    with _tmp_copy_and_open(yaml_path) as tmp_file:
        with open(tmp_file, "r") as f:
            return yaml.load(f, Loader=Loader)
