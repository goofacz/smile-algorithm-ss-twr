#!/bin/bash

source ../../../smile/scripts/run_simulation_common.sh

opp_run -m \
        -n ..:../../src:../../../inet/src:../../../inet/examples:../../../inet/tutorials:../../../inet/showcases:../../../smile/simulations:../../../smile/src --image-path=../../../inet/images \
        -l ../../src/smile-algorithm-ss-twr \
        -l ../../../inet/src/INET \
        -l ../../../smile/src/smile omnetpp.ini \
        -u $UI_MODE \
        -c $CONFIG_NAME
