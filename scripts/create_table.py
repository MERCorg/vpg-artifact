import argparse
import logging
import json
import os

formatter = logging.Formatter("%(message)s")
logging.basicConfig(level=logging.DEBUG)

def average(timings):
    """ Compute the average solving time in milliseconds from a list of timing results. """
    total = 0.0

    for result in timings:
        total += result

    return total / len(timings) * 1000.0


def main():
    parser = argparse.ArgumentParser(
        prog="create_table.py",
        description="Print JSON output of run.py as a LaTeX table",
        epilog="",
    )

    parser.add_argument(
        "input", action="store", type=str
    )

    args = parser.parse_args()

    results = {}
    with open(args.input, "r", encoding="utf-8") as json_file:
        # Read line by line and parse each line as JSON
        for line in json_file:
            json_data = json.loads(line)

            

            results.update({json_data["experiment"]: { os.path.basename(json_data["file"]): json_data } })

    print(results)

    print("\\begin{table}[h]")
    print("\\begin{tabular}{r|r|r|r|r|r}")
    print("model & property & family (max) & family-left-optimised (max) & product (max, total) \\\\ \\hline")

    old_experiment = None
    for experiment, properties in results.items():

        for prop, values in properties.items():
            # Reachable family variant
            family_time = 0.0
            family_recursive_calls = 0
            family_left_optimised_time = 0.0
            family_left_optimised_recursive_calls = 0

            # Product variant
            product_max_recursive_calls = 0
            product_recursive_calls = 0
            reachable_time = 0.0

            for algorithm, timings in values.items():
                if algorithm == "family":
                    family_time = average(timings["times"])
                elif algorithm == "family-left-optimised":
                    family_left_optimised_time = average(timings["times"])
                elif algorithm == "product":
                    reachable_time = average(timings["times"])

            print(f"{experiment if experiment != old_experiment else ''} & {prop} \
                & {family_time:.1f} ({family_recursive_calls}) & {family_left_optimised_time:.1f} ({family_left_optimised_recursive_calls}) & {reachable_time:.1f} ({product_max_recursive_calls}, {product_recursive_calls}) \\\\")
            old_experiment = experiment

    print("\\end{tabular}")
    print("\\end{table}")

if __name__ == "__main__":
    main()