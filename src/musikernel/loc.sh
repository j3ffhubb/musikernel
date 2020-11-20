#!/bin/sh

find src -type f -name '*.c' -or -name '*.h' -exec cat {} \; | wc -l

echo "^^^ Lines of C code"

find sgui sglib test -type f -name '*.py' -exec cat {} \; | wc -l

echo "^^^ Lines of Python code"

find sglib -type f -name '*.py' -exec cat {} \; | wc -l
echo "^^^ sglib"

find test -type f -name '*.py' -exec cat {} \; | wc -l
echo "^^^ tests"
