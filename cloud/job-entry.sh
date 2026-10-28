#!/bin/sh
# Inside the Nebius job: unpack the bundle cloud/suite-job.sh sent, then run the suite.
#   sh /andy/job-entry.sh <runs> [more run_suite.py arguments]
set -e
cd /andy
# Python's tarfile, so the slim image needs no xz tool; "r:*" reads a gzip or an xz bundle: bundle.xz as bytes
# (cloud/suite-job.sh since 2026-10-28), or bundle.b64 as base64 text.
python3 -c "import base64, io, os, tarfile; raw = open('bundle.xz', 'rb').read() if os.path.exists('bundle.xz') else base64.b64decode(open('bundle.b64').read()); tarfile.open(fileobj=io.BytesIO(raw), mode='r:*').extractall(filter='data')"
RUNS="$1"; shift
exec python3 evals/run_suite.py --runs "$RUNS" "$@"
