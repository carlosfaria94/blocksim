from setuptools import setup, find_packages
setup(
    name="BlockSim",
    version="0.1",
    packages=find_packages(),

    # metadata for upload to PyPI
    author="Carlos Faria",
    author_email="carlosfigueira@tecnico.ulisboa.pt",
    description="A discrete event Blockchain simulator",
    license="MIT",
    keywords="blocksim blockchain simulation discrete-event ethereum",
    url="https://blockbird.studio",   # project home page, if any
    project_urls={
        "Bug Tracker": "https://github.com/BlockbirdStudio/blocksim/issues",
        "Source Code": "https://github.com/BlockbirdStudio/blocksim",
    }
)