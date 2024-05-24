from click.testing import CliRunner

import psp_validation.cv_validation.cli as test_module

from tests.utils import TEST_DATA_DIR_CV, TEST_DATA_DIR_PSP

PATHWAY = (TEST_DATA_DIR_CV / "SP_PVBC-SP_PC.yaml").resolve()
SIMULATION = (TEST_DATA_DIR_PSP / "simple" / "simulation_config.json").resolve()
TARGETS = (TEST_DATA_DIR_CV / "targets.yaml").resolve()


def _test_setup(folder):
    runner = CliRunner()

    result = runner.invoke(
        test_module.setup,
        [
            "-c",
            SIMULATION,
            "-t",
            TARGETS,
            "-o",
            folder,
            "-p",
            PATHWAY,
            "-e",
            "default",
            "-n",
            "2",
            "--seed",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output

    sim_dir = folder / "SP_PVBC-SP_PC"
    assert sim_dir.exists()
    assert (sim_dir / "pairs.csv").exists()


def _test_simulation(folder):
    runner = CliRunner()

    result = runner.invoke(
        test_module.run,
        ["-c", SIMULATION, "-o", folder, "-p", PATHWAY, "-r", "2", "--nrrp", "1", "2", "-j", "4"],
    )

    assert result.exit_code == 0, result.output

    sim_dir = folder / "SP_PVBC-SP_PC"
    assert (sim_dir / "simulation_nrrp1.h5").exists()
    assert (sim_dir / "simulation_nrrp2.h5").exists()


def _test_analysis(folder):
    runner = CliRunner()

    result = runner.invoke(
        test_module.calibrate,
        ["-o", folder, "-p", PATHWAY, "-r", "10", "-n", "1", "--nrrp", "1", "2", "-j", "2"],
    )

    assert result.exit_code == 0, result.output

    fig_dir = folder / "SP_PVBC-SP_PC"
    assert fig_dir.exists()
    assert (fig_dir / "CV_regression.png").exists()
    assert (fig_dir / "lambdas.png").exists()


def test_workflow(tmp_path):
    # Run the whole workflow to not have to store data in GitLab
    _test_setup(tmp_path)
    _test_simulation(tmp_path)
    _test_analysis(tmp_path)
