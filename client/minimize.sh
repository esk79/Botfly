#!/usr/bin/env bash

# if needed: `pip install pyminifier`
pyminifier --obfuscate --gzip client.py > minclient.py