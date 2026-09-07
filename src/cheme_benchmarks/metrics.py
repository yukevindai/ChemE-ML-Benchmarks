"""Scalar regression metrics with equal-unit aggregation and group bootstrap intervals."""
import numpy as np


def regression_metrics(y, prediction, groups, bootstrap=1000):
    y, prediction = np.asarray(y, dtype=float), np.asarray(prediction, dtype=float)
    groups = np.asarray(groups, dtype=str)
    if y.ndim != 1 or prediction.shape != y.shape or groups.shape != y.shape or not len(y):
        raise ValueError("Metrics require aligned, nonempty one-dimensional arrays")
    if not np.isfinite(y).all() or not np.isfinite(prediction).all():
        raise ValueError("Targets and predictions must be finite")
    with np.errstate(over="ignore", invalid="ignore"):
        residual = prediction - y
        squared = residual ** 2
    if not np.isfinite(squared).all():
        raise ValueError("Prediction error exceeds finite metric range")
    unique = np.unique(groups)
    group_abs = np.array([np.abs(residual[groups == g]).mean() for g in unique])
    group_sq = np.array([squared[groups == g].mean() for g in unique])
    denominator = float(np.square(y - y.mean()).sum())
    r2 = 1 - float(squared.sum()) / denominator if len(y) > 1 and denominator > 0 else None
    interval = None
    if len(unique) > 1:
        rng = np.random.default_rng(0)
        # One group draw per independent-unit proxy; do not bootstrap correlated rows.
        means = np.array([rng.choice(group_abs, size=len(unique), replace=True).mean() for _ in range(bootstrap)])
        interval = np.quantile(means, [0.025, 0.975]).tolist()
    return {"mae": float(np.abs(residual).mean()), "rmse": float(np.sqrt(squared.mean())), "r2": r2,
            "group_mae": float(group_abs.mean()), "group_rmse": float(np.sqrt(group_sq.mean())),
            "group_mae_interval95": interval, "rows": len(y), "groups": len(unique),
            "interval_scope": "Percentile bootstrap of declared groups, conditional on this fixed test set/model; proxy groups do not prove experimental independence."}
