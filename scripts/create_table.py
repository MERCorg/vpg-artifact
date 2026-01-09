import argparse
import logging
import json
import os

formatter = logging.Formatter("%(message)s")
logging.basicConfig(level=logging.DEBUG)

def average(timings: list[float]) -> float:
    """ Compute the average solving time in milliseconds from a list of timing results. """
    total = 0.0

    for result in timings:
        total += result

    return total / len(timings)

def print_escaped(value: str) -> str:
    return value.replace("_", "\\_")

def flatten(lists: list[list[int]]) -> list[int]:
    """Flattens a list of lists into a single list."""
    flat_list = []
    for sublist in lists:
        flat_list.extend(sublist)
    return flat_list

def count_winning(solution: list[dict[str, dict[str, list[int]]]]) -> tuple[int, int]:
    """Counts the number of vertices won by even and odd players."""
    won_even = 0
    won_odd = 0

    for product, winners in solution[0].items():
        won_even += len(winners.get("0", []))
        won_odd += len(winners.get("1", []))

    return won_even, won_odd

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
        
            name = json_data["experiment"]
            if name not in results:
                results.update({name: {}})

            property_name = os.path.basename(json_data["file"])
            if property_name not in results[name]:
                results[name].update({property_name: {}})

            variant = json_data["solve_variant"]
            if "solve_variant" not in results[name][property_name]:
                results[name][property_name].update({variant: {}})

            results[name][property_name][variant] = json_data

    print("\\documentclass{standalone}")
    print("\\begin{document}")

    print("\\begin{tabular}{r r|r r|r r|r r r|r r r|r r}")
    print("\\multicolumn{2}{|c|}{Case} & \\multicolumn{2}{c|}{Family} & \\multicolumn{2}{c|}{Family Left} & \\multicolumn{3}{c|}{Product} & \\multicolumn{3}{c|}{Breakdown} & \\multicolumn{2}{c}{Solution} \\\\")
    print("model & property & solve & n & solve & n & solve & max & n & zielonka & project & reachable & even & odd \\\\ \\hline")

    old_experiment = None
    for experiment, properties in results.items():

        for prop, values in properties.items():
            # Reachable family variant
            family_time = 0.0
            family_recursive_calls = 0
            family_left_optimised_time = 0.0
            family_left_optimised_recursive_calls = 0

            won_even = 0
            won_odd = 0

            # Product variant
            product_max_recursive_calls = 0
            product_recursive_calls = 0
            product_time = 0.0
            project_time = 0.0
            reachable_time = 0.0

            for variant, values in values.items():
                if variant == "family":
                    family_time = average(values["times"])
                    family_recursive_calls = max(flatten(values["recursive_calls"]))
                    
                    won_even, won_odd = count_winning(values["solution"])

                elif variant == "family-optimised-left":
                    family_left_optimised_time = average(values["times"])
                    family_left_optimised_recursive_calls = max(flatten(values["recursive_calls"]))
                elif variant == "product":
                    project_time = average(values["project_times"])
                    reachable_time = average(values["reachable_times"])
                    product_time = average(values["times"])
                    product_recursive_calls = sum(flatten(values["recursive_calls"]))
                    product_max_recursive_calls = max(flatten(values["recursive_calls"]))

            print(f"{print_escaped(experiment) if experiment != old_experiment else ''} & {print_escaped(prop)} \
                & {family_time:.1f} & {family_recursive_calls} & {family_left_optimised_time:.1f} & {family_left_optimised_recursive_calls} & {product_time:.1f} & {product_max_recursive_calls} & {product_recursive_calls} & {max(0, product_time - project_time - reachable_time):.1f} & {project_time:.1f} & {reachable_time:.1f} & {won_even} & {won_odd} \\\\")
            old_experiment = experiment

    print("\\end{tabular}")

    print("\\end{document}")

if __name__ == "__main__":
    main()