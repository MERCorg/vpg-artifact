import argparse
import os
import re

from library import MyLogger, run_program
from prepare import EXPERIMENTS

solving_time_regex = re.compile(r">* Time solve_variability_zielonka: ([0-9.]+) s$")

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


def run_experiments(logger: MyLogger):
    """Runs all experiments"""

    result = {}
    for i in range(0, 5):
        logger.info(f"Run {i + 1}/5: Solving variability parity games")
        
        parser = ResultParser()
        run_program(
            [
                "merc-vpg",
                "solve",
                "--solve-variant=family",
            ],
            logger,
            parser
        )



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

    os.environ["PATH"] += os.pathsep + args.mcrl2_binpath.strip()

    logger = MyLogger("main", "prepare.log")

    # Prepare the variability parity games for all the properties and specifications.
    prepare_experiments(EXPERIMENTS, logger)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
