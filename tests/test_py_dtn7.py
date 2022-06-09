from pathlib import Path

import toml

import py_dtn7


def test_versions_are_in_sync():
    """Checks if the pyproject.toml and package.__init__.py __version__ are in sync."""

    # shamelessly ripped off from this GitHub issue:
    # https://github.com/python-poetry/poetry/issues/144#issuecomment-877835259
    # but for real -- this problem should have been solved years ago, sheesh.
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject = toml.loads(open(str(path)).read())
    pyproject_version = pyproject["tool"]["poetry"]["version"]

    package_init_version = py_dtn7.__version__

    assert package_init_version == pyproject_version
