import argparse
import os
import logging
import shutil
import re
import subprocess
import json

from library import MyLogger, run_program
from prepare import EXPERIMENTS

# A regex matching in=out
mapping_regex = re.compile(r"(.*)=(.*)")

# A regex matching a transition in the aut format '(from, action, to)'
transition_regex = re.compile(r"\(([0-9]*), \"(.*)\", ([0-9]*)\)")

# Extract the product (zeroes and ones) from the pbes file: minepump_fts_projected.renamed_0000001000.phi1.mcf.pbes
product_regex = re.compile(r".*_projected\.renamed_([01]+)\..*\.pbes")


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

        verify_family_solver(merc_vpg, logger, tmp_directory)

        # This projection function is not in the submodule yet, but only in the main branch.
        #project_fts(merc_vpg, logger, tmp_directory, directory)

        rename_projections(tmp_directory)

    for experiment in EXPERIMENTS:
        directory, mcrl2_name, properties = experiment

        tmp_directory = directory + "tmp/"

        generate_pbes(lts2pbes, logger, directory, mcrl2_name, properties, tmp_directory)

        solve_pbes(args, pbessolve, directory, properties, tmp_directory)

    # Open both the results.json and solution.json files and compare the results for each property.
    check_solution(args, logger)

def check_solution(args, logger):
    results = []
    with open(os.path.join(args.output, "results.json"), encoding="utf-8") as f:
        results = [json.loads(line) for line in f]

    with open(os.path.join(args.output, "solution.json"), encoding="utf-8") as f:
        for line in f:
            solution = json.loads(line)

            for result in results:
                name = os.path.splitext(solution["property"])[0]

                if name in result["file"]:
                    actual = result["solution"][0]
                    expected = solution["solution"]

                    for key, value in expected.items():
                        if key not in actual:
                            continue             

                        if value != actual[key]:
                            logger.error(
                                f"Verification failed for {name}, key: {key}, expected: {value}, actual: {actual[key]}"
                            )

def solve_pbes(args, pbessolve, directory, properties, tmp_directory):
    for prop in properties:
        result = {"experiment": directory, "property": prop, "solution": {}}

        for pbes in os.listdir(tmp_directory):
            if "pbes" in pbes and prop in pbes:
                print("Found pbes file: " + pbes)

                product = None
                match = product_regex.match(pbes)
                if match:
                    product = match.group(1)

                pbes_file = os.path.join(tmp_directory, pbes)

                proc = subprocess.run(
                        [pbessolve, pbes_file],
                        stdout=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                if "true" in proc.stdout:
                    result["solution"][product] = {"0": [0], "1": []}
                elif "false" in proc.stdout:
                    result["solution"][product] = {"0": [], "1": [0]}

        with open(
                os.path.join(args.output, "solution.json"), "a", encoding="utf-8"
            ) as f:
            json.dump(result, f)
            f.write("\n")

def generate_pbes(lts2pbes, logger, directory, mcrl2_name, properties, tmp_directory):
    for prop in properties:
        for file in os.listdir(tmp_directory):
            path = tmp_directory + file

            mcrl2_name = os.path.join(directory, mcrl2_name)
            pbes_file = path.replace(".aut", f".{prop}.pbes")

            if "_projected.renamed" in path and ".aut" in path:
                print("Generating pbes for " + path + " and " + prop)
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

def rename_projections(tmp_directory):
    for file in os.listdir(tmp_directory):
        path = tmp_directory + file

        if "_projected" in path and "renamed" not in path:
            aut_renamed_file = path.replace("_projected", "_projected.renamed")

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

def verify_family_solver(merc_vpg, logger, tmp_directory):
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
                        logger,
                    )
       
def project_fts(merc_vpg, logger, tmp_directory, directory):  
    for file in os.listdir(tmp_directory):
        path = tmp_directory + file      
                
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Interrupted program")
