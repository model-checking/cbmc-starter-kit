# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# See https://packaging.python.org/en/latest/tutorials/installing-packages/
# See https://packaging.python.org/tutorials/packaging-projects/
# python3 -m ensurepip
# python3 -m pip install --upgrade pip setuptools wheel
# python3 -m pip install --upgrade build
# python3 -m pip install --upgrade pylint

default:
	@echo Nothing to make

################################################################
# Run pylint over the package

pylint:
	make -C src/cbmc_starter_kit pylint

################################################################
# Build the distribution package

build:
	python3 -m build

unbuild:
	$(RM) -r dist

################################################################
# Install the package into a virtual environment in development mode
#
# Note: Editable installs from pyproject.toml require at least pip 21.3

VENV = /tmp/cbmc-starter-kit
develop:
	python3 -m venv $(VENV)
	$(VENV)/bin/python3 -m pip install --upgrade pip
	$(VENV)/bin/python3 -m pip install --editable .
	@ echo
	@ echo "Package installed into virtual environment at $(VENV)."
	@ echo "Activate virtual environment with 'source $(VENV)/bin/activate'"
	@ echo "(or add it to PATH with 'export PATH=\$$PATH:$(VENV)/bin')."
	@ echo

undevelop:
	$(RM) -r $(VENV)

################################################################
# Install the package
#
# Note: This requires write permission (sudo): It updates the system
# site-packages directory.


install:
	python3 -m pip install --verbose .

uninstall:
	python3 -m pip uninstall --verbose --yes cbmc-starter-kit

################################################################
# Clean up after packaging and installation

clean:
	$(RM) *~
	$(RM) *.pyc
	$(RM) -r __pycache__

veryclean: clean unbuild undevelop

################################################################
# Test uploading package to test.pypi.org

twine:
	$(RM) -r dist
	python3 -m build
	python3 -m twine upload --repository testpypi dist/*

################################################################

.PHONY: build clean default develop install pylint twine
.PHONY: unbuild undevelop uninstall veryclean
