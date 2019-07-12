#! /bin/bash

REBUILD=${1}

eval "$(conda shell.bash hook)"

if [[ -z "$(conda env list | grep cert-service)" ]] || [[ -n "${REBUILD}" ]]
then
  conda create -n cert-service -c conda-forge -y python=3.7 pyaml=19.4.1

  conda activate cert-service

  conda install -y conda-build

  packages=$(conda render . --file render.yaml 2>&1 >/dev/null && cat render.yaml | python -c "import sys; import yaml; print(' '.join(yaml.load(sys.stdin, Loader=yaml.FullLoader)['requirements']['run']))")

  rm render.yaml

  conda install -c conda-forge -c cdat -y ${packages} mongodb redis
fi

if [[ "${CONDA_DEFAULT_ENV}" != "cert-service" ]]
then
  conda activate cert-service
fi

mkdir -p ${PWD}/data

mongod --dbpath ${PWD}/data 2>&1 > mongodb.log &

redis-server 2>&1 > redis.log &

DEV=1 celery -A certification_service.tasks worker -c 2 -l DEBUG -B 2>&1 &

function cleanup {
  killall mongod
  killall redis-server
  killall celery
}

trap cleanup SIGINT SIGTERM EXIT

DEV=1 python -m certification_service.main
