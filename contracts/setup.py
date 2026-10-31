"""Setup script for bidscreen_contracts package."""

from setuptools import find_packages, setup

setup(
    name="bidscreen_contracts",
    version="0.1.0",
    description="Shared Pydantic models and enums for the Bid Compliance Screening Service",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
    ],
)
