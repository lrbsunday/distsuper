#!/bin/bash
set -e

# python setup.py install

distsuperctl init db

exec "$@"
