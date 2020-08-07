#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script performs  data collection for Arpa.
# Furthermore, it serves as a validation framework for existing CBMC proofs.
manual_proof_override="s2n_free_object s2n_mem_cleanup s2n_pkcs3_to_dh_params s2n_stuffer_free"


function initialize {
    results=arpa-test-results.log
    arpa_log=arpa-test-logs
    t_pfs_w_unnesc=0

    rm -f $results
    tot_prfs=$(ls -l | grep -c ^d)
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


function get_fcts {
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

    # get all dependencies (except for the harness itslef and for stubs) and sort
    # the order of stubs is left intact
    all_deps=$(grep 'PROOF_SOURCES += \$(PROOF_SOURCE).*\|PROJECT_SOURCES += .*' Makefile)
    sorted_deps_std=$(sort <<< "$all_deps")
    all_stubs=$(grep 'PROOF_SOURCES += \$(PROOF_STUB).*' Makefile)

    # remove existing dependencies (including stubs) from the Makefile
    makefile_std=$(sed  -e 's-PROOF_SOURCES += \$(PROOF_.*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        Makefile)

    # divide the file at the first dependency "PROOF_SOURCES += \$(HARNESS_FILE)"
    dep_start=$(grep -n 'PROOF_SOURCES += \$(HARNESS_FILE)' <(echo "$makefile_std") | cut -f1 -d:)
    first_half=$(head -n $dep_start <(echo "$makefile_std"))
    ((dep_next=dep_start+1))
    second_half=$(tail -n +$dep_next <(echo "$makefile_std"))

    # Add the dependencies 
    add_first=""
    add_next=""
    while read -r l; do
        if grep -q "$l" <(echo "$sorted_deps_arpa"); then
            add_first+="$l\n"
        else
            add_next+="$l\n"
        fi
    done <<< "$sorted_deps_std"

    # get 
    makefile_std=$(cat <(echo "$first_half") <(echo -e "$add_first") <(echo -e "$all_stubs")  <(echo -e "$add_next")   <(echo "$second_half"))
    make goto -f <(echo "$makefile_std")
    get_fcts std
}


function make_arpa {
    make veryclean
    # NOTE: STUBS ARE LEFT INTACT
    make arpa
    get_deps arpa Makefile.arpa


    # remove includes and defines from Makefile.arpa
    # n_stubs_arpa=$(grep 'PROOF_SOURCES += $(PROOF_STUB).*' Makefile.arpa)
    # sed -i '' -e 's-DEFINES += .*--g' \
    #     -e 's-INCLUDES += .*--g' \
    #     -e 's-PROOF_SOURCES += $(PROOF_STUB).*--g' \
    #     Makefile.arpa
    sed -i '' -e 's-PROOF_SOURCES += $(PROOF_STUB).*--g' \
        Makefile.arpa
    # TODO remove STUBS from Makefile arpa? (after checking if they do exist in makefile)

    sorted_deps_arpa=$(sort Makefile.arpa) # can sort the whole file cuz only comments beside deps
    echo "$sorted_deps_arpa" > Makefile.arpa

    #store, in case fails
    comp_cmds=$(cat arpa_cmake/compile_commands.json)
    
    # get stubs from Makefile
    all_stubs=$(grep 'PROOF_SOURCES += \$(PROOF_STUB).*' Makefile)
    # get rid of alldeps (including stubs, which will be added later)
    makefile_arpa=$(sed -e 's-PROOF_SOURCES += \$(PROOF_.*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        Makefile)
    
    dep_start=$(grep -n 'PROOF_SOURCES += \$(HARNESS_FILE)' <(echo "$makefile_arpa") | cut -f1 -d:)
    first_half=$(head -n $dep_start <(echo "$makefile_arpa"))
    ((dep_next=dep_start+1))
    second_half=$(tail -n +$dep_next <(echo "$makefile_arpa"))

    makefile_arpa=$(cat  <(echo "$first_half") <(echo "include Makefile.arpa") <(echo -e "$all_stubs") <(echo "$second_half"))

    make goto -f <(echo "$makefile_arpa")

    get_fcts arpa
}


function write_failure_docs {
    mkdir -p $arpa_log
    echo "$comp_cmds" > $arpa_log/compile_commands.json
    echo "$makefile_std" > $arpa_log/Makefile-std
    echo "$sorted_deps_arpa" > $arpa_log/Makefile.arpa
    echo "$makefile_arpa" > $arpa_log/Makefile-arpa
    echo "$fcts_std_clean" > $arpa_log/goto-functions-std
    echo "$fcts_arpa_clean" > $arpa_log/goto-functions-arpa
}


function write_to_log {
    # WRITE RESULT
    echo "($cnt/$tot_prfs) - $1 - $dir" >> ../$results

    r_succ=$((n_succ * 100 / n_prfs))
    echo "  1.-SUCC RATE:#proofs=$n_prfs, #succ=$n_succ, %succ=$r_succ%" >> ../$results

    ##############################
    ### PER PROOF MEASUREMENTS
    ##############################
    common_deps=$(comm -12 <(echo "$sorted_no_stubs_arpa") <(echo "$sorted_no_stubs_std"))
    # n_deps_com=$(grep -c -v 'PROOF_SOURCES += \$(PROOF_STUB).*' <(echo "$common_deps"))
    n_deps_com=$(count_lines "$common_deps")

    # case where arpa finds correct result, with less deps
    # I CAN NEVER SAY THAT THE STUB IS UNNESC BECAUSE I AM KEEPING IT IN MAKEFILE DURING DATA GATHERING
    # I AM ASSUMING THAT ALL STUBS ARE NECESSARY
    ((n_deps_nesc=$n_deps_std-$n_stubs_std))
    if [ ! "$is_dif" ]; then
        # if SUCCESSFUL, adjust number of required deps
        n_deps_nesc=$n_deps_com
        # TODO create a list of unnecessarily included deps
    else
        # if FAILURE, add not found deps to list
        deps_not_found=$(comm -13 <(echo "$sorted_no_stubs_arpa") <(echo "$sorted_no_stubs_std"))
        while read -r l; do
            to_add="$(sed -e 's-.* += --g' <<< "$l" )"
            if [[ ! "$list_deps_arpa_cannot_find" == *"$to_add"* ]]; then
                list_deps_arpa_cannot_find+="    $to_add\n"
            fi
        done <<< "$deps_not_found"
    fi
    ((n_deps_unnesc=n_deps_std-n_stubs_std-n_deps_nesc))
    if [ $n_deps_unnesc -gt 0 ]; then
        ((t_pfs_w_unnesc=t_pfs_w_unnesc+1))
    fi

    n_add_deps=$(($n_deps_arpa-$n_deps_com))
    n_missed_deps=$(($n_deps_std-$n_deps_com))
    r_deps_found=$((n_deps_com * 100 / n_deps_nesc))

    # TODO warn if n_deps_arpa > n_deps_com
    echo "  2.-PROOF STATS : #deps-in-std=$n_deps_std ($n_stubs_std stubs, $n_deps_unnesc unnesc), #deps-in-arpa=$n_deps_arpa ($n_stubs_arpa stubs), #non-stub-deps-in-common=$n_deps_com" >> ../$results
    echo "     \-ARPA FINDS: %of-nesc-non-stub-deps=$r_deps_found% ($n_deps_com/$n_deps_nesc), #additional-deps=$n_add_deps ($n_stubs_arpa stubs)" >> ../$results

    echo "  3.- START DIFF:" >> ../$results
    dif=$(diff <(echo "$sorted_arpa") <(echo "$sorted_std"))
    sed -e 's-^-    -g' <(echo "$dif") >> ../$results
    echo "  \-- END DIFF" >> ../$results

    ##############################
    ### RUNNING TOTAL MEASUREMENTS
    ##############################
    # assuming Arpa does ot find irrelevant deps
    ((t_deps_std=t_deps_std+n_deps_std))
    ((t_stubs_std=t_stubs_std+n_stubs_std))
    ((t_deps_nesc=t_deps_nesc+n_deps_nesc))
    ((t_deps_unnesc=t_deps_unnesc+n_deps_unnesc))
    ((t_deps_arpa=t_deps_arpa+n_deps_arpa))
    ((t_deps_com=t_deps_com+n_deps_com))

    ((t_add_deps=t_add_deps+n_add_deps))
    ((t_stubs_arpa=t_stubs_arpa+n_stubs_arpa))
    r_t_deps_found=$((t_deps_com * 100 / t_deps_nesc))

    echo "  4.-TOTAL STATS : #deps-in-std=$t_deps_std ($t_stubs_std stubs, $t_deps_unnesc unnesc in $t_pfs_w_unnesc proofs), #deps-in-arpa=$t_deps_arpa, #non-stub-deps-in-common=$t_deps_com" >> ../$results
    echo "     \-ARPA FINDS: %of-nesc-non-stub-deps=$r_t_deps_found% ($t_deps_com/$t_deps_nesc), #additional-deps=$t_add_deps ($t_stubs_arpa stubs)" >> ../$results

    ##############################
    ### AVERAGE RATIO MEASUREMENTS
    ##############################
    avg_r_deps_found=$(((avg_r_deps_found * (n_prfs -1) + r_deps_found) / n_prfs))
    echo "     \-AVERAGE   : avg%deps_found_per_proof=$avg_r_deps_found%" >> ../$results

    ##############################
    ### RELEVANT LISTS
    ##############################
    echo "  5.- START DEPS_MISSED_AT_LEAST_ONCE (NOT STUBS):" >> ../$results
    echo -n -e "$list_deps_arpa_cannot_find" >> ../$results
    echo "  \-- END DEPS_MISSED_AT_LEAST_ONCE:" >> ../$results
    # echo "            -DEPS_FOUND_AT_LEAST_ONCE : " >> ../$results
    # echo "            -DEPS_IRREL_AT_LEAST_ONCE : " >> ../$results

    echo "" >> ../$results
}


function compare_and_report {

    # compare functions list
    overwrite=""
    is_dif=$(diff -q <(echo "$fcts_std_clean") \
        <(echo "$fcts_arpa_clean"))

    # Ask user to MANUALLY confirm if result is correct
    if [ "$is_dif" ]; then
        if [[ "$overwrite_files" == *"$dir"* ]]; then
            is_dif=""
            overwrite="yes"
        fi

        # DONE MANUALLY
        # echo -e "\n----- Here is the goto functions diff -----\n"
        # diff <(echo "$fcts_std_clean") <(echo "$fcts_arpa_clean")
        # echo -e "\n----- OVERWRITE? consider as a SUCCESS? -----"
        # read overwrite
        # if [ "$overwrite" ]; then
        #     is_dif=""
        # fi
    fi
    # END TODO

    # report
    ((n_prfs=n_prfs+1))
    echo -n "< END - "
    if [ "$is_dif" ]; then
        # goto functions are different
        echo -n "(DIFFERENT)"
        write_to_log FAILURE
        write_failure_docs
    else
        # goto functions are identical
        ((n_succ=n_succ+1))
        echo -n "(IDENTICAL)"
        if [ "$overwrite" ]; then
            write_to_log SUCCESS-OVERWRITE
            write_failure_docs
        else
            write_to_log SUCCESS
        fi
        
        
    fi
    echo " >"
    # echo "$deps_arpa"
}


# MAIN
initialize
for dir in s2n_blob_char_to_lower s2n_align_to; do
    if [ ! -d $dir ]; then
        continue
    fi
    ((cnt=cnt+1))

    cd $dir
    harness="$dir"_harness.c
    echo -e "\n< BEGIN - ($dir) >"

    # check if required files exist
    look_for Makefile
    look_for $harness

    # define fcts_arpa_clean
    echo "-- Listing goto functions for ARPA approach"
    make_arpa > /dev/null

    # define fcts_std_clean
    echo "-- Listing goto functions for STANDARD approach"
    make_std > /dev/null

    # compare goto functions
    echo "-- Comparing results and writing report"
    compare_and_report

    # clean up
    make veryclean > /dev/null
    cd ..
done 

