#! /bin/bash

if [[ "${CONDA_DEFAULT_ENV}" != "cert-service" ]]
then
  if [[ -z "$(conda env list | grep cert-service)" ]]
  then
    echo "Missing cert-service, run the scripts/development.sh script"

    exit 1
  else
    conda activate cert-service
  fi
fi

conda install -c conda-forge -y pytest pytest-mock

mkdir -p ${PWD}/data

mongod --dbpath ${PWD}/data 2>&1 > mongodb.log &

pytest
