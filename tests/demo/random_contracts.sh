#!/bin/bash

PYTHONPATH=./src \
python3 -B -m modelmock generate contracts \
--total=10 \
--price=15 \
--multiplier=1000000
