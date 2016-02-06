#!/bin/sh

git tag $(cat major-version.txt)-$(cat minor-version.txt) && \
git push --tags
