#!/usr/bin/env bash

# -----------------------------------------------------------------------
# configuration

# all lower case!
FIND_REMOTE="github"

# all lower case!
FIND_REF="privat"

# -----------------------------------------------------------------------
# test

# GITHOOK_DEBUG=1
# GITHOOK_PREPUSH_REMOTE=origingithub
# GITHOOK_PREPUSH_URL=git@homeserver:/home/git/prend
# GITHOOK_PREPUSH_LOCAL_REF=refs/heads/master
# GITHOOK_PREPUSH_LOCAL_SHA=96923b8365375c4275f2f4044039f2b3ee81b930
# GITHOOK_PREPUSH_REMOTE_REF=refs/heads/master
# GITHOOK_PREPUSH_REMOTE_SHA=fbbe0d741228de8ac1b2524f868b7400200d9d49

# -----------------------------------------------------------------------

function output_text() {
	if [ "$GITHOOK_DEBUG" == "1" ] ; then
		echo "$1"
	fi
}

function find_key_in_text() {
	# result 1 if found, otherwise 0
	local TO_FIND=$(echo "$1" | tr '[:upper:]' '[:lower:]')
	local TO_SEARCH=$(echo "$2" | tr '[:upper:]' '[:lower:]')

	if [[ "$TO_SEARCH" == *"$TO_FIND"* ]]; then
  		output_text "find_key_in_text: \"$TO_FIND\" in \"$TO_SEARCH\""
  		return 1
	fi

	return 0
}

if [ "$GITHOOK_DEBUG" == "1" ] ; then
	echo "GITHOOK_PREPUSH_REMOTE=$GITHOOK_PREPUSH_REMOTE"
	echo "GITHOOK_PREPUSH_URL=$GITHOOK_PREPUSH_URL"
	echo "GITHOOK_PREPUSH_LOCAL_REF=$GITHOOK_PREPUSH_LOCAL_REF"
	echo "GITHOOK_PREPUSH_LOCAL_SHA=$GITHOOK_PREPUSH_LOCAL_SHA"
	echo "GITHOOK_PREPUSH_REMOTE_REF=$GITHOOK_PREPUSH_REMOTE_REF"
	echo "GITHOOK_PREPUSH_REMOTE_SHA=$GITHOOK_PREPUSH_REMOTE_SHA"
fi

find_key_in_text "$FIND_REMOTE" "$GITHOOK_PREPUSH_REMOTE"
FOUND_IN_REMOTE=$?

find_key_in_text "$FIND_REMOTE" "$GITHOOK_PREPUSH_URL"
FOUND_IN_URL=$?

if [ $FOUND_IN_REMOTE -eq 0 ] && [ $FOUND_IN_URL -eq 0 ] ; then
	output_text "no remote key found (FOUND_IN_REMOTE=$FOUND_IN_REMOTE; FOUND_IN_URL=$FOUND_IN_URL)=> OK"
	exit 0
else
	find_key_in_text "$FIND_REF" "$GITHOOK_PREPUSH_LOCAL_REF"
	FOUND_IN_LOCAL_REF=$?

	find_key_in_text "$FIND_REF" "$GITHOOK_PREPUSH_REMOTE_REF"
	FOUND_IN_REMOTE_REF=$?

	if [ $FOUND_IN_LOCAL_REF -ne 0 ] || [ $FOUND_IN_REMOTE_REF -ne 0 ] ; then
		output_text "ref key found (FOUND_IN_LOCAL_REF=$FOUND_IN_LOCAL_REF; FOUND_IN_REMOTE_REF=$FOUND_IN_REMOTE_REF)=> abort"
		exit 1
	else
		# do nothing
		output_text "no ref found (FOUND_IN_LOCAL_REF=$FOUND_IN_LOCAL_REF; FOUND_IN_REMOTE_REF=$FOUND_IN_REMOTE_REF)=> OK"
	fi

fi

exit 0
