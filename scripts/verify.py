import argparse
import os
import logging

from library import MyLogger, run_program
from prepare import EXPERIMENTS

def main():
    """Verifies the results of the variability solvers."""

    # Parse some configuration options
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Runs the experiments.",
        epilog="",
    )

    parser.add_argument(dest="merc_binpath", action="store", type=str)

    args = parser.parse_args()
    merc_vpg = os.path.join(args.merc_binpath.strip(), "merc-vpg")

    logger = MyLogger("main", "verify.log")

    # Prepare the variability parity games for all the properties and specifications.
    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        for file in os.listdir(tmp_directory):
            path = tmp_directory + file
            if ".svpg" in path:
                for solve_variant in ["family", "family-optimised-left"]:
                    run_program(
                        [
                            merc_vpg,
                            "solve",
                            "--oxidd-node-capacity=1000000",
                            f"--solve-variant={solve_variant}",
                            "--verify-solution",
                            path,
                        ],
                        logger
                    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
