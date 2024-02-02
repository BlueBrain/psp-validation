#!/usr/bin/env bash
# The tests for psp-validation require an installation of the neurodamus mod files
# that were compiled with the installed NEURON, and its dependencies.
# This is inspired by how it's done in bglibpy
# (see .compile_mod, .install_common_mods.sh and .install_neurodamus.sh)
# and by looking at how BlueBrain's spack installs the mods
set -euxo pipefail

BASE=$1

DONE=$BASE/.installed_hippocampus_mod_files
if [[ -f $DONE ]]; then
    echo "Already installed mod files"
    exit
fi

rm -rf "$BASE"
mkdir -p "$BASE"

GIT_BASE=git@bbpgitlab.epfl.ch:hpc/sim

pushd "$BASE"

git clone -q --depth 1 $GIT_BASE/neurodamus-core.git

MODEL="hippocampus"

echo "Cloning models for $MODEL"
git clone -q --depth 1 --recursive $GIT_BASE/models/$MODEL.git

echo "Downloading models for $MODEL"
pushd $MODEL
./fetch_common.bash
popd

echo "Compiling models for $MODEL"
nrnivmodl $MODEL/mod

popd
touch "$DONE"
