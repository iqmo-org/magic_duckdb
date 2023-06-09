from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open("magic_duckdb/_version.py", "r") as file:
    code = file.read()
    exec(code)
    _version = __version__  # type: ignore # noqa

setup(
    name="magic_duckdb",
    version=_version,  # type: ignore # noqa
    description="Jupyter Cell and Line Magics for DuckDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iqmo-org/magic_duckdb",
    author="iqmo",
    author_email="info@iqmo.com",
    classifiers=[],
    keywords="Jupyter, Cell Magic, DuckDB, Line Magic, Magic",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=["duckdb>=0.8.0", "pandas"],
)
