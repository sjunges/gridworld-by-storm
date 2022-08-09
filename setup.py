from setuptools import setup, find_packages
setup(
    name="gridstorm",
    version="0.2",
    packages=find_packages(),
    scripts=[],
    package_data={
        # If any package contains *.nm or *.rst files, include them:
        "": ["*.rst"],
        "gridstorm.models": ["files/*.nm"]
    },
    include_package_data=True,

    # metadata to display on PyPI
    author=["Sebastian Junges"],
    description="This is a benchmark set visualiser for simulating grid worlds with Storm.",
    keywords="gridworld storm model-checking",
    install_requires=[
        "stormpy>=1.7.0", "matplotlib", "tqdm"
    ],
)