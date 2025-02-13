from setuptools import setup, find_packages

setup(
    name="workflow_manager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'aiohttp',
        'pydantic'
    ]
)