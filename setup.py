from setuptools import setup

setup(
    name='batdata',
    version='0.0.1',
    packages=['batdata'],
    install_requires=['pandas'],
    entry_points={
        "console_scripts": ["batdata-convert=batdata.cli:main"],
        "materialsio.parser": [
            'arbin = batdata.extractors.arbin:ArbinExtractor',
            'maccor = batdata.extractors.maccor:MACCORExtractor',
        ]
    }
)
