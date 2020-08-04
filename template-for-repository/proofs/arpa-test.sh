#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script performs validation for arpa

makefile=Makefile
results=arpa-test-results.log
csv=arpa-test-results.csv

arpa_log=arpa-test-logs
makefile_std_save=$arpa_log/$makefile
goto_functions_std=$arpa_log/goto-functions-std
goto_functions_arpa=$arpa_log/goto-functions-arpa

#data collection

list_deps_arpa_cannot_find+="" 
# list_deps_arpa_has_found_at_least_once+=""
# list_deps_that_currently_exist_but_are_irrelevant+="" # case where arpa finds less deps but diff of show_goto_functions is the same


function initialize {
    t_pfs_w_unnesc=0
    rm -f $results
    tot_prfs=$(ls -l | grep -c ^d)
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


function count_lines {
    wc -l <<< "$1" | tr -d " "
}


function get_deps {
    grep_out=$(grep 'PROOF_SOURCES += \$(PROOF_.*\|PROJECT_SOURCES += .*' $2)
    eval deps_$1="\$grep_out"
    n_deps=$(count_lines "$grep_out")
    eval n_deps_$1="\$n_deps"
    sorted=$(sort <<< "$grep_out")
    eval sorted_$1="\$sorted"
    sorted_no_stubs=$(grep -v 'PROOF_SOURCES += \$(PROOF_STUB).*' <(echo "$sorted"))
    eval sorted_no_stubs_$1="\$sorted_no_stubs"
    n_non_stubs=$(count_lines "$sorted_no_stubs") 
    ((n_stubs=$n_deps-$n_non_stubs))
    eval n_stubs_$1="\$n_stubs"
    #in the sorted version, stubs are the last in line
}


function make_std {
    make veryclean
    #get all dependencies and sort
    all_deps=$(grep 'PROOF_SOURCES += \$(PROOF_.*\|PROJECT_SOURCES += .*' $makefile)
    sorted_deps=$(sort <<< "$all_deps")

    # remove existing depenedencies
    makefile_std=$(sed -e 's-PROOF_SOURCES += \$(PROOF_.*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        $makefile)
    #add sorted deps to beginning of file
    makefile_std=$(cat <(echo "$sorted_deps") <(echo "$makefile_std"))

    make goto -f <(echo "$makefile_std")

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

    sorted_deps=$(sort Makefile.arpa) # can sort the whole file cuz only comments beside deps
    echo "$sorted_deps" > Makefile.arpa
    
    # do not get rid of stubs
    makefile_arpa=$(sed -e 's-PROOF_SOURCES += \$(PROOF_SOURCE).*--g' \
        -e 's-PROJECT_SOURCES += .*--g' \
        $makefile)
    makefile_arpa=$(cat <(echo "include Makefile.arpa") <(echo "$makefile_arpa"))

    make goto -f <(echo "$makefile_arpa")

    get_fcts arpa
    get_deps arpa Makefile.arpa
}


function write_failure_docs {
    mkdir -p $arpa_log
    cp Makefile.arpa $arpa_log
    cp arpa_cmake/compile_commands.json $arpa_log
    echo "$makefile_std" > $makefile_std_save-std
    echo "$makefile_arpa" > $makefile_std_save-arpa
    echo "$fcts_std_clean" > $goto_functions_std
    echo "$fcts_arpa_clean" > $goto_functions_arpa
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
    n_deps_nesc=$n_deps_std-n_stubs_std
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

    echo "  4.-TOTAL STATS : #deps-in-std=$t_deps_std ($t_stubs_std stubs, $t_deps_unnesc unnesc, in $t_pfs_w_unnesc proofs), #deps-in-arpa=$t_deps_arpa, #non-stub-deps-in-common=$t_deps_com" >> ../$results
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
        write_failure_docs
    fi
    echo " >"
    # echo "$deps_arpa"
}


# MAIN
initialize
for dir in *; do
    if [ ! -d $dir ]; then
        continue
    fi
    ((cnt=cnt+1))

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
