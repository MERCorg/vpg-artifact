import argparse
import json
import logging
import os
import re
import shutil

from library import MyLogger, run_program
from prepare import EXPERIMENTS

project_time_regex = re.compile(r".*Time project: ([0-9.]+)s.*$")
reachable_time_regex = re.compile(r".*Time reachable: ([0-9.]+)s.*$")
solving_time_regex = re.compile(r".*Time solve_variability_zielonka: ([0-9.]+)s$")
recursive_calls_regex = re.compile(r".*Performed ([0-9]+) recursive calls.*")

class ResultParser:
    """Parser that captures solving time and number of recursive calls from tool output."""

    def __init__(self):
        self.project_time_s: float|None = None
        self.reachable_time_s: float|None = None
        self.solving_time_s: float|None = None
        self.recursive_calls: list[int] = []

    def __call__(self, line: str):
        """Processes a line of output from the tool."""
        s = line.strip()
        m = solving_time_regex.match(s)
        if m:
            self.solving_time_s = float(m.group(1))
            return

        m2 = recursive_calls_regex.match(s)
        if m2:
            self.recursive_calls.append(int(m2.group(1)))
            return
        
        m3 = project_time_regex.match(s)
        if m3:
            self.project_time_s = float(m3.group(1))
            return
        
        m4 = reachable_time_regex.match(s)
        if m4:
            self.reachable_time_s = float(m4.group(1))


def run_experiment(logger: MyLogger, merc_vpg_bin: str, mcrl2_name: str, file: str, solve_variant: str, output_dir: str):
    """Runs all experiments"""

    result = {}
    result["experiment"] = mcrl2_name
    result["file"] = file
    result["solve_variant"] = solve_variant
    result["times"] = []
    result["recursive_calls"] = []
    result["project_times"] = []
    result["reachable_times"] = []

    for i in range(0, 5):
        logger.info(f"Run {i + 1}/5: Solving {file} with variant {solve_variant}")

        parser = ResultParser()
        run_program(
            [
                merc_vpg_bin,
                "solve",
                "--oxidd-node-capacity=1000000",
                "--debug",
                "--timings",
                f"--solve-variant={solve_variant}",
                file,
            ],
            logger,
            parser,
        )
        result["times"].append(parser.solving_time_s)
        result["recursive_calls"].append(parser.recursive_calls)
        result["project_times"].append(parser.project_time_s)
        result["reachable_times"].append(parser.reachable_time_s)

    with open(os.path.join(output_dir, "results.json"), "a", encoding="utf-8") as f:
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

    parser.add_argument(dest="merc_binpath", action="store", type=str)
    parser.add_argument(dest="output", action="store", type=str)

    args = parser.parse_args()

    merc_vpg_bin = shutil.which("merc-vpg", path=args.merc_binpath)
    if merc_vpg_bin is None:
        raise FileNotFoundError(f"Could not find merc_vpg binary in path {args.merc_binpath}")

    logger = MyLogger("main", os.path.join(args.output, "run.log"))

    # Prepare the variability parity games for all the properties and specifications.
    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        for file in os.listdir(tmp_directory):
            path = tmp_directory + file
            if ".svpg" in path:
                for variant in ["family", "product", "family-optimised-left"]:
                    run_experiment(logger, merc_vpg_bin, mcrl2_name, path, variant, args.output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
