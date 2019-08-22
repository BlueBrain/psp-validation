#!/usr/bin/env python

"""Test the BluePy extractor"""

# import bglibpy
# from bglibpy import bluepy
import bluepy.extractor
import shutil
import os


def create_extracted_circuit(old_circuitname, output_path):
    "..."
    circuit = bluepy.Circuit(old_circuitname)

    gids = [76921, 77978,
            81378, 82622,
            77717, 78285,
            78917, 81501,
            82506, 82758]

    gids.sort()
    print gids

            # 76938, 78350,
            # 78545, 82822,
            # 81379, 78297,
            # 78323, 79768,
            # 78462, 77243]
    extracted = bluepy.extractor.CircuitExtractor(circuit, gids)
    extracted.extract_and_write(output_path, keep_empty_targets=True)

    new_circuitconfig = os.path.join(output_path, "CircuitConfig")
    print new_circuitconfig
    with open(new_circuitconfig, "r") as new_circuitconfig_file:
        new_circuitconfig_content = new_circuitconfig_file.read()

    cor_new_circuitconfig_content = ""

    base_dir = 'psp_validation/tests/input_data'

    for line in new_circuitconfig_content.split("\n")[:-1]:
        newline = line

        if "MorphologyPath" in line:
            newline = "  MorphologyPath %s/circuit_tencell_example1/" \
                      "morphologies/h5" % (base_dir)
        if "METypePath" in line:
            newline = "  METypePath %s/circuit_tencell_example1/ccells" % (base_dir)
        if "CircuitPath" in line:
            newline = "  CircuitPath %s/circuit_tencell_example1" % (base_dir)
        elif "nrnPath" in line:
            newline = "  nrnPath %s/circuit_tencell_example1/" \
                      "ncsFunctionalAllRecipePathways" % (base_dir)
        cor_new_circuitconfig_content += newline + "\n"

    with open(new_circuitconfig, "w") as new_circuitconfig_file:
        new_circuitconfig_file.write(cor_new_circuitconfig_content)

    new_metypepath = os.path.join(output_path, "ccells")
    new_morphpath = os.path.join(output_path, "morphologies/ascii")

    os.mkdir(new_metypepath)
    os.makedirs(new_morphpath)

    orig_metypepath = circuit.RUN.CONTENTS.METypePath
    orig_morphpath = circuit.RUN.CONTENTS.MorphologyPath[:-3] + "/ascii"
    for gid in gids:
        template_name = circuit.mvddb.load_gids([gid])[0].METype + ".hoc"
        morph_name = circuit.mvddb.load_gids([gid])[0].name + ".asc"
        template_filename = os.path.join(orig_metypepath, template_name)
        morph_filename = os.path.join(orig_morphpath, morph_name)
        shutil.copy(template_filename, new_metypepath)
        shutil.copy(morph_filename, new_morphpath)


def main():
    """Main"""

    print 'Create a test circuit with ten cells from %s' \
        % "/bgscratch/bbp/circuits/23.07.12/SomatosensoryCxS1-v4."\
        "lowerCellDensity.r151/O1/merged_circuit/CircuitConfig"

    output_path = "../../input_data/circuit_tencell_example1/"
    shutil.rmtree(output_path)
    old_circuitname = "/bgscratch/bbp/l5/release/2012.07.23/circuit/Somato" \
        "sensoryCxS1-v4.lowerCellDensity.r151"\
        "/O1/merged_circuit/CircuitConfig"

    create_extracted_circuit(old_circuitname, output_path)

if __name__ == "__main__":
    main()
