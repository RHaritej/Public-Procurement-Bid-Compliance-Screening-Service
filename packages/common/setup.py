from setuptools import find_packages, setup

setup(
    name="bidscreen-common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "structlog>=23.0.0",
        "starlette>=0.28.0",
        "prometheus-client>=0.17.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp-proto-grpc>=1.20.0",
    ],
)
