from setuptools import setup, find_packages

setup(
    name='batdata',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['pandas'],
    entry_points={
        "console_scripts": ["batdata-convert=batdata.cli:main"],
        "materialsio.parser": [
            'arbin = batdata.extractors.arbin:ArbinExtractor',
            'maccor = batdata.extractors.maccor:MACCORExtractor',
            'batteryarchive = batdata.extractors.batteryarchive:BatteryArchiveExtractor',
        ]
    }
)
