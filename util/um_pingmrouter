#!/bin/bash

ALIVE=0
NODES=40

for ((i=1; i<=$NODES; i++)); do
    echo -en "\033[00m mrouter$i:"
    if ping -q -c 1 mrouter$i >/dev/null 2>/dev/null; then
        echo -e "\033[01;32m online"
        ((ALIVE++));
    else
        echo -e "\033[01;31m offline"
    fi
done

echo -e "\033[00m Summary: $ALIVE of $NODES mrouter answered a ping."
