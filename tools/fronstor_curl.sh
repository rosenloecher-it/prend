#!/usr/bin/env bash

curl -Ss http://192.168.12.42/solar_api/v1/GetStorageRealtimeData.cgi?Scope=System

echo -e "\n#"$?