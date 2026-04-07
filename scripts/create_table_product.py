import argparse
import logging
import json
import math
import os
import re

formatter = logging.Formatter("%(message)s")
logging.basicConfig(level=logging.DEBUG)

EXPERIMENT_LABELS = {
    "VendingMachine.mcrl2": "Vending Machine",
    "elevator.mcrl2": "Elevator",
    "minepump_fts.mcrl2": "Minepump",
}

EXPERIMENT_ORDER = {
    "VendingMachine.mcrl2": 0,
    "elevator.mcrl2": 1,
    "minepump_fts.mcrl2": 2,
}

PROPERTY_PREFIX = {
    "VendingMachine.mcrl2": "chi",
    "elevator.mcrl2": "psi",
    "minepump_fts.mcrl2": "phi",
}

def average(timings: list[float]) -> float:
    """ Compute the average solving time in milliseconds from a list of timing results. """
    if len(timings) == 0:
        raise ValueError("Cannot compute average of an empty timing list")

    for result in timings:
        if result is None:
            return 0.0

    lowest_five = sorted(timings)[:5]
    mean = sum(lowest_five) / len(lowest_five)

    if mean == 0.0:
        if any(result != 0.0 for result in lowest_five):
            raise ValueError("Standard deviation check failed: mean is 0 with non-zero timings")
        return 0.0

    variance = sum((result - mean) ** 2 for result in lowest_five) / len(lowest_five)
    stddev = math.sqrt(variance)
    relative_stddev = stddev / mean

    if relative_stddev > 0.10 and mean >= 0.01:
        print(f"Lowest 5 timings: {lowest_five}")
        raise ValueError(
            f"Standard deviation of lowest 5 timings too high: {relative_stddev * 100:.2f}% (> 10%)"
        )

    return mean

def print_escaped(value: str) -> str:
    return value.replace("_", "\\_")

def flatten(lists: list[list[int]]) -> list[int]:
    """Flattens a list of lists into a single list."""
    flat_list = []
    for sublist in lists:
        flat_list.extend(sublist)
    return flat_list

def property_number(property_name: str) -> int:
    match = re.search(r"(\d+)", property_name)
    if match is None:
        return 0
    return int(match.group(1))

def format_property(experiment: str, property_name: str) -> str:
    prefix = PROPERTY_PREFIX.get(experiment, "prop")
    return f"${chr(92)}{prefix}_{property_number(property_name)}$"

def load_results(path: str) -> dict[str, dict[str, dict[str, dict]]]:
    results: dict[str, dict[str, dict[str, dict]]] = {}

    with open(path, "r", encoding="utf-8") as json_file:
        for line in json_file:
            json_data = json.loads(line)

            experiment = json_data["experiment"]
            results.setdefault(experiment, {})

            property_name = os.path.basename(json_data["file"])
            results[experiment].setdefault(property_name, {})

            variant = json_data["solve_variant"]
            results[experiment][property_name][variant] = json_data

    return results

def product_metrics(entry: dict | None) -> dict[str, float | int]:
    if entry is None:
        return {
            "solve": 0.0,
            "max_recursive_calls": 0,
            "recursive_calls": 0,
            "zielonka": 0.0,
            "project": 0.0,
            "reachable": 0.0,
        }

    recursive_calls = flatten(entry["recursive_calls"])
    project_time = average(entry["project_times"])
    reachable_time = average(entry["reachable_times"])
    solve_time = average(entry["times"])

    return {
        "solve": solve_time,
        "max_recursive_calls": max(recursive_calls),
        "recursive_calls": int(sum(recursive_calls) / len(entry["recursive_calls"])),
        "zielonka": max(0.0, solve_time - project_time - reachable_time),
        "project": project_time,
        "reachable": reachable_time,
    }

def main():
    parser = argparse.ArgumentParser(
        prog="create_table_product.py",
        description="Compare product-only solving results with and without reachability as a LaTeX table",
        epilog="",
    )

    parser.add_argument(
        "reachable_input", action="store", type=str,
        help="JSON lines file with regular product results, including reachability timings"
    )
    parser.add_argument(
        "no_reachability_input", action="store", type=str,
        help="JSON lines file with product results computed without reachability"
    )

    args = parser.parse_args()

    reachable_results = load_results(args.reachable_input)
    no_reachability_results = load_results(args.no_reachability_input)

    all_experiments = sorted(
        set(reachable_results) | set(no_reachability_results),
        key=lambda experiment: (EXPERIMENT_ORDER.get(experiment, 99), experiment),
    )

    print("\\documentclass{standalone}")
    print("\\begin{document}")

    print("\\begin{tabular}{r r|r r r||r r r r}")
    print("model & property & solve & zielonka & project & solve & zielonka & project & reachability \\\\ \\hline")

    old_experiment = None
    for experiment in all_experiments:
        reachable_properties = reachable_results.get(experiment, {})
        no_reachability_properties = no_reachability_results.get(experiment, {})
        all_properties = sorted(
            set(reachable_properties) | set(no_reachability_properties),
            key=lambda property_name: (property_number(property_name), property_name),
        )

        for property_name in all_properties:
            reachable_metrics = product_metrics(reachable_properties.get(property_name, {}).get("product"))
            no_reachability_metrics = product_metrics(no_reachability_properties.get(property_name, {}).get("product"))

            model_label = EXPERIMENT_LABELS.get(experiment, print_escaped(experiment))
            property_label = format_property(experiment, property_name)

            row = (
                f"{model_label if experiment != old_experiment else ''} & {property_label} & "
                f"{no_reachability_metrics['solve']:.1f} & {no_reachability_metrics['zielonka']:.1f} & {no_reachability_metrics['project']:.1f} & "
                f"{reachable_metrics['solve']:.1f} & "
                f"{reachable_metrics['zielonka']:.1f} & {reachable_metrics['project']:.1f} & {reachable_metrics['reachable']:.1f} \\\\" 
            )
            print(row)
            old_experiment = experiment

        print("\\hline")

    print("\\end{tabular}")

    print("\\end{document}")

if __name__ == "__main__":
    main()