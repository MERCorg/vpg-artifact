import argparse
import os
import re
import json
import logging

from library import MyLogger, run_program
from prepare import EXPERIMENTS

solving_time_regex = re.compile(r".* Time solve_variability_zielonka: ([0-9.]+)s$")


class ResultParser:
    """Parser that captures 'Solving time' and 'Reachable time' (in ms) from tool output."""

    def __init__(self):
        self.solving_time_s: float = -1

    def __call__(self, line: str):
        """Processes a line of output from the tool."""
        s = line.strip()
        m = solving_time_regex.match(s)
        if m:
            self.solving_time_s = float(m.group(1))
            return


def run_experiment(logger: MyLogger, mcrl2_name: str, file: str, solve_variant: str):
    """Runs all experiments"""

    result = {}
    result["experiment"] = mcrl2_name
    result["file"] = file
    result["solve_variant"] = solve_variant
    result["times"] = []
    for i in range(0, 5):
        logger.info(f"Run {i + 1}/5: Solving {file} with variant {solve_variant}")

        parser = ResultParser()
        run_program(
            [
                "merc-vpg",
                "solve",
                "--oxidd-node-capacity=1000000",
                f"--solve-variant={solve_variant}",
                file,
            ],
            logger,
            parser,
        )
        result["times"].append(parser.solving_time_s)

    with open("results.json", "a", encoding="utf-8") as f:
        json.dump(result, f)
        f.write("\n")


def main():
    """The main function"""

    # Parse some configuration options
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Runs the experiments.",
        epilog="",
    )

    parser.add_argument("-m", "--merc-binpath", action="store", type=str, required=True)

    args = parser.parse_args()

    os.environ["PATH"] += os.pathsep + args.merc_binpath.strip()

    logger = MyLogger("main", "run.log")

    # Prepare the variability parity games for all the properties and specifications.
    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        for file in os.listdir(tmp_directory):
            path = tmp_directory + file
            if ".svpg" in path:
                for variant in ["family", "product", "family-optimised-left"]:
                    run_experiment(logger, mcrl2_name, path, variant)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
