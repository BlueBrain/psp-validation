"""NRRP calibration.

Generates NRRP values with different lambdas (mean of the Poisson dist),
samples pairs run with the same NRRP, calculates their mean CV (and mean Jackknife sampled CVs)
and finds best lambda to match experimentally reported CV (and an other one to match the calculated
JK CV).

See Barros-Zulaica et al 2019
"""

import logging

import numpy as np
from scipy.stats import poisson

from psp_validation.cv_validation.analyze_traces import get_all_cvs
from psp_validation.cv_validation.plots import plot_cv_regression, plot_lambdas
from psp_validation.cv_validation.utils import read_simulation_pairs

N_REPS = 50  # number of repetitions for random NRRP generation
logging.basicConfig(level=logging.INFO)
L = logging.getLogger(__name__)


def _sample_cvs(unique_nrrps, counts, all_cvs):
    """Helper function to sample the cvs for each unique nrrp."""
    cvs = []
    jk_cvs = []

    for nrrp, count in zip(unique_nrrps, counts):
        cvs.extend(np.random.choice(all_cvs[f"nrrp{nrrp}"]["CV"], size=count, replace=False))
        jk_cvs.extend(np.random.choice(all_cvs[f"nrrp{nrrp}"]["JK_CV"], size=count, replace=False))

    return np.mean(cvs), np.mean(jk_cvs)


def scan_lambdas(all_cvs, nrrp_range, n_pairs, n_reps=None):
    """Generates random Poisson samples with different lambdas.

    'lambda' is a mean of Poisson distribution that's behind NRRP values (which are always ints).
    For each individual point in the generated distribution the function samples CVs calculated
    from pairs run with the same NRRP value, and returns the mean of the sample NRRPs (which are
    technically a lambdas again as they're floats) and the mean of the corresponding sampled CVs.
    """
    if n_reps is None:
        n_reps = N_REPS

    lambdas = np.arange(nrrp_range[0], nrrp_range[1] + 0.1, 0.1)
    mean_nrrps = []
    mean_cvs = []

    for lambda_ in lambdas:
        for _ in range(n_reps):
            nrrps = poisson.rvs(lambda_ - 1, size=n_pairs, loc=1)  # generate random samples
            unique_nrrps, counts = np.unique(nrrps, return_counts=True)
            # don't go outside of simulated range
            unique_nrrps[unique_nrrps > lambdas[-1]] = lambdas[-1]
            mean_cvs.append(_sample_cvs(unique_nrrps, counts, all_cvs))
            mean_nrrps.append(np.mean(nrrps))

    mean_cvs = np.asarray(mean_cvs).T
    return np.asarray(mean_nrrps), mean_cvs[0], mean_cvs[1]


def _flatten_cvs(all_cvs, nrrp):
    """Flatten CV arrays.

    Returns 2 concatenated arrays for CVs and Jackknife sampled CVs used for regression
    (instead of the original dict, with NRRPs as keys)
    """
    cvs = np.concatenate([all_cvs[f"nrrp{i}"]["CV"] for i in range(nrrp[0], nrrp[1] + 1)])
    jk_cvs = np.concatenate([all_cvs[f"nrrp{i}"]["JK_CV"] for i in range(nrrp[0], nrrp[1] + 1)])
    return cvs, jk_cvs


def regress_cvs(cvs, jk_cvs, target_cv):
    """Regress CVs to get target Jackknife sampled CV.

    Fits a line to CV vs. Jackknife sampled CV and converts in vitro target CV to a JK CV
    (based on simulation data... I know it's a bit convoluted)
    """

    def _line(x, a, b):
        """Dummy line"""
        return a * x + b

    line_params = np.polyfit(cvs, jk_cvs, 1)
    target_jk_cv = _line(target_cv, line_params[0], line_params[1])
    reg_x = np.linspace(np.min(cvs), np.max(cvs), 100)
    reg_y = _line(reg_x, line_params[0], line_params[1])
    return target_jk_cv, reg_x, reg_y


def regress_lambdas(lambdas, cvs, target_cv, jk_cvs, target_jk_cv):
    """Find closest lamdas to match target CVs.

    Fits decaying exponential to the lambdas vs. CVs curves and finds closest lambdas to match
    target CVs
    """
    best_jk_lambda = best_lambda = None

    if np.max(cvs) <= target_cv:
        L.info(
            "All CVs are lower than %.2f, consider it univesicular (NRRP = 1) and check U_SE",
            target_cv,
        )
    else:
        best_lambda = lambdas[np.argmin(np.abs(cvs - target_cv))]
        L.info("Target CV = %.2f is best matched with NRRP = %.2f", target_cv, best_lambda)

    if np.max(jk_cvs) <= target_jk_cv:
        L.info(
            "All JK CVs are lower than %.2f, consider it univesicular (NRRP = 1) and check U_SE",
            target_jk_cv,
        )
    else:
        best_jk_lambda = lambdas[np.argmin(np.abs(jk_cvs - target_jk_cv))]
        L.info(
            "Calculated target JK CV = %.2f is best matched with NRRP = %.2f",
            target_jk_cv,
            best_jk_lambda,
        )

    return best_lambda, best_jk_lambda


def calibrate(fig_dir, all_cvs, target_cv, nrrp, n_pairs, n_reps):
    """Calibrates the nrrp according to the target_cv and plots the results."""
    # regress CVs to get target JK CV
    cvs, jk_cvs = _flatten_cvs(all_cvs, nrrp)
    target_jk_cv, reg_x, reg_y = regress_cvs(cvs, jk_cvs, target_cv)
    L.info("The reported in vitro CV was: %.2f, while the JK CV is: %.2f", target_cv, target_jk_cv)

    fig_name = fig_dir / "CV_regression.png"
    plot_cv_regression(cvs, jk_cvs, reg_x, reg_y, target_cv, target_jk_cv, fig_name)

    # scan lambdas and find the closest ones to the target CV and JK CV
    lambdas, cvs, jk_cvs = scan_lambdas(all_cvs, nrrp, n_pairs, n_reps=n_reps)
    best_lambda, best_jk_lambda = regress_lambdas(lambdas, cvs, target_cv, jk_cvs, target_jk_cv)

    fig_name = fig_dir / "lambdas.png"
    plot_lambdas(
        lambdas, cvs, target_cv, best_lambda, jk_cvs, target_jk_cv, best_jk_lambda, nrrp, fig_name
    )


def run_calibration(output_dir, pathways, nrrp, n_pairs=None, n_reps=None, n_jobs=None):
    """Run the calibration for given nrrp range"""
    pairs = read_simulation_pairs(output_dir)
    n_simulated_pairs = len(pairs)

    if n_pairs is None:
        n_pairs = int(n_simulated_pairs / 2)
    elif n_pairs >= n_simulated_pairs:
        raise ValueError(
            f"number of pairs to choose (given: {n_pairs} must be less than number "
            f"of simulated pairs (is: {n_simulated_pairs})",
        )

    # precalculate CVs from all simulations
    target_cv = pathways["reference"]["cv"]
    all_cvs = get_all_cvs(output_dir, pairs, nrrp, pathways["protocol"], n_jobs=n_jobs)

    calibrate(output_dir, all_cvs, target_cv, nrrp, n_pairs, n_reps)
