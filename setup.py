from setuptools import setup, find_packages

setup(
    name='batdata',
    version='0.0.1',
    packages=find_packages(),
    install_requires=['pandas'],
    entry_points={
        "console_scripts": ["batdata-convert=batdata.cli:main"],
        "materialsio.parser": [
            'arbin = batdata.extractors.arbin:ArbinExtractor',
            'maccor = batdata.extractors.maccor:MACCORExtractor',
        ]
    }
)
