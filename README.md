# Atari-uIP-Fetcher
A tool to recursively fetch files from an Atari ST via "uip-tools" (https://bitbucket.org/sqward/uip-tools) with the 'Netusbee' Atari cartridge port dongle.

The local filesystem directory of files is compatible with Hatari's (et al) GemDos hard disk boot, so an emulator can boot an Atari using the host's fetched directory.

#### Installation
Create a virtual environment in the source directory and install dependencies:
```console
python3 -m venv venv
source venv/bin/activate
pip intstall --upgrade pip
pip intstall --upgrade setuptools
pip install -r requirements.txt
```

#### Usage options
`python uip_fetcher.py --help`
