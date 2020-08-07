#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script performs  data collection for Arpa.
# Furthermore, it serves as a validation framework for existing CBMC proofs.

# TODO add project-specific list of proofs that fail, but should be overriden due to limitations of the validation approach
manual_proof_override=""


function initialize {
    # variable initializations
    results=arpa-test-results.log
    arpa_log=arpa-test-logs
    t_pfs_w_unnesc=0
    tot_prfs=$(ls -l | grep -c ^d)

    # remove existing results
    rm -f $results

    # consider command-line flag
    if [[ "$1" == "-mo" || "$1" == "--manual-override" ]]; then

        echo -e "\n<MANUAL OVERRIDING ENABLED>"
        manual_override_flag=1
    fi
}


function look_for {
    if [ ! -f $1 ]; then
        echo "-- $1 does not exist in ($dir)." 1>&2
        echo "< SKIPPING >" 1>&2
        cd ..
        echo "($cnt/$tot_prfs) - ERROR - $dir" >> $results
        echo -e "  0.- $1 does not exist in ($dir)\n" >> $results
        continue
    fi
}


function proof_init {
    # proof-specific initialisations
    cd $dir
    harness="$dir"_harness.c
    rm -r -f $arpa_log
    echo -e "\n<($cnt/$tot_prfs)-BEGIN-($dir)>"

    # check if required files exist
    look_for Makefile
    look_for $harness
}


function get_fcts {
    # this function gets the goto functions relevant to the CBMC proof
    # and store it in a variable
    goto_fcts=$(cbmc --show-goto-functions gotos/$harness.goto)

    # get rid of comments
    clean_goto_fcts=$(grep -v " *//.*" <<< "$goto_fcts")
    eval fcts_$1_clean="\$clean_goto_fcts"
}


function count_lines {
    wc -l <<< "$1" | tr -d " "
}


function get_deps {
    #this function defines variables for numeric evaluation at a later stage

    # we consider all dependencies except the harness file itself
    grep_out=$(grep 'PROOF_SOURCES += \$(PROOF_.*\|PROJECT_SOURCES += .*' $2)
    eval deps_$1="\$grep_out"
    n_deps=$(count_lines "$grep_out")
    eval n_deps_$1="\$n_deps"

    # we sort the dependencies as we perform a diff between approaches later on
    sorted=$(sort <<< "$grep_out")
    eval sorted_$1="\$sorted"

    # we remove stubs, as they are not expected to be found by arpa
    sorted_no_stubs=$(grep -v 'PROOF_SOURCES += \$(PROOF_STUB).*' <(echo "$sorted"))
    eval sorted_no_stubs_$1="\$sorted_no_stubs"
    n_non_stubs=$(count_lines "$sorted_no_stubs") 
    ((n_stubs=$n_deps-$n_non_stubs))
    eval n_stubs_$1="\$n_stubs"
}


function make_std {
    make veryclean
    get_deps std Makefile

    # get goto functions that are being tested
    make goto -f Makefile
    get_fcts std
}


function make_arpa {
    make veryclean
    make arpa
    get_deps arpa Makefile.arpa

    # remove all dependencies (except stubs) from the current makefile
    # and add the "include Makefile.arpa" line
    makefile_for_arpa=$(sed -e 's-PROOF_SOURCES += \$(PROOF_SOURCE).*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        -e 's-include ../Makefile.common-include Makefile.arpa\'$'\ninclude ../Makefile.common-g'\
        Makefile)

    # get goto functions that are being tested
    make goto -f <(echo "$makefile_for_arpa")
    get_fcts arpa
}


function write_failure_docs {
    mkdir -p $arpa_log
    # documents related to the standard approach
    cp Makefile $arpa_log/Makefile-for-std
    echo "$fcts_std_clean" > $arpa_log/goto-functions-for-std
    # documents related to the arpa approach
    cp arpa_cmake/compile_commands.json $arpa_log
    cp Makefile.arpa $arpa_log
    echo "$makefile_for_arpa" > $arpa_log/Makefile-for-arpa
    echo "$fcts_arpa_clean" > $arpa_log/goto-functions-for-arpa
}


function write_success_rate {
    r_succ=$((n_succ * 100 / n_prfs))
    echo "  1.-SUCC RATE:#proofs=$n_prfs, #succ=$n_succ, %succ=$r_succ%"
}


function write_proof_stats {

    # get a list of common dependencies for both approaches (with/without arpa)
    common_deps=$(comm -12 <(echo "$sorted_no_stubs_arpa") <(echo "$sorted_no_stubs_std"))
    n_deps_com=$(count_lines "$common_deps")

    # necessary dependencies do not include stubs
    ((n_deps_nesc=$n_deps_std-$n_stubs_std))
    if [ ! "$failure" ]; then
        # if the diff is IDENTICAL, this means that the dependencies specified
        # in bth approaches are necessary and any other dependencies used only
        # in the standard approach are unnecessary
        n_deps_nesc=$n_deps_com
    else
        # if the diff is DIFFERENT, we assume that arpa is missing some dependencies
        deps_not_found=$(comm -13 <(echo "$sorted_no_stubs_arpa") <(echo "$sorted_no_stubs_std"))
        while read -r l; do
            to_add="$(sed -e 's-.* += --g' <<< "$l" )"
            if [[ ! "$list_deps_arpa_cannot_find" == *"$to_add"* ]]; then
                list_deps_arpa_cannot_find+="    $to_add\n"
            fi
        done <<< "$deps_not_found"
        # DISCLAIMER: known limitation
        # there are cases where the existing Makefile contains a necessary dependency X and an unnecessary dependency Y
        # if arpa is able to find Y but unable to find X, this validation script will consider that arpa is unable to find 
        # both X and Y because the diff is DIFFERENT.
    fi

    # unnecessary dependencies do not include stubs
    ((n_deps_unnesc=n_deps_std-n_stubs_std-n_deps_nesc))
    if [ $n_deps_unnesc -gt 0 ]; then
        ((t_pfs_w_unnesc=t_pfs_w_unnesc+1))
    fi

    n_add_deps=$(($n_deps_arpa-$n_deps_com))
    n_missed_deps=$(($n_deps_std-$n_deps_com))
    r_deps_found=$((n_deps_com * 100 / n_deps_nesc))

    echo "  2.-PROOF STATS : #deps-in-std=$n_deps_std ($n_stubs_std stubs, $n_deps_unnesc unnesc), #deps-in-arpa=$n_deps_arpa ($n_stubs_arpa stubs), #non-stub-deps-in-common=$n_deps_com"
    echo "    \-ARPA FINDS: %of-nesc-non-stub-deps=$r_deps_found% ($n_deps_com/$n_deps_nesc), #additional-deps=$n_add_deps ($n_stubs_arpa stubs)"
}


function write_diff {
    echo "  3.- START DIFF:"
    dif=$(diff <(echo "$sorted_arpa") <(echo "$sorted_std"))
    sed -e 's-^-    -g' <(echo "$dif")
    echo "    \-- END DIFF"
}


function write_total_stats {
    # measure running totals and output the relevant values

    # simple running totals measurements
    ((t_deps_std=t_deps_std+n_deps_std))
    ((t_stubs_std=t_stubs_std+n_stubs_std))
    ((t_deps_nesc=t_deps_nesc+n_deps_nesc))
    ((t_deps_unnesc=t_deps_unnesc+n_deps_unnesc))

    ((t_deps_arpa=t_deps_arpa+n_deps_arpa))
    ((t_deps_com=t_deps_com+n_deps_com))
    ((t_add_deps=t_add_deps+n_add_deps))
    ((t_stubs_arpa=t_stubs_arpa+n_stubs_arpa))

    # total percentage of non-stub necessary dependencies found by arpa
    r_t_deps_found=$((t_deps_com * 100 / t_deps_nesc))
    echo "  4.-TOTAL STATS : #deps-in-std=$t_deps_std ($t_stubs_std stubs, $t_deps_unnesc unnesc in $t_pfs_w_unnesc proofs), #deps-in-arpa=$t_deps_arpa, #non-stub-deps-in-common=$t_deps_com"
    echo "    \-ARPA FINDS: %of-nesc-non-stub-deps=$r_t_deps_found% ($t_deps_com/$t_deps_nesc), #additional-deps=$t_add_deps ($t_stubs_arpa stubs)"
    
    # average percentage of non-stub dependencies found by arpa per proof
    avg_r_deps_found=$(((avg_r_deps_found * (n_prfs -1) + r_deps_found) / n_prfs))
    echo "    \-AVERAGE   : avg%deps_found_per_proof=$avg_r_deps_found%"
}


function write_missing_deps {
    echo "  5.- START DEPS_MISSED_AT_LEAST_ONCE (NOT STUBS):"
    echo -n -e "$list_deps_arpa_cannot_find"
    echo "    \-- END DEPS_MISSED_AT_LEAST_ONCE"
}

function write_overriden_proofs {
    echo "  6.- START PROOFS_OVERRIDEN_SO_FAR:"
    echo -n -e "$overriden_proofs"
    echo "    \-- END PROOFS_OVERRIDEN_SO_FAR"
}


function write_to_log {
    # general info
    echo "($cnt/$tot_prfs) - $1 - $dir" >> ../$results
    write_success_rate >> ../$results

    # proof-specific results
    write_proof_stats >> ../$results
    write_diff >> ../$results

    # total results so far
    write_total_stats >> ../$results
    write_missing_deps >> ../$results
    write_overriden_proofs >> ../$results

    echo "" >> ../$results
}


function ask_override {
    # Overriding can either be done:

    # manually ...
    if [[ "$manual_override_flag" ]]; then
        # print the diff to stdout, user may decide to override accordingly
        echo -e "\n----- Here is the goto functions diff -----\n"
        diff <(echo "$fcts_std_clean") <(echo "$fcts_arpa_clean")
        echo ""

        # The above lines may be replaced by the line below, for vs code users
        # code --diff $arpa_log/goto-functions-for-arpa $arpa_log/goto-functions-for-std

        while true; do
            read -p "Do you wish to OVERRIDE? " override
            case $override in
                [YyNn]* ) return;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    fi

    # ... or automatically.
    if [[ "$manual_proof_override" == *"$dir"* ]]; then
        override="y"
        return
    else
        override="n"
        return
    fi
}


function compare_and_report {
    # COMPARE FUNCTIONS
    override=""
    failure=$(diff -q <(echo "$fcts_std_clean") \
        <(echo "$fcts_arpa_clean"))

    # REPORT RESULTS
    ((n_prfs=n_prfs+1))
    if [ ! "$failure" ]; then
        ((n_succ=n_succ+1))
        echo "<($cnt/$tot_prfs)-END-(IDENTICAL)>"
        write_to_log SUCCESS
    else
        echo "<($cnt/$tot_prfs)-END-(DIFFERENT)>"
        write_failure_docs
        # users may override failures.
        # This option exists to assess some limitations of this approach.
        ask_override

        if [[ "$override" == [Yy]* ]]; then
            ((n_succ=n_succ+1))
            failure=""
            echo "<CORRECTION-(OVERRIDEN)>"
            overriden_proofs+="    $dir\n"
            write_to_log SUCCESS-OVERRIDE
        else
            not_overriden_proofs+="$dir "
            write_to_log FAILURE
        fi
    fi
}


# MAIN
initialize $1
for dir in *; do
    if [ ! -d $dir ]; then
        continue
    fi
    ((cnt=cnt+1))

    # proof-specific initializations and checks
    proof_init
    
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
