#!/usr/bin/env bash

# http://demo.openhab.org:8080/doc/index.html#/

BASEURL="http://127.0.0.1:8080/rest"
ITEMNAME="dummy_number_2"

# --------------------------------------------------------------------------------------------

function send_command() {
    local LOCAL_ITEMNAME="$1"
    local LOCAL_STATE="$2"
    echo -e "\nsend_command(post): \"$LOCAL_ITEMNAME\" - \"$LOCAL_STATE\""

    curl -Ss -X POST --header "Content-Type: text/plain" --header "Accept: application/json" -d "$LOCAL_STATE" "$BASEURL/items/$LOCAL_ITEMNAME"
    local RC=$?
    if [ $RC -ne 0 ] ; then
        echo "RC=$RC"
    fi
}

function send_update() {
    local LOCAL_ITEMNAME="$1"
    local LOCAL_STATE="$2"
    echo -e "\nsend_update(put): \"$LOCAL_ITEMNAME\" - \"$LOCAL_STATE\""

    curl -Ss -X PUT --header "Content-Type: text/plain" --header "Accept: application/json" -d "$LOCAL_STATE" "$BASEURL/items/$LOCAL_ITEMNAME/state"
    local RC=$?
    if [ $RC -ne 0 ] ; then
        echo "RC=$RC"
    fi
}

function show_state() {
    local LOCAL_ITEMNAME="$1"
    echo -e "\nshow_state(get): \"$LOCAL_ITEMNAME\""

    curl -Ss -X GET --header "Accept: text/plain" "$BASEURL/items/$LOCAL_ITEMNAME/state"
    local RC=$?
    if [ $RC -ne 0 ] ; then
        echo "RC=$RC"
    fi
    echo ""
}

# --------------------------------------------------------------------------------------------

show_state "$ITEMNAME"
sleep 1

send_command "$ITEMNAME" "1"
sleep 1

show_state "$ITEMNAME"
sleep 1

send_command "$ITEMNAME" "NULL"
sleep 1

show_state "$ITEMNAME"
sleep 1

send_command "$ITEMNAME" "UNDEF"
sleep 1

show_state "$ITEMNAME"
sleep 1

send_update "$ITEMNAME" "NULL"
sleep 1

show_state "$ITEMNAME"
sleep 1

send_update "$ITEMNAME" "UNDEF"
sleep 1

show_state "$ITEMNAME"
sleep 1

send_update "$ITEMNAME" "2"
sleep 1
