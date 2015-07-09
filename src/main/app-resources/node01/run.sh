#!/bin/bash

# source the ciop functions (e.g. ciop-log, ciop-getparam)
source ${ciop_job_include}

# define the exit codes
SUCCESS=0
E_OPTERROR=65
E_NOINPUT=66

# add a trap to exit gracefully
function cleanExit ()
{
   local retval=$?
   local msg=""
   case "$retval" in
       $SUCCESS)     msg="Processing successfully concluded";;
       $E_OPTERROR)  msg="Call to mkjson had illegal argument(s)";;
       $E_NOINPUT)   msg="No input provided";;
       *)            msg="Unknown error";;
   esac
   [ "$retval" != "0" ] && ciop-log "ERROR" "Error $retval - $msg, processing aborted" || ciop-log "INFO" "$msg"
   exit $retval
}

trap cleanExit EXIT

# loops over all inputs
while read inputfile; do
  # report activity in log
  ciop-log "INFO" "Retrieving $inputfile from storage"

  # retrieve input data to local TMPDIR
  retrieved=`ciop-copy -o $TMPDIR "$inputfile"`

  # check if file retrieved, if not throw $E_NOINPUT
  [ "$?" == "0" -a -e "$retrieved" ] || exit $E_NOINPUT

  # report activity in log
  ciop-log "INFO" "Retrieving `basename $retrieved`"

  # publish the result
  ciop-log "INFO" "Publishing result"
  ciop-publish $TMPDIR/*.N1
done

exit $SUCCESS
