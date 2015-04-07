#!/bin/bash

set -e

echo 'This is a demo hook!'

# `socrates` will add these environment variables before running a hook:
echo "$SOCRATES_DIR"
echo "$SOCRATES_CONFIG_PATH"
echo "$SOCRATES_HOOKS_DIR"
echo "$SOCRATES_STATIC_DIR"
echo "$SOCRATES_DROPBOX_DIR"
echo "$SOCRATES_CRITERIA_DIR"

# final note: hooks don't have to be shell scripts, but they should always
# return a nonzero exit status if something goes wrong, so that `socrates`
# will halt

exit 0
