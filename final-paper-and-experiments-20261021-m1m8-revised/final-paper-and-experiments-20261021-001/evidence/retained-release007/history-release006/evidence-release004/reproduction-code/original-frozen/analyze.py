"""Frozen, question-grouped UI Traces predictive reanalysis.

This module does not acquire data or execute agents. ``analyze`` consumes an
already admitted canonical manifest. Production configuration is fixed; small
overrides require the explicit ``synthetic_unit_test`` fixture tag. The caller
must provide the protocol/source seal and enforce the external 1,800-second
process deadline before invoking this function on the real corpus.

All selectors use validation data only. Every planned fit must finish before
test predictions are produced. Retained candidates keep both their fitted
estimator and their original feature representation. No models are serialized.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import re
import time
from typing import Any, Optional
import warnings

import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from .features import DEFAULT_ORIGIN, delay, feature_names, features, project, shuffle_types
except ImportError:
    from features import DEFAULT_ORIGIN, delay, feature_names, features, project, shuffle_types


DEFAULT_CONFIG = {
    "fixture_tag": None,
    "expected_rows": 4200,
    "expected_classes": 14,
    "expected_labels": None,  # Exact source identities are checked by admission.
    "seed": 20261008,
    "split_salt": "20261008",
    "origin": DEFAULT_ORIGIN,
    "minimum_questions": {"train": 20, "validation": 10, "test": 10},
    "epsilon": 1e-6,
    "logistic_C": [0.1, 1.0, 10.0],
    "logistic_max_iter": 1000,
    "logistic_tol": 1e-6,
    "rf_trees": 200,
    "rf_max_depth": 12,
    "rf_min_samples_leaf": 2,
    "rf_max_features": "sqrt",
    "noise_max_ms": 5000.0,
    "noise_realizations": [0, 1, 2],
    "bootstrap_draws": 3000,
    "interval_percent": 98.33333333333333,
    "selection_tie_tolerance": 1e-12,
    "include_action_only": True,
    "include_type_shuffle": True,
    "max_fit_count": 19,
}
_FIXTURE_KEYS = frozenset((
    "expected_rows", "expected_classes", "minimum_questions", "rf_trees", "bootstrap_draws"
))
_OPTION_KEYS = frozenset(("include_action_only", "include_type_shuffle", "expected_labels"))
_PARTITIONS = ("train", "validation", "test")
_ORIGINAL_PARTITIONS = ("train", "val", "test")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
EFFECT_NAMES = ("observer_expansion", "sequence_increment", "timestamp_adaptation")


class AnalysisError(ValueError):
    """Admission, configuration, or fit-plan failure; callers must record HOLD."""


def default_config() -> dict[str, Any]:
    """Return the complete JSON-serializable configuration for sealing."""
    return deepcopy(DEFAULT_CONFIG)


def _configuration(config: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    result = default_config()
    if config is not None:
        if not isinstance(config, Mapping):
            raise AnalysisError("config must be a mapping")
        unknown = set(config) - set(result)
        if unknown:
            raise AnalysisError(f"unknown configuration fields: {sorted(unknown)}")
        result.update(deepcopy(dict(config)))
    fixture = result["fixture_tag"] == "synthetic_unit_test"
    if result["fixture_tag"] is not None and not fixture:
        raise AnalysisError("fixture_tag must be null or 'synthetic_unit_test'")
    allowed = _OPTION_KEYS | (_FIXTURE_KEYS if fixture else frozenset()) | {"fixture_tag"}
    for key, original in DEFAULT_CONFIG.items():
        if key not in allowed and result[key] != original:
            raise AnalysisError(f"frozen production configuration cannot change {key}")
    for key in _FIXTURE_KEYS - {"minimum_questions"}:
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise AnalysisError(f"{key} must be a positive integer")
    if result["expected_classes"] < 2:
        raise AnalysisError("classification requires at least two canonical model identities")
    minima = result["minimum_questions"]
    if not isinstance(minima, Mapping) or set(minima) != set(_PARTITIONS):
        raise AnalysisError("minimum_questions must contain train, validation, and test")
    for partition, value in minima.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise AnalysisError(f"minimum_questions[{partition}] must be positive")
    for key in ("include_action_only", "include_type_shuffle"):
        if not isinstance(result[key], bool):
            raise AnalysisError(f"{key} must be boolean")
    labels = result["expected_labels"]
    if labels is not None:
        if (not isinstance(labels, list) or any(not isinstance(x, str) or not x for x in labels)
                or len(set(labels)) != len(labels) or len(labels) != result["expected_classes"]):
            raise AnalysisError("expected_labels must list each canonical model exactly once")
    return result


def split_for_question(question_hash: str) -> str:
    """The sealed split, shared by every model and repeat of this question."""
    if not isinstance(question_hash, str) or not _HASH_RE.fullmatch(question_hash):
        raise AnalysisError("question_hash must be a lowercase SHA256 hex string")
    digest = hashlib.sha256(f"20261008:{question_hash}".encode("utf-8")).hexdigest()
    bucket = int(digest[:16], 16) % 100
    return "train" if bucket < 50 else "validation" if bucket < 75 else "test"


def question_weights(question_hashes: Sequence[str]) -> np.ndarray:
    """Equal total weight per question, normalized to mean row weight one."""
    if len(question_hashes) == 0:
        raise AnalysisError("cannot weight an empty partition")
    counts = Counter(question_hashes)
    scale = len(question_hashes) / len(counts)
    return np.array([scale / counts[q] for q in question_hashes], dtype=np.float64)


def question_values(values: Sequence[float], question_hashes: Sequence[str]) -> dict[str, float]:
    """Average rows within a question; output order is reproducibly sorted."""
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) != len(question_hashes) or not np.isfinite(array).all():
        raise AnalysisError("question values require aligned finite row values")
    if len(array) == 0:
        raise AnalysisError("cannot summarize an empty partition")
    groups: dict[str, list[float]] = {}
    for question, value in zip(question_hashes, array):
        groups.setdefault(question, []).append(float(value))
    return {question: float(np.mean(groups[question])) for question in sorted(groups)}


def question_mean(values: Sequence[float], question_hashes: Sequence[str]) -> float:
    return float(np.mean(list(question_values(values, question_hashes).values())))


def smooth_probabilities(probabilities: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """Add the fixed epsilon to every class and normalize each row."""
    array = np.asarray(probabilities, dtype=np.float64)
    if (array.ndim != 2 or array.shape[1] < 2 or not np.isfinite(array).all()
            or np.any(array < 0) or np.any(array.sum(axis=1) <= 0)):
        raise AnalysisError("probabilities must be finite nonnegative nonempty distributions")
    if not np.isfinite(epsilon) or not 0 < epsilon < 1:
        raise AnalysisError("epsilon must lie strictly between zero and one")
    smoothed = array + epsilon
    return smoothed / smoothed.sum(axis=1, keepdims=True)


def row_log_losses(probabilities: np.ndarray, encoded_labels: Sequence[int], epsilon: float = 1e-6) -> np.ndarray:
    array = np.asarray(probabilities, dtype=np.float64)
    encoded = np.asarray(encoded_labels, dtype=np.int64)
    if (array.ndim != 2 or encoded.ndim != 1 or len(array) != len(encoded)
            or not np.isfinite(array).all() or np.any(array < 0)
            or np.any(encoded < 0) or np.any(encoded >= array.shape[1])):
        raise AnalysisError("loss inputs are invalid or misaligned")
    return -np.log(np.clip(array[np.arange(len(encoded)), encoded], epsilon, 1.0))


def bootstrap_question_effects(
    per_question: Mapping[str, Sequence[float]], draws: int = 3000,
    seed: int = 20261008, interval_percent: float = 98.33333333333333,
) -> dict[str, Any]:
    """Common paired question resamples for the three frozen primary effects."""
    if not per_question:
        raise AnalysisError("bootstrap requires at least one question")
    questions = sorted(per_question)
    matrix = np.array([per_question[q] for q in questions], dtype=np.float64)
    if matrix.shape != (len(questions), 3) or not np.isfinite(matrix).all():
        raise AnalysisError("bootstrap requires three finite effects per question")
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 1:
        raise AnalysisError("bootstrap draws must be positive")
    if not 0 < interval_percent < 100:
        raise AnalysisError("interval_percent must be between zero and 100")
    rng = np.random.default_rng(seed)
    # One resample is shared by all contrasts, preserving their pairing.
    resamples = np.empty((draws, 3), dtype=np.float64)
    for draw in range(draws):
        indices = rng.integers(0, len(questions), size=len(questions))
        resamples[draw] = matrix[indices].mean(axis=0)
    tail = (100.0 - interval_percent) / 2.0
    limits = np.percentile(resamples, [tail, 100.0 - tail], axis=0, method="linear")
    return {
        "unit": "equal_weight_question",
        "interval_kind": "percentile_resampling_stability",
        "conditional_on": ["training_and_selection", "fixed_noise_realizations"],
        "population_interpretation_requires": "exchangeable_questions",
        "family_allocation": "three_contrast_Bonferroni",
        "question_count": len(questions), "draws": draws, "seed": seed,
        "interval_percent": interval_percent,
        "effects": {
            name: {"mean": float(matrix[:, i].mean()), "lower": float(limits[0, i]),
                   "upper": float(limits[1, i])}
            for i, name in enumerate(EFFECT_NAMES)
        },
    }


@dataclass
class _Row:
    identifier: str
    label: str
    question_hash: str
    episode: Mapping[str, Any]
    partition: str
    failed: Optional[bool]
    error_present: Optional[bool]
    result_present: Optional[bool]
    original_split: Optional[str]


def _original_split_coverage(rows: list[_Row]) -> dict[str, Any]:
    """Descriptive public-split overlap; never consulted by a predictor."""
    available = [row for row in rows if row.original_split is not None]
    question_sets = {
        original: {row.question_hash for row in available if row.original_split == original}
        for original in _ORIGINAL_PARTITIONS
    }
    cross_sets = {
        original: {
            partition: {row.question_hash for row in available
                        if row.original_split == original and row.partition == partition}
            for partition in _PARTITIONS
        }
        for original in _ORIGINAL_PARTITIONS
    }
    intersections = {}
    for index, first in enumerate(_ORIGINAL_PARTITIONS):
        for second in _ORIGINAL_PARTITIONS[index + 1:]:
            shared = sorted(question_sets[first] & question_sets[second])
            intersections[f"{first}__{second}"] = {"questions": len(shared), "question_hashes": shared}
    all_shared = sorted(set.intersection(*question_sets.values()))
    status = "NR" if not available else "complete" if len(available) == len(rows) else "partial"
    return {
        "status": status,
        "reason": "original_public_split_not_provided" if status == "NR" else None,
        "descriptive_only": True,
        "available_rows": len(available), "missing_rows": len(rows) - len(available),
        "row_counts": {original: sum(row.original_split == original for row in available)
                       for original in _ORIGINAL_PARTITIONS},
        "distinct_question_counts": {original: len(questions) for original, questions in question_sets.items()},
        "question_hashes": {original: sorted(questions) for original, questions in question_sets.items()},
        "pairwise_question_intersections": intersections,
        "all_three_question_intersection": {"questions": len(all_shared), "question_hashes": all_shared},
        "original_split_by_new_partition": {
            "row_counts": {
                original: {partition: sum(row.original_split == original and row.partition == partition
                                          for row in available) for partition in _PARTITIONS}
                for original in _ORIGINAL_PARTITIONS
            },
            "distinct_question_counts": {
                original: {partition: len(questions) for partition, questions in partitions.items()}
                for original, partitions in cross_sets.items()
            },
            "question_hashes": {
                original: {partition: sorted(questions) for partition, questions in partitions.items()}
                for original, partitions in cross_sets.items()
            },
        },
    }


def _admit_rows(rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]):
    materialized = list(rows)
    if len(materialized) != config["expected_rows"]:
        raise AnalysisError(f"expected {config['expected_rows']} canonical rows, got {len(materialized)}")
    admitted = []
    identifiers = set()
    for row in materialized:
        if not isinstance(row, Mapping):
            raise AnalysisError("each canonical row must be a mapping")
        identifier, label, question = row.get("id"), row.get("label"), row.get("question_hash")
        if not isinstance(identifier, str) or not identifier:
            raise AnalysisError("each canonical row requires a nonempty id")
        if identifier in identifiers:
            raise AnalysisError(f"duplicate canonical id: {identifier}")
        identifiers.add(identifier)
        if not isinstance(label, str) or not label or label.strip() != label:
            raise AnalysisError(f"invalid model identity for {identifier}")
        if not isinstance(row.get("episode"), Mapping):
            raise AnalysisError(f"episode must be a mapping for {identifier}, including failures")
        partition = split_for_question(question)
        original_split = row.get("split")
        if original_split is not None and original_split not in _ORIGINAL_PARTITIONS:
            raise AnalysisError("original public split must be train, val, test, or absent in fixtures")
        if original_split is None and config["fixture_tag"] is None:
            raise AnalysisError("production canonical rows require their original public split")
        failed = row.get("failed")
        error_present, result_present = row.get("error_present"), row.get("result_present")
        for field, value in (("error_present", error_present), ("result_present", result_present)):
            if value is not None and not isinstance(value, bool):
                raise AnalysisError(f"optional {field} descriptor must be boolean or null")
        if "failed" not in row and error_present is not None and result_present is not None:
            failed = bool(error_present or not result_present)
        if failed is not None and not isinstance(failed, bool):
            raise AnalysisError("optional failed descriptor must be boolean or null")
        admitted.append(_Row(identifier, label, question, row["episode"], partition, failed,
                             error_present, result_present, original_split))
    admitted.sort(key=lambda row: row.identifier)
    labels = sorted({row.label for row in admitted})
    if len(labels) != config["expected_classes"]:
        raise AnalysisError(f"expected {config['expected_classes']} model identities, got {len(labels)}")
    if config["expected_labels"] is not None and labels != sorted(config["expected_labels"]):
        raise AnalysisError("canonical model identities do not match expected_labels")
    class_coverage = {}
    for label in labels:
        class_coverage[label] = {}
        for partition in _PARTITIONS:
            selected = [row for row in admitted if row.label == label and row.partition == partition]
            unique_questions = len({row.question_hash for row in selected})
            class_coverage[label][partition] = {"rows": len(selected), "questions": unique_questions}
            if unique_questions < config["minimum_questions"][partition]:
                raise AnalysisError(f"insufficient distinct questions: {label} {partition} has {unique_questions}")
    question_model_repeats: dict[str, dict[str, int]] = {}
    for row in admitted:
        question_model_repeats.setdefault(row.question_hash, {}).setdefault(row.label, 0)
        question_model_repeats[row.question_hash][row.label] += 1
    coverage = {
        "classes": class_coverage,
        "partitions": {
            partition: {"rows": sum(row.partition == partition for row in admitted),
                        "questions": len({row.question_hash for row in admitted if row.partition == partition})}
            for partition in _PARTITIONS
        },
        "question_model_repeats": {
            question: {"partition": split_for_question(question), "models": question_model_repeats[question]}
            for question in sorted(question_model_repeats)
        },
        "original_public_split": _original_split_coverage(admitted),
    }
    return admitted, labels, coverage


def _json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


class _FitLedger:
    def __init__(self, path: Path, planned: int):
        self.path, self.planned, self.entries = path, planned, []

    def start(self, name: str, representation: str, architecture: Mapping[str, Any]) -> dict[str, Any]:
        if len(self.entries) >= self.planned:
            raise AnalysisError("attempted fit exceeds complete frozen fit plan")
        entry = {"fit_id": len(self.entries) + 1, "name": name,
                 "representation": representation, "architecture": dict(architecture), "status": "running"}
        self.entries.append(entry)
        _json_write(self.path, {"planned": self.planned, "fits": self.entries})
        return entry

    def finish(self, entry: dict[str, Any], seconds: float, convergence: list[str], error: Optional[str] = None):
        entry.update(status="failed" if error is not None else "complete", seconds=seconds,
                     convergence_warnings=convergence, convergence_warning_accepted=True)
        if error is not None:
            entry["error"] = error
        _json_write(self.path, {"planned": self.planned, "fits": self.entries})

    def require_complete(self):
        if len(self.entries) != self.planned or any(entry["status"] != "complete" for entry in self.entries):
            raise AnalysisError("incomplete candidate plan; test predictions are prohibited")


@dataclass
class _Model:
    name: str
    estimator: Any
    representation: str
    architecture: dict[str, Any]
    fit_id: int

    def descriptor(self) -> dict[str, Any]:
        return {"name": self.name, "representation": self.representation,
                "architecture": self.architecture, "fit_id": self.fit_id}


def _architectures(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"kind": "logistic", "C": c, "max_iter": config["logistic_max_iter"],
             "tol": config["logistic_tol"], "random_state": config["seed"], "n_jobs": 1}
            for c in config["logistic_C"]] + [{
                "kind": "random_forest", "n_estimators": config["rf_trees"],
                "max_depth": config["rf_max_depth"], "min_samples_leaf": config["rf_min_samples_leaf"],
                "max_features": config["rf_max_features"], "random_state": config["seed"], "n_jobs": 1,
            }]


def _estimator(architecture: Mapping[str, Any], config: Mapping[str, Any]):
    if architecture["kind"] == "logistic":
        return Pipeline([
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(
                C=architecture["C"], max_iter=config["logistic_max_iter"],
                tol=config["logistic_tol"], random_state=config["seed"], n_jobs=1,
            )),
        ])
    return RandomForestClassifier(
        n_estimators=config["rf_trees"], max_depth=config["rf_max_depth"],
        min_samples_leaf=config["rf_min_samples_leaf"], max_features=config["rf_max_features"],
        random_state=config["seed"], n_jobs=1,
    )


def _fit(
    name: str, representation: str, architecture: dict[str, Any], estimator: Any,
    matrices: Mapping[str, np.ndarray], indices: np.ndarray, encoded: np.ndarray,
    weights: np.ndarray, ledger: _FitLedger,
) -> _Model:
    entry = ledger.start(name, representation, architecture)
    start = time.monotonic()
    convergence: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            if isinstance(estimator, Pipeline):
                estimator.fit(matrices[representation][indices], encoded[indices],
                              scale__sample_weight=weights, classifier__sample_weight=weights)
            else:
                estimator.fit(matrices[representation][indices], encoded[indices], sample_weight=weights)
        convergence = [str(warning.message) for warning in caught
                       if issubclass(warning.category, ConvergenceWarning)]
    except Exception as exc:
        ledger.finish(entry, time.monotonic() - start, convergence, f"{type(exc).__name__}: {exc}")
        raise AnalysisError(f"fit failed; no retry or partial selector: {name}") from exc
    ledger.finish(entry, time.monotonic() - start, convergence)
    return _Model(name, estimator, representation, architecture, entry["fit_id"])


def _probabilities(model: _Model, matrices: Mapping[str, np.ndarray], indices: np.ndarray,
                   class_count: int, epsilon: float) -> np.ndarray:
    raw = model.estimator.predict_proba(matrices[model.representation][indices])
    model_classes = np.asarray(model.estimator.classes_, dtype=np.int64)
    if sorted(model_classes.tolist()) != list(range(class_count)):
        raise AnalysisError("fitted classifier omitted or changed a canonical class")
    aligned = np.zeros((len(indices), class_count), dtype=np.float64)
    aligned[:, model_classes] = raw
    return smooth_probabilities(aligned, epsilon)


def _choose(scored_entries: Sequence[dict[str, Any]], tolerance: float = 1e-12) -> int:
    if not scored_entries or any(not np.isfinite(entry["validation_log_loss"]) for entry in scored_entries):
        raise AnalysisError("selector requires every planned finite validation loss")
    best = min(entry["validation_log_loss"] for entry in scored_entries)
    return next(index for index, entry in enumerate(scored_entries)
                if entry["validation_log_loss"] <= best + tolerance)


def _select(
    representation: str, matrices: Mapping[str, np.ndarray], train: np.ndarray, validation: np.ndarray,
    encoded: np.ndarray, train_weights: np.ndarray, validation_questions: list[str],
    labels: list[str], config: Mapping[str, Any], ledger: _FitLedger,
    retained: Optional[_Model] = None,
):
    models, scored = [], []
    for architecture in _architectures(config):
        suffix = f"logistic_C_{architecture['C']:g}" if architecture["kind"] == "logistic" else "random_forest"
        name = f"{representation}/{suffix}"
        model = _fit(name, representation, architecture, _estimator(architecture, config),
                     matrices, train, encoded, train_weights, ledger)
        models.append(model)
    # The declared four new candidates precede the retained fitted candidate.
    if retained is not None:
        models.append(retained)
    for index, model in enumerate(models):
        probabilities = _probabilities(model, matrices, validation, len(labels), config["epsilon"])
        losses = row_log_losses(probabilities, encoded[validation], config["epsilon"])
        scored.append({"declared_order": index, "retained": index == 4,
                       "model": model.descriptor(),
                       "validation_log_loss": question_mean(losses, validation_questions)})
    chosen = _choose(scored, config["selection_tie_tolerance"])
    return models[chosen], {"candidates": scored, "selected_order": chosen,
                            "selected_model": models[chosen].descriptor()}


def _matrices(rows: list[_Row], config: Mapping[str, Any], realization: Optional[int] = None,
              type_shuffle: bool = False):
    values: dict[str, list[np.ndarray]] = {
        "single_coarse": [], "single_combined": [], "broad_combined": [], "single_action_only": []
    }
    empty_single, empty_other = [], []
    for row in rows:
        single = project(row.episode, "single_origin_js", config["origin"])
        other = project(row.episode, "other_origins_js", config["origin"])
        empty_single.append(not single)
        empty_other.append(not other)
        if realization is not None:
            # Independent streams give every retained timestamp its own draw;
            # a row's paired clean/adapted predictions share these matrices.
            stem = f"{config['seed']}:noise:{realization}:{row.identifier}"
            single = delay(single, config["noise_max_ms"], f"{stem}:single_origin_js")
            other = delay(other, config["noise_max_ms"], f"{stem}:other_origins_js")
        if type_shuffle:
            stem = f"{config['seed']}:type_shuffle:{row.identifier}"
            single = shuffle_types(single, f"{stem}:single_origin_js")
            other = shuffle_types(other, f"{stem}:other_origins_js")
        coarse = features(single, "coarse")
        combined = features(single, "combined")
        other_combined = features(other, "combined")
        values["single_coarse"].append(coarse)
        values["single_combined"].append(combined)
        values["broad_combined"].append(np.concatenate((combined, other_combined)))
        values["single_action_only"].append(features(single, "action_only"))
    matrices = {name: np.asarray(items, dtype=np.float64) for name, items in values.items()}
    names = {
        "single_coarse": list(feature_names("coarse")),
        "single_combined": list(feature_names("combined")),
        "broad_combined": [f"single::{name}" for name in feature_names("combined")]
                          + [f"other::{name}" for name in feature_names("combined")],
        "single_action_only": list(feature_names("action_only")),
    }
    for representation, matrix in matrices.items():
        if matrix.shape != (len(rows), len(names[representation])) or not np.isfinite(matrix).all():
            raise AnalysisError(f"invalid restricted features for {representation}")
    return matrices, names, {"empty_single": empty_single, "empty_other": empty_other}


def _score(probabilities: np.ndarray, encoded: np.ndarray, questions: list[str],
           baseline_losses: np.ndarray, labels: list[str], epsilon: float) -> dict[str, Any]:
    losses = row_log_losses(probabilities, encoded, epsilon)
    prediction = probabilities.argmax(axis=1)
    weights = question_weights(questions)
    return {
        "question_mean_log_loss": question_mean(losses, questions),
        "question_mean_gain_over_training_prior": question_mean(baseline_losses - losses, questions),
        "macro_f1_question_weighted": float(f1_score(encoded, prediction, labels=np.arange(len(labels)),
                                                     average="macro", sample_weight=weights, zero_division=0)),
        "accuracy_question_weighted": question_mean((prediction == encoded).astype(float), questions),
        "per_class": {
            label: {"rows": int(np.sum(encoded == index)),
                    "questions": len({q for q, y in zip(questions, encoded) if y == index}),
                    "row_accuracy": float(np.mean(prediction[encoded == index] == index)),
                    "question_mean_log_loss": question_mean(losses[encoded == index],
                        [q for q, y in zip(questions, encoded) if y == index])}
            for index, label in enumerate(labels)
        },
    }


def analyze(rows: Sequence[Mapping[str, Any]], config: Optional[Mapping[str, Any]], out_dir: Any) -> dict[str, Any]:
    """Fit the entire frozen plan, then write predictions and paired effects.

    Required row fields: ``id``, ``label``, ``question_hash``, ``episode``, and
    production-only original ``split`` (train/val/test). The original split is
    saved only in descriptive overlap coverage and cannot enter a predictor.
    Optional ``failed`` is used solely for descriptive grouping; if absent,
    boolean admission flags ``error_present`` and ``result_present`` define it
    as error-present or result-absent. Error text is never inspected. Admission
    failures raise before fitting; estimator failures retain the fit ledger.
    Existing artifact files are never overwritten by a new invocation.
    """
    cfg = _configuration(config)
    admitted, labels, coverage = _admit_rows(rows, cfg)
    output = Path(out_dir)
    artifact_names = (
        "summary.json", "per_question_effects.json", "private_predictions.jsonl",
        "validation_selection.json", "class_question_coverage.json", "fit_ledger.json",
    )
    if any((output / name).exists() for name in artifact_names):
        raise AnalysisError("analysis artifacts already exist; use a new attempt directory")
    output.mkdir(parents=True, exist_ok=True)
    _json_write(output / "class_question_coverage.json", coverage)
    matrices, names, observed = _matrices(admitted, cfg)
    encoded = np.array([labels.index(row.label) for row in admitted], dtype=np.int64)
    indices = {partition: np.array([i for i, row in enumerate(admitted) if row.partition == partition], dtype=np.int64)
               for partition in _PARTITIONS}
    train, validation, test = (indices[partition] for partition in _PARTITIONS)
    train_questions = [admitted[i].question_hash for i in train]
    validation_questions = [admitted[i].question_hash for i in validation]
    test_questions = [admitted[i].question_hash for i in test]
    train_weights = question_weights(train_questions)
    planned = 12 + len(cfg["noise_realizations"]) + (4 if cfg["include_action_only"] else 0)
    if planned > cfg["max_fit_count"]:
        raise AnalysisError("frozen fit plan exceeds max_fit_count")
    ledger = _FitLedger(output / "fit_ledger.json", planned)
    selected, selection = {}, {}
    for representation, retained_key in (("single_coarse", None), ("single_combined", "single_coarse"),
                                         ("broad_combined", "single_combined")):
        selected[representation], selection[representation] = _select(
            representation, matrices, train, validation, encoded, train_weights, validation_questions,
            labels, cfg, ledger, selected.get(retained_key),
        )
    noise_matrices, adapted = {}, {}
    clean_adaptation_model = selected["single_combined"]
    for realization in cfg["noise_realizations"]:
        noisy, _, _ = _matrices(admitted, cfg, realization=realization)
        if not np.array_equal(matrices["single_action_only"], noisy["single_action_only"]):
            raise AnalysisError("action-only feature invariance failed before test prediction")
        noise_matrices[realization] = noisy
        adapted[realization] = _fit(
            f"adaptation/{realization}/{clean_adaptation_model.name}", clean_adaptation_model.representation,
            deepcopy(clean_adaptation_model.architecture), clone(clean_adaptation_model.estimator),
            noisy, train, encoded, train_weights, ledger,
        )
    if cfg["include_action_only"]:
        selected["single_action_only"], selection["single_action_only"] = _select(
            "single_action_only", matrices, train, validation, encoded, train_weights,
            validation_questions, labels, cfg, ledger,
        )
    ledger.require_complete()
    # This record is written before any test predictions; no subsequent selector runs.
    selection["adaptation"] = {"retuning": False, "frozen_clean_model": clean_adaptation_model.descriptor(),
                               "models": {str(draw): model.descriptor() for draw, model in adapted.items()}}
    _json_write(output / "validation_selection.json", selection)
    training_prior = np.bincount(encoded[train], weights=train_weights, minlength=len(labels))
    training_prior /= training_prior.sum()
    prior = smooth_probabilities(np.tile(training_prior, (len(test), 1)), cfg["epsilon"])
    baseline_losses = row_log_losses(prior, encoded[test], cfg["epsilon"])
    predictions = {"training_prior": prior}
    for representation, model in selected.items():
        predictions[representation] = _probabilities(model, matrices, test, len(labels), cfg["epsilon"])
    losses = {name: row_log_losses(probs, encoded[test], cfg["epsilon"])
              for name, probs in predictions.items()}
    noise_effects = []
    noise_scores = {}
    action_invariance = {}
    for realization in cfg["noise_realizations"]:
        noisy = noise_matrices[realization]
        clean_noisy = _probabilities(clean_adaptation_model, noisy, test, len(labels), cfg["epsilon"])
        adapted_noisy = _probabilities(adapted[realization], noisy, test, len(labels), cfg["epsilon"])
        clean_loss = row_log_losses(clean_noisy, encoded[test], cfg["epsilon"])
        adapted_loss = row_log_losses(adapted_noisy, encoded[test], cfg["epsilon"])
        noise_effects.append(clean_loss - adapted_loss)
        predictions[f"noise_{realization}/clean_single_combined"] = clean_noisy
        predictions[f"noise_{realization}/adapted_single_combined"] = adapted_noisy
        noise_scores[str(realization)] = {
            "clean": _score(clean_noisy, encoded[test], test_questions, baseline_losses, labels, cfg["epsilon"]),
            "adapted": _score(adapted_noisy, encoded[test], test_questions, baseline_losses, labels, cfg["epsilon"]),
        }
        if cfg["include_action_only"]:
            action_noisy = _probabilities(selected["single_action_only"], noisy, test, len(labels), cfg["epsilon"])
            if not np.array_equal(predictions["single_action_only"], action_noisy):
                raise AnalysisError("frozen action-only prediction invariance failed")
            predictions[f"noise_{realization}/single_action_only"] = action_noisy
            action_invariance[str(realization)] = {"features_exactly_equal": True, "predictions_exactly_equal": True}
    effect_rows = np.column_stack((
        losses["single_combined"] - losses["broad_combined"],
        losses["single_coarse"] - losses["single_combined"],
        np.mean(np.asarray(noise_effects), axis=0),
    ))
    effect_by_question = [question_values(effect_rows[:, i], test_questions) for i in range(3)]
    per_question = {
        question: [effect_by_question[i][question] for i in range(3)]
        for question in sorted(set(test_questions))
    }
    effects = bootstrap_question_effects(per_question, cfg["bootstrap_draws"], cfg["seed"], cfg["interval_percent"])
    question_records = {
        question: {"rows": test_questions.count(question),
                   "models": dict(Counter(admitted[i].label for i in test if admitted[i].question_hash == question)),
                   "effects": dict(zip(EFFECT_NAMES, per_question[question])),
                   "adaptation_by_realization": {
                       str(realization): question_values(noise_effects[draw], test_questions)[question]
                       for draw, realization in enumerate(cfg["noise_realizations"])
                   }}
        for question in per_question
    }
    supplementary = {"noise_scores": noise_scores, "action_only_invariance": action_invariance}
    if cfg["include_type_shuffle"]:
        shuffled, _, _ = _matrices(admitted, cfg, type_shuffle=True)
        if not np.array_equal(matrices["single_coarse"], shuffled["single_coarse"]):
            raise AnalysisError("type shuffle did not preserve coarse features")
        shuffle_probs = _probabilities(selected["single_combined"], shuffled, test, len(labels), cfg["epsilon"])
        predictions["type_shuffle/frozen_single_combined"] = shuffle_probs
        supplementary["type_shuffle"] = {
            "refit": False, "coarse_features_exactly_equal": True,
            "score": _score(shuffle_probs, encoded[test], test_questions, baseline_losses, labels, cfg["epsilon"]),
        }
    scores = {name: _score(probs, encoded[test], test_questions, baseline_losses, labels, cfg["epsilon"])
              for name, probs in predictions.items() if name in losses}
    descriptions = {}
    descriptor_masks = {
        "single_origin_empty": np.array([observed["empty_single"][i] for i in test], dtype=bool),
        "single_origin_nonempty": np.array([not observed["empty_single"][i] for i in test], dtype=bool),
        "failure": np.array([admitted[i].failed is True for i in test], dtype=bool),
        "nonfailure": np.array([admitted[i].failed is False for i in test], dtype=bool),
        "source_error_present": np.array([admitted[i].error_present is True for i in test], dtype=bool),
        "source_error_absent": np.array([admitted[i].error_present is False for i in test], dtype=bool),
        "source_result_absent": np.array([admitted[i].result_present is False for i in test], dtype=bool),
    }
    for descriptor, mask in descriptor_masks.items():
        descriptions[descriptor] = {"rows": int(mask.sum()), "questions": len({q for q, keep in zip(test_questions, mask) if keep})}
        if mask.any():
            descriptions[descriptor]["selected_single_combined_question_mean_loss"] = question_mean(
                losses["single_combined"][mask], [q for q, keep in zip(test_questions, mask) if keep])
    summary = {
        "status": "complete", "fixture_only": cfg["fixture_tag"] is not None,
        "config": cfg, "class_order": labels,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__},
        "fit_counter": {"planned": planned, "completed": len(ledger.entries), "maximum": cfg["max_fit_count"]},
        "training_prior": dict(zip(labels, training_prior.tolist())),
        "feature_names": names, "selected_models": {name: model.descriptor() for name, model in selected.items()},
        "test_scores": scores, "primary": effects, "supplementary": supplementary,
        "descriptive_subsets": descriptions,
        "failure_descriptor_missing_rows": sum(admitted[i].failed is None for i in test),
        "limitations": ["retrospective_public_archive_reanalysis", "exact_question_grouping_not_semantic_deduplication",
                        "recorded_callback_order_is_harness_proxy", "local_timestamp_age_not_duration",
                        "metadata_obfuscation_not_live_agent_delay", "predictive_pipeline_effect_not_mutual_information",
                        "fixed_training_selection_and_noise_conditional_resampling"],
        "artifacts": {name: str(output / name) for name in artifact_names},
    }
    _json_write(output / "per_question_effects.json", {"effect_order": list(EFFECT_NAMES), "questions": question_records})
    with (output / "private_predictions.jsonl").open("x", encoding="utf-8") as stream:
        for local_index, global_index in enumerate(test):
            row = admitted[global_index]
            record = {"id": row.identifier, "label": row.label, "question_hash": row.question_hash,
                      "partition": "test", "class_order": labels,
                      "probabilities": {name: probs[local_index].tolist() for name, probs in predictions.items()}}
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
    _json_write(output / "summary.json", summary)
    return summary
