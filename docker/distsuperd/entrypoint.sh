#!/bin/bash
set -e

# python setup.py install

while ! nc -z database 3306; do echo waiting...; sleep 1; done
distsuperctl init db

exec "$@"
