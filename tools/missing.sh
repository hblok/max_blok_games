#!/bin/bash

THIS_DIR="$(readlink -f $(dirname $0))"

$THIS_DIR/missing_tests.py
$THIS_DIR/missing_test_targets.py
