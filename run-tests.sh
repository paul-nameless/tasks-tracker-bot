#!/bin/bash

docker-compose -f docker-compose-tests.yml up --abort-on-container-exit --exit-code-from tests --force-recreate
docker-compose -f docker-compose-tests.yml down
