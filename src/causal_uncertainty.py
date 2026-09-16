"""
causal_uncertainty.py

Stage 3 of the R3-DE pipeline: causal inference and uncertainty
scoring.

Two responsibilities live here because they consume the same input
(the extracted Records) and both produce a per-record numeric signal:

1. Causal inference: estimate whether a given trigger plausibly caused
   a given state change, as opposed to merely co-occurring with it.
   docs/ARCHITECTURE.md describes this as DoWhy combined with linear
   regression; DoWhy is optional here (it pulls in a heavier
   dependency chain) and the module degrades gracefully to a plain
   linear-regression effect estimate when it isn't installed.

2. Uncertainty and confidence scoring: fit a Gaussian Process
   Regressor over simple structural features of each record (turn
   position, sentiment, trigger frequency) to produce a confidence
   score and noise estimate, matching the actor's stated behavior of
   attaching a confidence value to every record.
"""

from __future__ import annotations

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.linear_model import LinearRegression

from extract import Record

try:
    from dowhy import CausalModel

    _HAS_DOWHY = True
except ImportError:  # pragma: no cover - optional dependency
    _HAS_DOWHY = False


def _record_features(records: list[Record]) -> np.ndarray:
    """
    Build a small structural feature matrix per record:
    [turn_index, sentiment, trigger_frequency_in_run].
    """
    trigger_counts: dict[str, int] = {}
    for r in records:
        trigger_counts[r.trigger] = trigger_counts.get(r.trigger, 0) + 1

    features = []
    for i, r in enumerate(records):
        features.append([i, r.sentiment, trigger_counts.get(r.trigger, 1)])
    return np.array(features, dtype=float)


def estimate_causal_effect(records: list[Record]) -> dict[str, float]:
    """
    Estimate, per distinct trigger, an effect size on sentiment as a
    proxy for "did this trigger move the conversation's state".

    Returns {trigger: effect_size}. Values close to zero indicate the
    trigger is not a strong driver of state change in this run.
    """
    if len(records) < 2:
        return {r.trigger: 0.0 for r in records}

    triggers = sorted({r.trigger for r in records})
    trigger_index = {t: i for i, t in enumerate(triggers)}

    X = np.array([[trigger_index[r.trigger]] for r in records], dtype=float)
    y = np.array([r.sentiment for r in records], dtype=float)

    if _HAS_DOWHY and len(triggers) > 1:
        # DoWhy expects a dataframe and an explicit causal graph; for
        # a single-treatment / single-outcome setup this collapses to
        # the same estimate as the regression fallback, so both paths
        # are kept in sync deliberately rather than diverging.
        import pandas as pd

        df = pd.DataFrame({"trigger_idx": X.ravel(), "sentiment": y})
        model = CausalModel(
            data=df,
            treatment="trigger_idx",
            outcome="sentiment",
            common_causes=[],
        )
        identified = model.identify_effect(proceed_when_unidentifiable=True)
        estimate = model.estimate_effect(
            identified, method_name="backdoor.linear_regression"
        )
        effect = float(estimate.value)
        return {t: effect for t in triggers}

    reg = LinearRegression().fit(X, y)
    effect = float(reg.coef_[0])
    return {t: effect for t in triggers}


def score_confidence(records: list[Record]) -> list[Record]:
    """
    Fit a Gaussian Process Regressor over structural features and use
    its posterior standard deviation, inverted, as a confidence score.
    Mutates and returns the same list of records.
    """
    if not records:
        return records

    X = _record_features(records)

    if len(records) < 3:
        # Not enough points for a meaningful GP fit; assign a flat,
        # moderate confidence instead of overfitting noise.
        for r in records:
            r.confidence = 0.6
        return records

    # A pseudo-target: records with non-empty entity/trigger fields
    # and neutral-to-positive sentiment are treated as higher-quality
    # extractions during fitting. This is a proxy signal, not ground
    # truth, and only shapes the GP's notion of "surprising" records.
    pseudo_target = np.array(
        [1.0 if (r.entity and r.trigger) else 0.3 for r in records]
    )

    kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, alpha=1e-6)
    gp.fit(X, pseudo_target)

    _, std = gp.predict(X, return_std=True)
    # Lower predictive std -> higher confidence. Normalize into [0, 1].
    max_std = max(std.max(), 1e-6)
    for r, s in zip(records, std):
        r.confidence = round(float(1.0 - (s / max_std) * 0.5), 4)

    return records


if __name__ == "__main__":
    from speaker_split import split_into_turns
    from extract import run_frame_extraction, cluster_records

    sample = "Alice: Let's schedule a meeting tomorrow at 3pm.\nBob: Works for me."
    turns = split_into_turns(sample)
    records = cluster_records([run_frame_extraction(t) for t in turns])
    records = score_confidence(records)
    print(estimate_causal_effect(records))
    for r in records:
        print(r.to_dict())
