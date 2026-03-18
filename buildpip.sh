#!/bin/bash
export PIP_USE_PEP517=1
rm -rf dist/*
if python3 setup.py sdist bdist_wheel ; then
	echo "Uploading to pip"
	twine upload dist/*
else
	echo "Skipping upload, build failed"
fi

