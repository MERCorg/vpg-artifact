import argparse
import os
import logging
import shutil
import re
import subprocess

from library import MyLogger, run_program
from prepare import EXPERIMENTS

# A regex matching in=out
mapping_regex = re.compile(r"(.*)=(.*)")

# A regex matching a transition in the aut format '(from, action, to)'
transition_regex = re.compile(r"\(([0-9]*), \"(.*)\", ([0-9]*)\)")


def main():
    """Verifies the results of the variability solvers."""

    # Parse some configuration options
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Runs the experiments.",
        epilog="",
    )

    parser.add_argument(dest="mcrl2_binpath", action="store", type=str)
    parser.add_argument(dest="merc_binpath", action="store", type=str)
    parser.add_argument(dest="output", action="store", type=str)

    args = parser.parse_args()
    merc_vpg = shutil.which("merc-vpg", path=args.merc_binpath)
    lts2pbes = shutil.which("lts2pbes", path=args.mcrl2_binpath)
    pbessolve = shutil.which("pbessolve", path=args.mcrl2_binpath)

    logger = MyLogger("main", os.path.join(args.output, "verify.log"))

    # Prepare the variability parity games for all the properties and specifications.
    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        # The directory in which to store all generated files
        tmp_directory = directory + "tmp/"

        for file in os.listdir(tmp_directory):
            path = tmp_directory + file
            # if ".svpg" in path:
            #     for solve_variant in ["family", "family-optimised-left"]:
            #         run_program(
            #             [
            #                 merc_vpg,
            #                 "solve",
            #                 "--oxidd-node-capacity=1000000",
            #                 f"--solve-variant={solve_variant}",
            #                 "--verify-solution",
            #                 path,
            #             ],
            #             logger
            #         )

            if ".renamed.aut" in path:
                projected_aut = path.replace(".renamed.aut", "_projected.aut")
                run_program(
                    [
                        merc_vpg,
                        "project",
                        path,
                        os.path.join(directory, "FD"),
                        projected_aut,
                    ],
                    logger,
                )

        for file in os.listdir(tmp_directory):
            path = tmp_directory + file

            if "_projected" in path and "renamed" not in path:
                aut_renamed_file = path.replace(
                    "_projected", "_projected.renamed"
                )

                # Rename the action labels in the aut file based on the mapping computed above
                with open(aut_renamed_file, "w", encoding="utf-8") as outfile:
                    with open(path, encoding="utf-8") as file:
                        for line in file.readlines():
                            result = transition_regex.match(line)
                            if result is not None:
                                action = result.group(2)
                                # Remove the action parameters between brackets
                                action = re.sub(r"\(.*\)", "", action)
                                outfile.write(
                                    f'({result.group(1)},"{action}",{result.group(3)})\n'
                                )
                            else:
                                outfile.write(line)

    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        tmp_directory = directory + "tmp/"

        # Generate pbes for every property
        for prop in properties:
            for file in os.listdir(tmp_directory):
                path = tmp_directory + file

                mcrl2_name = os.path.join(directory, mcrl2_name)
                pbes_file = path.replace(".aut", f".{prop}.pbes")

                if "_projected.renamed" in path and ".aut" in path:
                    run_program(
                        [
                            lts2pbes,
                            "-f",
                            os.path.join(directory, prop),
                            "-m",
                            mcrl2_name,
                            path,
                            pbes_file,
                        ],
                        logger,
                    )

        for prop in properties:
            result = {}

            for pbes in os.listdir(args.output):
                if "pbes" in pbes and prop in pbes:
                    print("Found pbes file: " + pbes)
                    pbes_file = os.path.join(args.output, pbes)
                    
                    result = subprocess.run([pbessolve, pbes_file], stdout=subprocess.PIPE, text=True, check=True)
                    if "true" in result.stdout:
                        true_count += 1
                    elif "false" in result.stdout:
                        false_count += 1

            print(f"True: {true_count}, False: {false_count}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
