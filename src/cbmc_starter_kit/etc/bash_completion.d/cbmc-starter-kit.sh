#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

################################################################
# Documentation
#
# compgen, complete:
#   https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion-Builtins.html
# _filedir:
#   https://github.com/nanoant/bash-completion-lib/blob/master/include/_filedir

################################################################
# Options
#

common_options="--help -h --verbose --debug --version"

setup_options=""
setup_proof_options=""
update_options="--cbmc-root --starter-kit-root --no-test-removal --no-update"

_core_autocomplete()
{
  local options=$1
  local cur=${COMP_WORDS[COMP_CWORD]}
  local prev=${COMP_WORDS[COMP_CWORD-1]}

  case "$prev" in
   --cbmc-root|--starter-kit-root|--proofdir)
     _filedir -d
     return 0
     ;;
  esac

  # all remaining completions satisfy: "$cur" == -*
  COMPREPLY=( $( compgen -W "$options $common_options" -- $cur ) )
  return 0
}

_setup_autocomplete()
{
  _core_autocomplete "$setup_options"
}

_setup_proof_autocomplete()
{
  _core_autocomplete "$setup_proof_options"
}

_update_autocomplete()
{
  _core_autocomplete "$update_options"
}

complete -F _setup_autocomplete cbmc-starter-kit-setup
complete -F _setup_proof_autocomplete cbmc-starter-kit-setup-proof
complete -F _update_autocomplete cbmc-starter-kit-update
