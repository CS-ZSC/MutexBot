#!/bin/bash

# This script is used to run the Python script that encrypts the data and returns the key.

# Usage: ./run_encrypt.sh

if [ "$#" -ne 0 ]; then
    echo "Usage: $0 "
    exit 1
fi

python3 encrypt.py
