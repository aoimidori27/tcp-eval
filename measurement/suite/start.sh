#!/bin/bash

USAGE="Usage: $0 [init|measure|analyze] [folder] [offset]"

if [ $# -lt 3 ]; then
    echo $USAGE
    exit 1
fi
FOLDER=$2
OFFSET=$3
LOG=$FOLDER/measurement.log

MEASUREMENTS="suite2.1.1_delay40_nots
suite2.1.2_delay40_nots-ackloss
suite2.1.2_delay40_nots-ackreor-ackloss
suite2.1.2_delay40_nots-ackreor
suite2.1.2_delay40_nots-reor-ackloss
suite2.1.2_delay40_nots-reor-ackreor-ackloss
suite2.1.2_delay40_nots-reor-ackreor
suite2.1.2_delay40_nots-reor
suite2.2.1_delay40_nots-ackloss
suite2.2.1_delay40_nots-ackreor-ackloss
suite2.2.1_delay40_nots-ackreor
suite2.2.1_delay40_nots-reor-ackloss
suite2.2.1_delay40_nots-reor-ackreor-ackloss
suite2.2.1_delay40_nots-reor-ackreor
suite2.2.1_delay40_nots-reor
suite2.2.2_delay40_nots-ackloss
suite2.2.2_delay40_nots-ackreor-ackloss
suite2.2.2_delay40_nots-ackreor
suite2.2.2_delay40_nots
suite2.2.2_delay40_nots-reor-ackloss
suite2.2.2_delay40_nots-reor-ackreor-ackloss
suite2.2.2_delay40_nots-reor-ackreor
suite2.2.2_delay40_nots-reor
suite2.3.1_delay40_nots-ackloss
suite2.3.1_delay40_nots-ackreor-ackloss
suite2.3.1_delay40_nots-ackreor
suite2.3.1_delay40_nots
suite2.3.2_delay40_nots-ackloss
suite2.3.2_delay40_nots-ackreor-ackloss
suite2.3.2_delay40_nots-ackreor
suite2.3.2_delay40_nots
suite2.4.1_delay40_nots-ackreor-ackloss
suite2.4.1_delay40_nots-ackreor
suite2.4.1_delay40_nots-reor-ackloss
suite2.4.1_delay40_nots-reor-ackreor-ackloss
suite2.4.1_delay40_nots-reor-ackreor
suite2.4.1_delay40_nots-reor
suite2.4.2_delay40_nots-ackreor-ackloss
suite2.4.2_delay40_nots-ackreor
suite2.4.2_delay40_nots-reor-ackloss
suite2.4.2_delay40_nots-reor-ackreor-ackloss
suite2.4.2_delay40_nots-reor-ackreor
suite2.4.2_delay40_nots-reor
suite2.5.1_delay40_nots-ackloss
suite2.5.1_delay40_nots
suite2.5.1_delay40_nots-reor-ackloss
suite2.5.1_delay40_nots-reor
suite2.5.2_delay40_nots-ackloss
suite2.5.2_delay40_nots
suite2.5.2_delay40_nots-reor-ackloss
suite2.5.2_delay40_nots-reor
suite2.5.3_delay40_nots-ackreor
suite2.5.3_delay40_nots
suite2.5.3_delay40_nots-reor-ackreor
suite2.5.3_delay40_nots-reor
suite2.5.4_delay40_nots-ackreor
suite2.5.4_delay40_nots
suite2.5.4_delay40_nots-reor-ackreor
suite2.5.4_delay40_nots-reor"

if [ "$1" = "init" ]; then
	echo -e "starting vmrouter\n=========================" | tee $LOG
	./config/start_dumbbell.pl restart $OFFSET | tee -a $LOG
	echo -e "\nexecuting um_vmesh\n=========================" | tee -a $LOG
	um_vmesh -u -s -q -o $OFFSET config/dumbbell.conf 2>&1 | tee -a $LOG
fi

if [ "$1" = "measure" ]; then
	echo -e "\nmeasurements\n=========================" | tee -a $LOG
    for measurement in `echo $MEASUREMENTS`;
    do
        echo -e "----- measurement: $FOLDER/$measurement ------" | tee -a $LOG
	    ./config/$measurement.py -o $OFFSET -L $FOLDER/${measurement} 2>&1 | tee -a $LOG
    done
fi

if [ "$1" = "analyze" ]; then
	echo -e "\ncreating pdf\n=========================" | tee -a $LOG
    for measurement in `echo $MEASUREMENTS`;
    do
        echo -e "----- analyze: $FOLDER/$measurement ------" | tee -a $LOG
	    cd $FOLDER/${measurement}
        #rm data.sqlite
	    vmesh_dumbbell_flowgrind_analysis.py -V bnbw    -T congestion -O pdf

        vmesh_dumbbell_flowgrind_analysis.py -V rrate   -T reordering -O pdf
	    vmesh_dumbbell_flowgrind_analysis.py -V rdelay  -T reordering -O pdf

        vmesh_dumbbell_flowgrind_analysis.py -V bnbw    -T both       -O pdf
	    vmesh_dumbbell_flowgrind_analysis.py -V rrate   -T both       -O pdf
        vmesh_dumbbell_flowgrind_analysis.py -V rdelay  -T both       -O pdf

        cd ../..
    done
fi

if [ "$1" != "init" ] && [ "$1" != "measure" ] && [ "$1" != "analyze" ]; then
	echo $USAGE
fi
