#!/bin/sh
# Inside the Nebius job: unpack the bundle cloud/suite-job.sh sent, then run the suite.
#   sh /andy/job-entry.sh <runs> [more run_suite.py arguments]
set -e
cd /andy
base64 -d bundle.b64 | tar -xzf -
RUNS="$1"; shift
exec python3 evals/run_suite.py --runs "$RUNS" "$@"
