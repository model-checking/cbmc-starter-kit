#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script performs  data collection for Arpa.
# Furthermore, it serves as a validation framework for existing CBMC proofs.
# TODO _ remove for s2n
manual_proof_override="s2n_blob_zeroize_free  s2n_free  s2n_free_object  s2n_pkcs3_to_dh_params  s2n_stuffer_peek_check_for_str  s2n_stuffer_read_expected_str  s2n_stuffer_write_vector_size"


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

    # Remove defines and includes from the generated Makefile.arpa, for consistency
    # TODO _ remove for s2n
    sed -i '' -e 's-DEFINES += .*--g' \
        -e 's-INCLUDES += .*--g' \
        Makefile.arpa

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


function write_to_log {
    # TODO clean this fct
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
    if [ ! "$failure" ]; then
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
        echo "<END-(IDENTICAL)>"
        write_to_log SUCCESS
    else
        echo "<END-(DIFFERENT)>"
        write_failure_docs
        # users may override failures.
        # This option exists to assess some limitations of this approach.
        ask_override

        if [[ "$override" == [Yy]* ]]; then
            ((n_succ=n_succ+1))
            failure=""
            echo "<END-(OVERRIDEN)>"
            overriden_proofs+="$dir "
            write_to_log SUCCESS-OVERRIDE
            echo "< Overriden Proofs: $overriden_proofs>"
        else
            not_overriden_proofs+="$dir "
            write_to_log FAILURE
        fi
    fi
}


# MAIN
initialize $1
for dir in s2n_blob_zeroize_free; do
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

echo -e "\nHere are all the proofs that have been overriden:\n< $overriden_proofs >"
