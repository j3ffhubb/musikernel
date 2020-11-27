#!/bin/sh

find musikernel/src -type f -name '*.c' -or -name '*.h' -exec cat {} \; | wc -l

echo "^^^ Lines of C code"

find musikernel/{mkpy,sgdata} -type f -name '*.py' -exec cat {} \; | wc -l

echo "^^^ Lines of Python code"

