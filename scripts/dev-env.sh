#! /bin/bash

REBUILD=${1}

eval "$(conda shell.bash hook)"

if [[ -z "$(conda env list | grep cert-service)" ]] || [[ -n "${REBUILD}" ]]
then
  conda create -n cert-service -c conda-forge -y python=3.7 pyaml=19.4.1

  conda activate cert-service

  packages=$(conda render . --file render.yaml 2>&1 >/dev/null && cat render.yaml | python -c "import sys; import yaml; print(' '.join(yaml.load(sys.stdin, Loader=yaml.FullLoader)['requirements']['run']))")

  conda install -c conda-forge -c cdat -y ${packages} mongodb redis
fi

if [[ "${CONDA_DEFAULT_ENV}" != "cert-service" ]]
then
  conda activate cert-service
fi

mkdir -p ${PWD}/data

mongod --dbpath ${PWD}/data 2>&1 > mongodb.log &

redis-server 2>&1 > redis.log &

celery -A certification_service.tasks worker -c 2 -l DEBUG -B 2>&1 &

trap "kill -2 $(jobs -pr)" SIGINT SIGTERM EXIT

python -m certification_service.service
