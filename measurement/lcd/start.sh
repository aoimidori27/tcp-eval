#!/bin/bash

USAGE="Usage: $0 [init|measure|analyze] [folder] [offset]"

if [ $# -lt 3 ]; then
    echo $USAGE
    exit 1
fi
FOLDER=$2
OFFSET=$3
LOG=$FOLDER/measurement.log

MEASUREMENTS="measurement1" # insert measurement names here.
                            # for measurement1 the script located at config/measurement1.py is called
                            # the results of this measurement are then saved to $FOLDER/measurement1/

if [ "$1" = "init" ]; then
	echo -e "starting vmrouter\n=========================" | tee $LOG
	./config/start_dumbbell.pl restart $OFFSET | tee -a $LOG
	echo -e "\nexecuting um_vmesh\n=========================" | tee -a $LOG
	um_vmesh -u -s -q -o --userscripts-path=./config $OFFSET config/dumbbell.conf 2>&1 | tee -a $LOG
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
        rm data.sqlite
	    #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V bnbw    -T congestion -O pdf -E
	    #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V delay   -T congestion -O pdf -E

        #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V rrate   -T reordering -O pdf -E
	    ~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V rdelay  -T reordering -O pdf -E
	    #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V delay   -T reordering -O pdf -E
	    #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V ackloss -T reordering -O pdf -E
	    #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V ackreor -T reordering -O pdf -E

        ~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V bnbw    -T both       -O pdf -E
	    ~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V rrate   -T both       -O pdf -E
        #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V rdelay  -T both       -O pdf -E
        #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V delay   -T both       -O pdf -E
        #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V ackloss -T both       -O pdf -E
        #~/checkout/scripts/analysis/vmesh_dumbbell_flowgrind_analysis.py -V ackreor -T both       -O pdf -E
        cd -
    done
fi

if [ "$1" != "init" ] && [ "$1" != "measure" ] && [ "$1" != "analyze" ]; then
	echo $USAGE
fi
