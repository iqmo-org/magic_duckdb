from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="magic_duckdb",
    version="0.1.11",
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
    install_requires=["duckdb>=0.7.1"],
)
