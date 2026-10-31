from setuptools import find_packages, setup

setup(
    name="bidscreen-api",
    version="0.1.0",
    package_dir={"": "."},
    packages=["bidscreen_api", "bidscreen_api.routes"],
)
