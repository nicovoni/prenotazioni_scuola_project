#!/usr/bin/env bash
# Script helper to run the send_test_pin management command inside the web service container
# Usage: ./scripts/run-in-docker.sh i.nizzo@isufol.it

if [ -z "$1" ]; then
  echo "Usage: $0 recipient_email"
  exit 1
fi

RECIPIENT=$1

echo "Running send_test_pin for $RECIPIENT inside docker-compose web service"

docker-compose run --rm web python manage.py send_test_pin "$RECIPIENT"
