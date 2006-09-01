#!/bin/bash

while ((1)); do
	ping -c 1 meshserver &>/dev/null && echo Piep
	sleep 15
done >/dev/watchdog
