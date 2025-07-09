#!/bin/bash
temporal operator nexus endpoint create \
  --name weather-service \
  --target-namespace default \
  --target-task-queue weather-service \
  --description-file endpoint_description.md