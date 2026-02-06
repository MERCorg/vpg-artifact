#!/usr/bin/env python

import os
import argparse
import logging
import json
import shutil
import re

from typing import List
from library import run_program, MyLogger

# A regex matching in=out
mapping_regex = re.compile(r"(.*)=(.*)")

# A regex matching a transition in the aut format '(from, action, to)'
transition_regex = re.compile(r"\(([0-9]*),\"(.*)\",([0-9]*)\)")

SCRIPT_PATH=os.path.dirname(os.path.abspath(__file__))

EXPERIMENTS = [
    (
        os.path.join(SCRIPT_PATH, "../cases/elevator/"),
        "elevator.mcrl2",
        [
            "property1.mcf",
            "property2.mcf",
            "property3.mcf",
            "property4.mcf",
            "property5.mcf",
            "property6.mcf",
            "property7.mcf",
        ],
    ),
    (
        os.path.join(SCRIPT_PATH, "../cases/minepump/"),
        "minepump_fts.mcrl2",
        [
            "phi1.mcf",
            "phi2.mcf",
            "phi3.mcf",
            "phi4.mcf",
            "phi5.mcf",
            "phi6.mcf",
            "phi7.mcf",
            "phi8.mcf",
            "phi9.mcf",
        ],
    ),
    (
        os.path.join(SCRIPT_PATH, "../cases/vending_machine/"),
        "VendingMachine.mcrl2",
        [
            "property1.mcf",
            "property2.mcf",
            "property3.mcf",
            "property4.mcf",
            "property5.mcf",
            "property6.mcf",
            "property7.mcf",
        ],
    ),
]

def is_newer(inputfile: str, outputfile: str, ignore=False) -> bool:
    """Returns true iff the input file is newer than the output file"""
    if ignore:
        return True

    try:
        return os.path.getmtime(inputfile) > os.path.getmtime(outputfile)
    except OSError:
        return True

def prepare(
    directory: str,
    tmp_directory: str,
    mcrl2_name: str,
    properties: List[str],
    logger: MyLogger,
    mcrl22lps_bin: str,
    lps2lts_bin: str,
    merc_vpg_bin: str
):
    """Prepares the parity games for one experiment, consisting of an mCRL2 specification and several properties"""

    # Ensure that tmp directory exists since the mCRL2 tools cannot make it
    try:
        os.mkdir(tmp_directory)
    except OSError:
        logger.debug(f"{tmp_directory} already exists")

    # Convert the mcrl2 to an aut file.
    base, _ = os.path.splitext(mcrl2_name)
    mcrl2_file = os.path.join(directory, mcrl2_name)
    lps_file = os.path.join(tmp_directory, base + ".lps")
    aut_file = os.path.join(tmp_directory, base + ".aut")

    if is_newer(mcrl2_file, lps_file):
        run_program([mcrl22lps_bin, "--verbose", mcrl2_file, lps_file], logger)
    if is_newer(lps_file, aut_file):
        run_program([lps2lts_bin, "--verbose", lps_file, aut_file], logger)

    # Convert the actions in the .aut files to move features from the data into the action label.
    # File contains from=to per line for each action.
    mapping = {}

    # Indicates that the .aut file has been generated.
    actionrename_file = os.path.join(directory, "actionrename")
    aut_renamed_file = os.path.join(tmp_directory, base + ".renamed.aut")

    if is_newer(actionrename_file, aut_renamed_file) or is_newer(
        aut_file, aut_renamed_file
    ):
        with open(actionrename_file, encoding="utf-8") as file:
            for line in file.readlines():
                result = mapping_regex.match(line)
                if result is not None:
                    mapping[result.group(1)] = result.group(2)

        logger.debug("renaming applied: %s", mapping)

        # Rename the action labels in the aut file based on the mapping computed above
        with open(aut_renamed_file, "w", encoding="utf-8") as outfile:
            with open(aut_file, encoding="utf-8") as file:
                for line in file.readlines():
                    result = transition_regex.match(line)
                    if result is not None:
                        action = result.group(2)
                        action = mapping.get(action, action)
                        outfile.write(
                            f'({result.group(1)},"{action}",{result.group(3)})\n'
                        )
                    else:
                        outfile.write(line)

    # Generate the SVPG for every property
    featurediagram_file = os.path.join(directory, "FD")

    for prop in properties:
        mcf_file = os.path.join(directory, prop)
        prop, _ = os.path.splitext(prop)
        game_file = os.path.join(tmp_directory, prop + ".svpg")

        name = f"{os.path.basename(aut_file)} and {os.path.basename(mcf_file)}"
        if (
            is_newer(featurediagram_file, game_file)
            or is_newer(aut_renamed_file, game_file)
            or is_newer(mcf_file, game_file)
        ):
            logger.info(f"Generating parity game for {name}")
            run_program(
                [
                    merc_vpg_bin,
                    "translate",
                    featurediagram_file,
                    aut_renamed_file,
                    mcf_file,
                    game_file,
                ],
                logger,
            )

def main():
    """The main function"""

    # Parse some configuration options
    parser = argparse.ArgumentParser(
        prog="prepare.py",
        description="Prepares the variability parity games.",
        epilog="",
    )

    parser.add_argument(
        dest="mcrl2_binpath", action="store", type=str
    )
    parser.add_argument(dest="merc_binpath", action="store", type=str)

    args = parser.parse_args()

    mcrl22lps_bin = shutil.which("mcrl22lps", path=args.mcrl2_binpath)
    lps2lts_bin = shutil.which("lps2lts", path=args.mcrl2_binpath)
    merc_vpg_bin = shutil.which("merc-vpg", path=args.merc_binpath)
    if mcrl22lps_bin is None or lps2lts_bin is None or merc_vpg_bin is None:
        logging.error(f"Could not find one of the required binaries {mcrl22lps_bin, lps2lts_bin, merc_vpg_bin}")
        exit(1)

    logger = MyLogger("main", "prepare.log")

    # Prepare the variability parity games for all the properties and specifications.
    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        logger.info("Starting preparation for experiment '%s'...", directory)
        prepare(directory, tmp_directory, mcrl2_name, properties, logger, mcrl22lps_bin, lps2lts_bin, merc_vpg_bin)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
