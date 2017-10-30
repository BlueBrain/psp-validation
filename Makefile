#modules that have tests
#TEST_MODULES=.

#modules that are installable (ie: ones w/ setup.py)
INSTALL_MODULES=.

# Ignore directories for pep8 and pylint (on top of tests and doc)
IGNORE_LINT=apps|psp_validation

#packages to cover
COVER_PACKAGES=psp_validation

PYTHON_PIP_VERSION=pip==9.0.1

DOC_MODULES=doc
DOC_REPO=--doc-repo ssh://bbpcode.epfl.ch/infra/jekylltest

##### DO NOT MODIFY BELOW #####################

CI_REPO?=ssh://bbpcode.epfl.ch/platform/ContinuousIntegration.git
CI_DIR?=ContinuousIntegration

FETCH_CI := $(shell \
        if [ ! -d $(CI_DIR) ]; then \
            git clone $(CI_REPO) $(CI_DIR) > /dev/null ;\
        fi;\
        echo $(CI_DIR) )
include $(FETCH_CI)/python/common_makefile
