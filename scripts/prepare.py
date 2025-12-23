#!/usr/bin/env python

from io import StringIO
import os
import subprocess
import argparse
import logging
import sys
import time
import json
import shutil

from typing import List

formatter = logging.Formatter("%(threadName)-11s %(asctime)s %(levelname)s %(message)s")
logging.basicConfig(level=logging.DEBUG)

class MyLogger(logging.Logger):
    """My own logger that stores the log messages into a string stream"""

    def __init__(self, name: str, filename: str | None = None, terminator="\n"):
        """Create a new logger instance with the given name"""
        logging.Logger.__init__(self, name, logging.DEBUG)

        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.terminator = terminator
        handler.setFormatter(formatter)

        if filename is not None:
            self.addHandler(logging.FileHandler(filename))

        standard_output = logging.StreamHandler(sys.stderr)
        standard_output.terminator = terminator

        self.addHandler(handler)
        self.addHandler(standard_output)

    def getvalue(self) -> str:
        """Returns the str that has been logged to this logger"""
        return self.stream.getvalue()

def is_newer(inputfile: str, outputfile: str, ignore=False) -> bool:
    """Returns true iff the input file is newer than the output file"""
    if ignore:
        return True

    try:
        return os.path.getmtime(inputfile) > os.path.getmtime(outputfile)
    except OSError:
        return True


def run_program(cmds, logger, process=None):
    """Runs the given program with sensible defaults, and logs the results to the logger.
    Returns the execution time in seconds."""

    start_time = time.time()

    with subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    ) as proc:
        for line in proc.stdout:
            logger.info(line.strip())

            if process is not None:
                process(line.strip())

        proc.wait()

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, proc.args)

    elapsed_time = time.time() - start_time
    return elapsed_time


def prepare(
    directory: str,
    tmp_directory: str,
    mcrl2_name: str,
    properties: List[str],
    logger: MyLogger,
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

    mcrl22lps_exe = shutil.which("mcrl22lps")
    lps2lts_exe = shutil.which("lps2lts")

    if is_newer(mcrl2_file, lps_file):
        run_program([mcrl22lps_exe, "--verbose", mcrl2_file, lps_file], logger)
    if is_newer(lps_file, aut_file):
        run_program([lps2lts_exe, "--verbose", lps_file, aut_file], logger)

    # Convert the actions in the .aut files to move features from the data into the action label.
    # File contains from=to per line for each action.
    mapping = {}

    # Indicates that the .aut file has been generated.
    update_projections = False
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
                    "merc-vpg",
                    "translate",
                    featurediagram_file,
                    aut_renamed_file,
                    mcf_file,
                    game_file,
                ],
                logger,
            )


def prepare_experiments(
    experiments: list[tuple[str, str, list[str]]], logger: MyLogger
):
    """Runs all preparation steps for the given experiments"""

    timing_results: dict[str, dict[str, float]] = {}

    for experiment in experiments:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        logger.info("Starting preparation for experiment '%s'...", directory)
        directory: prepare(directory, tmp_directory, mcrl2_name, properties, logger)

    with open("preprocessing.json", "w", encoding="utf-8") as json_file:
        json.dump(timing_results, json_file, indent=2)


def main():
    """The main function"""

    # Parse some configuration options
    parser = argparse.ArgumentParser(
        prog="prepare.py",
        description="Prepares the variability parity games.",
        epilog="",
    )

    parser.add_argument(
        "-t", "--mcrl2-binpath", action="store", type=str, required=True
    )
    parser.add_argument("-m", "--merc-binpath", action="store", type=str, required=True)

    args = parser.parse_args()

    os.environ["PATH"] += os.pathsep + args.mcrl2_binpath.strip()
    os.environ["PATH"] += os.pathsep + args.merc_binpath.strip()

    experiments = [
        (
            "../cases/elevator/",
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
            "../cases/minepump/",
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
            "../cases/vending_machine/",
            "VendingMachine.mcrl2",
            [
                "infinitely_many_latte_then_infinitely_often_clean_nozzle.mcf",
                "infinitely_often_cappuccino.mcf",
                "infinitely_often_cleaning_nozzle.mcf",
                "infinitely_often_coffee.mcf",
                "infinitely_often_espresso.mcf",
                "infinitely_often_hot_water.mcf",
                "infinitely_often_jug.mcf",
                "infinitely_often_latte_macchiato.mcf",
                "infinitely_often_tea.mcf",
                "infinitely_often_warm_milk.mcf",
                "invariantly_possibly_cappuccino.mcf",
                "no_clean_nozzle_if_no_milk_can_be_heated_or_steamed.mcf",
                "no_espresso_without_grinder.mcf",
            ],
        ),
    ]

    logger = MyLogger("main", "prepare.log")

    # Prepare the variability parity games for all the properties and specifications.
    prepare_experiments(experiments, logger)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
