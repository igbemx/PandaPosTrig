#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name="tangods-pandapostrig",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Panda position based triggering for STXM FPGA.",
    url="https://gitlab.maxiv.lu.se/softimax/tangods-softimax-pandapostrig",
    packages=find_packages(exclude=["tests", "*.tests.*", "tests.*", "scripts"]),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "pytango",
        "pyparsing",
    ],
    entry_points={"console_scripts": ["PandaPosTrig = PandaPosTrig.PandaPosTrig:main",]},
)
