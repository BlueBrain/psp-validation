"""PSP analysis toolkit.

* `psp run`     Run pair simulations for given pathway(s)
* `psp summary` Collect `psp run` summary output
* `psp plot`    Plot voltage / current traces obtained with `psp run`
"""

import logging

import click

from psp_validation import setup_logging
from psp_validation.utils import CLICK_DIR, CLICK_FILE, load_yaml
from psp_validation.version import VERSION


@click.group()
@click.version_option(version=VERSION)
@click.option("-v", "--verbose", count=True, help="-v for INFO, -vv for DEBUG")
def cli(verbose=0):
    """PSP analysis tool"""
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}[verbose]
    setup_logging(level)


@cli.command()
@click.argument("pathway_files", nargs=-1, type=CLICK_FILE, required=True)
@click.option(
    "-c",
    "--sonata_simulation_config",
    type=CLICK_FILE,
    required=True,
    help="Path to Sonata simulation config",
)
@click.option(
    "-t",
    "--targets",
    type=CLICK_FILE,
    required=True,
    help="Path to neuron groups definitions (YAML)",
)
@click.option("-o", "--output-dir", type=CLICK_DIR, required=True, help="Path to output folder")
@click.option(
    "-n", "--num-pairs", type=int, required=True, help="Sample NUM_PAIRS pairs from each pathway"
)
@click.option(
    "-r", "--num-trials", type=int, required=True, help="Run NUM_TRIALS simulations for each pair"
)
@click.option(
    "-e", "--edge-population", type=str, required=True, help="Edge population for the pathway"
)
@click.option(
    "-m",
    "--clamp",
    type=click.Choice(["current", "voltage"]),
    help="Clamp type used",
    default="current",
    show_default=True,
)
@click.option(
    "--dump-traces", is_flag=True, default=False, help="Dump PSP traces", show_default=True
)
@click.option(
    "--dump-amplitudes", is_flag=True, default=False, help="Dump PSP amplitudes", show_default=True
)
@click.option("--seed", type=int, help="Pseudo-random generator seed", default=0, show_default=True)
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=None,
    help=(
        "Number of trials to run in parallel"
        "(if not specified, trials are run sequentially; "
        "setting to 0 would use all available CPUs)"
    ),
)
def run(  # noqa: PLR0913,PLR0917 too many args / positional args
    pathway_files,
    sonata_simulation_config,
    targets,
    output_dir,
    num_pairs,
    num_trials,
    edge_population,
    clamp,
    dump_traces,
    dump_amplitudes,
    seed,
    jobs,
):
    """Obtain PSP amplitudes; derive scaling factors"""
    from psp_validation import psp

    output_dir.mkdir(parents=True, exist_ok=True)

    psp.run(
        pathway_files,
        sonata_simulation_config,
        targets,
        output_dir,
        num_pairs,
        num_trials,
        edge_population,
        clamp,
        dump_traces,
        dump_amplitudes,
        seed,
        jobs,
    )


@cli.command()
@click.argument("summary_files", nargs=-1, type=CLICK_FILE)
@click.option("-s", "--style", type=click.Choice(["default", "jira"]), help="Table style")
@click.option("--with-scaling", is_flag=True, help="Include 'scaling' column")
def summary(summary_files, with_scaling=False, style="default"):
    """Print table with `psp run` output summary"""

    def _format_value(value):
        return "N/A" if value is None else f"{value:.6g}"

    def _format_value_mean_std(value):
        return "N/A" if value is None else f"{value['mean']:.6g}±{value['std']:.6g}"

    def _add_borders(values):
        return ["", values, ""]

    headers = ["pathway", "reference", "model"]
    if with_scaling:
        headers.append("scaling")
    if style == "jira":
        print(*_add_borders(headers), sep="||")
    else:
        print(*headers, sep="\t")

    for filepath in summary_files:
        data = load_yaml(filepath)
        row = [
            data["pathway"],
            _format_value_mean_std(data.get("reference")),
            _format_value_mean_std(data.get("model")),
        ]
        if with_scaling:
            row.append(_format_value(data.get("scaling")))
        if style == "jira":
            print(*_add_borders(row), sep="|")
        else:
            print(*row, sep="\t")


@cli.command()
@click.argument("traces_files", type=CLICK_FILE, nargs=-1)
@click.option("-o", "--output-dir", type=CLICK_DIR, required=True, help="Path to output folder")
def plot(traces_files, output_dir):
    """Plot voltage traces stored in .h5 dump"""
    from psp_validation.plot import voltage_traces

    voltage_traces(traces_files, output_dir)
