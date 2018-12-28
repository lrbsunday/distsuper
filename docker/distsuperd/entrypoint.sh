#!/bin/bash
set -e

# python setup.py install

while ! nc -z database 3306;
distsuperctl init db

exec "$@"
