#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script performs validation for arpa

makefile=Makefile
results=arpa-test-results.log
csv=arpa-test-results.csv

arpa_log=arpa-test-logs
goto_functions_std=$arpa_log/goto-functions-std
goto_functions_arpa=$arpa_log/goto-functions-arpa

#data collection
n_prfs=0
n_succ=0

t_deps_std=0 # sum of all n_deps_std
t_deps_arpa=0 # sum of all n_deps_arpa

avg_r_deps_proof=0

list_deps_arpa_cannot_find+="" 
list_deps_arpa_has_found_at_least_once+=""
list_deps_that_currently_exist_but_are_irrelevant+="" # case where arpa finds less deps but diff of show_goto_functions is the same


function initialize {
        rm -f $results
}


function look_for {
    if [ ! -f $1 ]; then
        echo "-- $1 does not exist in ($dir)." 1>&2
        echo "<SKIPPING>" 1>&2
        cd ..
        echo "ERROR  -  $dir" >> $results
        continue
    fi
}


function get_fcts {
    goto_fcts=$(cbmc --show-goto-functions gotos/$harness.goto)
    # eval fcts_$1="\$goto_fcts"
    clean_goto_fcts=$(grep -v " *//.*" <<< "$goto_fcts")
    eval fcts_$1_clean="\$clean_goto_fcts"
}


function get_deps {
    grep_out=$(grep 'PROOF_SOURCES += \$(PROOF_SOURCE).*\|PROJECT_SOURCES += .*' $2)
    eval deps_$1="\$grep_out"
    eval n_deps_$1=$(wc -l <<< "$grep_out" | tr -d " ")
}


function make_std {
    make veryclean
    make goto

    get_fcts std
    get_deps std Makefile
}


function make_arpa {
    make veryclean
    make arpa
    # remove includes and defines from Makefile.arpa
    sed -i '' -e 's-DEFINES += .*--g' \
        -e 's-INCLUDES += .*--g' \
        Makefile.arpa

    makefile_temp=$(sed -e 's-PROOF_SOURCES += \$(PROOF_SOURCE).*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        -e 's-include ../Makefile.common-include Makefile.arpa\'$'\ninclude ../Makefile.common-g'\
        $makefile)
    # TODO put iclude arpa after PROOF_SOURCES += $(HARENSS_FILE)

    make goto -f <(echo "$makefile_temp")

    get_fcts arpa
    get_deps arpa Makefile.arpa
}


function write_failure_docs {
    mkdir -p $arpa_log
    cp Makefile.arpa $arpa_log
    cp arpa_cmake/compile_commands.json $arpa_log
    echo "$fcts_std_clean" > $goto_functions_std
    echo "$fcts_arpa_clean" > $goto_functions_arpa
}


function write_to_log {
    # WRITE RESULT
    echo "$1  -  $dir" >> ../$results


    r_succ=$((n_succ * 100 / n_prfs))
    echo "    \-SUCC RATE:#proofs=$n_prfs, #succ=$n_succ, %succ=$r_succ%" >> ../$results

    ##############################
    ### PER PROOF MEASUREMENTS
    ##############################
    if [ "$is_dif" ]; then
        # we assume that all included dependencies are required
        # we assume that arpa does not find any irrelevant dependencies
        n_deps_irrelevant=0
        n_deps_missing=$((n_deps_std-n_deps_arpa))

        not_found="$(comm -13 <(sort <<< "$deps_arpa") <(sort <<< "$deps_std"))"
        while read -r l; do
            to_add="$(sed -e 's-PROJECT_SOURCES += --g' <<< "$l" )"
            if [[ ! "$list_deps_arpa_cannot_find" == *"$to_add"* ]]; then
                list_deps_arpa_cannot_find+="$to_add"
                list_deps_arpa_cannot_find+=", "
            fi
        done <<< "$not_found"
    else
        n_deps_irrelevant=$((n_deps_std-n_deps_arpa))
        n_deps_missing=0
    fi

    if [ $n_deps_irrelevant -lt 0 ]; then
        #found a stub!!!
        n_stubs=$((0 - n_deps_irrelevant))

        #### ASSUMPTION: the STUBS directory is a recursive subdirectory of the PROOF_SOURCE directory
        echo "     -(ARPA has found ($n_stubs) STUBS!)" >> ../$results
        n_deps_arpa=$((n_deps_std))
        n_deps_irrelevant=0
    fi
    n_deps_relevant=$((n_deps_std-n_deps_irrelevant))
    # r_deps_proof=$((n_deps_arpa * 100 / n_deps_relevant))


    echo "    \-PROOF -STD : #deps_incl=$n_deps_std, #deps_irrelevant=$n_deps_irrelevant, #deps_relevant=$n_deps_relevant" >> ../$results
    echo "            -ARPA: #deps_found=$n_deps_arpa, #missing_deps=$n_deps_missing, %relevant_deps_found=$r_deps_proof%" >> ../$results

    ##############################
    ### TOTAL MEASUREMENTS
    ##############################
    # assuming Arpa does ot find irrelevant deps
    ((t_deps_std=t_deps_std+n_deps_std))
    ((t_deps_arpa=t_deps_arpa+n_deps_arpa))

    t_deps_irrelevant=$((t_deps_irrelevant+n_deps_irrelevant))
    t_deps_relevant=$((t_deps_std-t_deps_irrelevant))
    t_deps_missing=$((t_deps_missing+n_deps_missing))

    r_deps_total=$((t_deps_arpa * 100 / t_deps_relevant))
    echo "    \-TOTAL -STD : #deps_incl=$t_deps_std, #deps_irrelevant=$t_deps_irrelevant, #deps_relevant=$t_deps_relevant" >> ../$results
    echo "            -ARPA: #deps_found=$t_deps_arpa, #missing_deps=$t_deps_missing, %relevant_deps_found=$r_deps_total%" >> ../$results

    ##############################
    ### AVERAGE RATIO MEASUREMENTS
    ##############################
    avg_r_deps_proof=$(((avg_r_deps_proof * (n_prfs -1) + r_deps_proof) / n_prfs))
    echo "    \-AVERAGE    : avg%deps_found_per_proof=$avg_r_deps_proof%" >> ../$results

    ##############################
    ### RELEVANT LISTS
    ##############################

    echo "    \-LISTS -DEPS_MISSED_AT_LEAST_ONCE: $list_deps_arpa_cannot_find" >> ../$results
    # echo "            -DEPS_FOUND_AT_LEAST_ONCE : " >> ../$results
    # echo "            -DEPS_IRREL_AT_LEAST_ONCE : " >> ../$results

    echo "" >> ../$results
}


function compare_and_report {
    # write csv header
    echo "Proof,Success?,#deps-std,#deps-arpa,#deps-common" > ../$csv

    # compare functions list
    is_dif=$(diff -q <(echo "$fcts_std_clean") \
        <(echo "$fcts_arpa_clean"))

    # report
    ((n_prfs=n_prfs+1))
    echo -n "<END - "
    if [ "$is_dif" ]; then
        # goto functions are different
        echo -n "(DIFFERENT)"
        write_to_log FAILURE
        write_failure_docs
    else
        # goto functions are identical
        ((n_succ=n_succ+1))
        echo -n "(IDENTICAL)"
        write_to_log SUCCESS
    fi
    echo " >"
    # echo "$deps_arpa"
}


# MAIN
initialize
for dir in s2n_stuffer_write_uint32; do
    if [ ! -d $dir ]; then
        continue
    fi

    cd $dir
    harness="$dir"_harness.c
    echo -e "\n<BEGIN - ($dir) >"

    # check files
    look_for $makefile
    look_for $harness

    # define fcts_std_clean
    echo "-- Listing goto functions for STANDARD approach"
    make_std > /dev/null

    # define fcts_arpa_clean
    echo "-- Listing goto functions for ARPA approach"
    make_arpa > /dev/null

    # compare goto functions
    echo "-- Comparing results and writing report"
    compare_and_report

    # clean up
    make veryclean > /dev/null
    cd ..
done
