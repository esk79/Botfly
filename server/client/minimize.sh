#!/usr/bin/env bash

# if needed: `pip install pyminifier`
pyminifier --gzip client.py > minclient.py
pyminifier --gzip install.py > mininstall.py