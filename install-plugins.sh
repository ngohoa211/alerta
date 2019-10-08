#!/bin/bash

while read plugin ; do
  echo "Installing '${plugin}' "
  cd /source/alerta-contrib/${plugin}
  python3 setup.py install
done </app/plugins.txt
