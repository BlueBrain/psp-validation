"""NRRP calibration related plots"""

import matplotlib as mpl
import numpy as np
import seaborn as sns

mpl.use("Agg")
import matplotlib.pyplot as plt

sns.set(style="ticks", context="notebook")


def plot_cv_regression(cvs, jk_cvs, reg_x, reg_y, target_cv, target_jk_cv, fig_name):
    """Plots regression of CV vs. Jackknife sampled CV"""
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(cvs, jk_cvs, marker=".", s=30, edgecolor="none", label="in silico data")
    ax.plot(reg_x, reg_y, "k--", label="regression line")
    ax.scatter(target_cv, target_jk_cv, s=50, marker="x", label="target CV")
    ax.axvline(target_cv, color="gray", ls="--", lw=0.5, alpha=0.75)
    ax.axhline(target_jk_cv, color="gray", ls="--", lw=0.5, alpha=0.75)
    ax.legend(frameon=False)
    ax.set_xlabel("CV")
    ax.set_xlim([np.min(reg_x), np.max(reg_x)])
    ax.set_ylabel("JK CV")
    ax.set_ylim([np.min(reg_y), np.max(reg_y)])
    sns.despine(offset=5, trim=True)
    fig.savefig(fig_name, bbox_inches="tight", dpi=100)
    plt.close(fig)


def plot_lambdas(  # noqa: PLR0913,PLR0917 too many args / positional args
    lambdas, cvs, target_cv, best_lambda, jk_cvs, target_jk_cv, best_jk_lambda, nrrp, fig_name
):
    """Plots CV and Jackknife sampled CVs against lambdas (and fitting curves)"""
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(2, 1, 1)
    ax.scatter(lambdas, cvs, marker=".", s=20, edgecolor="none")
    ax.axhline(target_cv, color="red", ls="--", label=f"target CV: {target_cv:.2f}")
    if best_lambda is not None:
        ax.axvline(best_lambda, color="black", ls="--", label=f"lambda: {best_lambda:2f}")
    ax.set_xlim(nrrp)  # NRRP range is hard coded in `setsim.py` right now
    ax.set_ylabel("CV")
    ax.legend(frameon=False, loc=1)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.scatter(lambdas, jk_cvs, marker=".", s=20, edgecolor="none")
    ax2.axhline(target_jk_cv, color="red", ls="--", label=f"target JK CV: {target_jk_cv:.2f}")
    if best_jk_lambda is not None:
        ax2.axvline(
            best_jk_lambda, color="black", ls="--", label=f"lambda (JK): {best_jk_lambda:.2f}"
        )
    ax2.set_xlabel("lambda")
    ax2.set_xlim(nrrp)
    ax2.set_ylabel("JK CV")
    ax2.legend(frameon=False, loc=1)
    sns.despine(offset=5, trim=True)
    fig.tight_layout()
    fig.savefig(fig_name, bbox_inches="tight", dpi=100)
    plt.close(fig)
