#!/bin/sh

find pydaw/src -type f -name '*.c' -or -name '*.h' -exec cat {} \; | wc -l

echo "^^^ Lines of C code"

find pydaw/mkpy -type f -name '*.py' -exec cat {} \; | wc -l

echo "^^^ Lines of Python code"

