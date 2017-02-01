#!/usr/bin/env bash

# if needed: `pip install pyminifier`
pyminifier --obfuscate-variables --obfuscate-builtins client.py > minclient.py