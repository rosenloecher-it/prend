#!/usr/bin/env bash

# to activate this hook create a symlink
#   cd $PROJECT_DIR/.git/hooks
#   ln -s ../../tools/githooks/pre-push-entry.sh ./pre-push

# -----------------------------------------------------------------------
# configuration

# set to 0 or 1
export GITHOOK_DEBUG=1

# if any of the scripts exists with a non 0 value, the push is aborted
# pathes should be relative to this script
declare -a HOOK_SCRIPTS=("./pre-push-pervent-private.sh")
# separate by spaces: ("./pre-push-pervent-private.sh" "./script2.sh")

# -----------------------------------------------------------------------

# change into script dir to use relative pathes
SCRIPT_PATH=$(readlink -f $0)
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SCRIPT_NAME=$(basename $0)
cd "$SCRIPT_DIR"

export GITHOOK_PREPUSH_REMOTE="$1"
export GITHOOK_PREPUSH_URL="$2"


while read local_ref local_sha remote_ref remote_sha
do

    export GITHOOK_PREPUSH_LOCAL_REF="$local_ref"
    export GITHOOK_PREPUSH_LOCAL_SHA="$local_sha"
    export GITHOOK_PREPUSH_REMOTE_REF="$remote_ref"
    export GITHOOK_PREPUSH_REMOTE_SHA="$remote_sha"

    # iterate the sripts
    for HOOK_SCRIPT in ${HOOK_SCRIPTS[@]}; do

        if [ -f "$HOOK_SCRIPT" ] ; then
            echo "found HOOK_SCRIPT script: $HOOK_SCRIPT"
            "$HOOK_SCRIPT"
            RC=$?
            if [ $RC -ne 0 ] ; then
                echo "push aborted by hook - $GITHOOK_PREPUSH_REMOTE:$GITHOOK_PREPUSH_LOCAL_SHA..$GITHOOK_PREPUSH_REMOTE_REF"
                exit 1
            fi
        else
           echo "script not found ($HOOK_SCRIPT)"
        fi
    done

done

exit 0
