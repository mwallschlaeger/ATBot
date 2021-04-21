#!/bin/bash

PYTHON3_ENV="/home/mwall/Documents/code/venv3.6"
#TWITTER_SH = "./twitter.sh"

source "${PYTHON3_ENV}/bin/activate"
/usr/bin/env python --version
/usr/bin/env python twitter_cmd_wrapper.py -twittersh TWITTER_SH -username "Goodgoodksey1" -password "peple001" -phone "89067668172" 
