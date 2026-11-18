"""Assess deterministic S01 fixture conformance, not fault-classifier accuracy.

Input: reports created by run_scenarios.py; no raw frames or fault labels are
provided to the receiver by this evaluation tool.
"""

import argparse
import json
from pathlib import Path
import re

STATUS_METRICS = {
    "first": "first_frames",
    "in_order": "in_order_frames",
    "gap": "gap_events",
    "duplicate": "duplicate_frames",
    "out_of_order": "out_of_order_frames",
}
ALL_STATUSES = set(STATUS_METRICS) | {"invalid"}
METRIC_KEYS = (
    "received_frames", "valid_frames", "invalid_frames",
    "estimated_missing_on_gaps", *STATUS_METRICS.values(),
)


class InvalidRun(ValueError):
    """The run cannot be audited because inputs are malformed or missing."""


def read_json(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidRun(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise InvalidRun(f"JSON root must be an object: {path}")
    return obj


def accounting_issues(observation: dict) -> list[str]:
    """Validate receiver records without consulting the known intervention."""
    m = observation.get("measurements")
    events = observation.get("events")
    if not isinstance(m, dict) or not isinstance(events, list):
        raise InvalidRun("observations must contain measurements object and events list")
    for key in METRIC_KEYS:
        if type(m.get(key)) is not int or m[key] < 0:
            raise InvalidRun(f"missing or invalid nonnegative integer: {key}")
    issues = []
    if len(events) != m["received_frames"]:
        issues.append("event count differs from received_frames")
    if m["valid_frames"] + m["invalid_frames"] != m["received_frames"]:
        issues.append("valid + invalid != received")
    if sum(m[key] for key in STATUS_METRICS.values()) != m["valid_frames"]:
        issues.append("sum of valid statuses differs from valid_frames")
    status_counts = {s: 0 for s in ALL_STATUSES}
    missing_total = 0
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            issues.append(f"event {index} must be an object")
            continue
        if type(event.get("frame_index")) is not int or event["frame_index"] != index:
            issues.append(f"event {index} has incorrect frame_index")
        status = event.get("status")
        if not isinstance(status, str) or status not in ALL_STATUSES:
            issues.append(f"event {index} has unrecognized status")
            continue
        status_counts[status] += 1
        if status == "invalid":
            if not isinstance(event.get("reason"), str) or not event["reason"]:
                issues.append(f"invalid event {index} lacks reason")
        else:
            sequence = event.get("sequence")
            source = event.get("source_id")
            missing = event.get("estimated_missing")
            if type(sequence) is not int or not 0 <= sequence <= 65535:
                issues.append(f"event {index} has invalid sequence")
            if type(source) is not int or not 0 <= source <= 255:
                issues.append(f"event {index} has invalid source")
            if type(missing) is not int or missing < 0:
                issues.append(f"event {index} has invalid missing estimate")
            elif status != "gap" and missing:
                issues.append(f"event {index} claims missing packets without a gap")
            else:
                missing_total += missing
    if status_counts["invalid"] != m["invalid_frames"]:
        issues.append("invalid event count does not match counter")
    for status, key in STATUS_METRICS.items():
        if status_counts[status] != m[key]:
            issues.append(f"{status} event count does not match {key}")
    if missing_total != m["estimated_missing_on_gaps"]:
        issues.append("per-event missing estimates do not match counter")
    return issues


def evaluate_pair(obs: dict, truth: dict, policy: dict, run_id: str, scenario: str) -> dict:
    issues = accounting_issues(obs)
    for field, expected in (("run_id", run_id), ("scenario_id", scenario),
                            ("lab_id", "S01"), ("data_origin", "synthetic")):
        if obs.get(field) != expected or truth.get(field) != expected:
            issues.append(f"mismatched {field}")
    ob_hash = obs.get("checksums")
    tr_hash = truth.get("checksums")
    ob_hash = ob_hash.get("input_frames_sha256") if isinstance(ob_hash, dict) else None
    tr_hash = tr_hash.get("input_frames_sha256") if isinstance(tr_hash, dict) else None
    if not isinstance(ob_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", ob_hash):
        issues.append("malformed observation SHA-256")
    if not isinstance(tr_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", tr_hash):
        issues.append("malformed ground-truth SHA-256")
    if ob_hash != tr_hash:
        issues.append("input SHA-256 differs between the two reports")
    if truth.get("generated_frame_count") != policy["generated_frames"]:
        issues.append("unexpected generated frame count in ground truth")
    if truth.get("delivered_frame_count") != policy["delivered_frames"]:
        issues.append("unexpected delivered frame count in ground truth")
    if truth.get("delivered_frame_count") != obs["measurements"]["received_frames"]:
        issues.append("ground truth delivered count differs from received count")
    intervention = truth.get("intervention")
    kind = intervention.get("type") if isinstance(intervention, dict) else None
    if kind != policy["intervention_type"] or (intervention is not None and not isinstance(intervention, dict)):
        issues.append("unexpected intervention type in ground truth")
    if intervention != policy["expected_intervention"]:
        issues.append("generator intervention details differ from predefined policy")
    differences = {
        key: {"expected": wanted, "observed": obs["measurements"].get(key)}
        for key, wanted in policy["measurements"].items()
        if obs["measurements"].get(key) != wanted
    }
    statuses = [item.get("status") if isinstance(item, dict) else None for item in obs["events"]]
    if statuses != policy["event_statuses"]:
        differences["event_statuses"] = {"expected": policy["event_statuses"], "observed": statuses}
    actual_invalid_reasons = {
        str(event["frame_index"]): event.get("reason")
        for event in obs["events"]
        if isinstance(event, dict) and event.get("status") == "invalid"
        and type(event.get("frame_index")) is int
    }
    if actual_invalid_reasons != policy["invalid_reasons"]:
        differences["invalid_reasons"] = {
            "expected": policy["invalid_reasons"], "observed": actual_invalid_reasons,
        }
    return {
        "scenario_id": scenario,
        "verdict": "inconsistent" if issues else ("deviation" if differences else "conformant"),
        "record_issues": issues,
        "expectation_differences": differences,
        "known_generator_intervention": kind,
        "measurements": obs["measurements"],
        "recorded_input_sha256": ob_hash,
    }


def evaluate_run(run_dir: Path, policy: dict) -> dict:
    if policy.get("policy_version") != 1 or not isinstance(policy.get("scenarios"), dict):
        raise InvalidRun("unrecognized or malformed evaluation policy")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_dir.name):
        raise InvalidRun("invalid run directory name")
    results = []
    for scenario, expected in policy["scenarios"].items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", scenario):
            raise InvalidRun("unsafe scenario directory name in evaluation policy")
        obs = read_json(run_dir / scenario / "observations.json")
        truth = read_json(run_dir / scenario / "ground_truth.json")
        entry = evaluate_pair(obs, truth, expected, run_dir.name, scenario)
        if truth.get("base_sequences") != policy.get("expected_base_sequences"):
            entry["record_issues"].append("unexpected generator base_sequences")
        if truth.get("source_id") != policy.get("expected_source_id"):
            entry["record_issues"].append("unexpected generator source_id")
        if entry["record_issues"]:
            entry["verdict"] = "inconsistent"
        results.append(entry)
    return {
        "evaluation_schema_version": 1,
        "policy_version": policy["policy_version"],
        "run_id": run_dir.name,
        "purpose": "Deterministic software conformance; NOT fault-cause classification accuracy",
        "counts": {
            "scenarios": len(results),
            "conformant": sum(x["verdict"] == "conformant" for x in results),
            "deviation": sum(x["verdict"] == "deviation" for x in results),
            "inconsistent": sum(x["verdict"] == "inconsistent" for x in results),
        },
        "results": results,
        "limitations": [
            "Both files originate in one software simulator, not independent physical observations.",
            "Stored hashes cross-reference the reports; original frame bytes are not archived for re-hashing.",
            "A receiver sequence gap is not proof of a lost physical transmission.",
            "These five deterministic cases cannot estimate precision, recall, sensitivity or accuracy.",
        ],
    }


def markdown_summary(report: dict) -> str:
    lines = [
        "# S01 — avaliação de cenários sintéticos", "",
        f"- Identificador da execução: `{report['run_id']}`",
        f"- Política de avaliação: versão {report['policy_version']}",
        "- Escopo: conformidade de software, não acurácia de um classificador de causas.", "",
        "| Cenário | Intervenção conhecida | Recebidos | Inválidos | Lacunas | Duplicados | Fora de ordem | Veredito |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for result in report["results"]:
        metrics = result["measurements"]
        lines.append(
            f"| {result['scenario_id']} | {result['known_generator_intervention'] or 'nenhuma'} | "
            f"{metrics['received_frames']} | {metrics['invalid_frames']} | "
            f"{metrics['gap_events']} | {metrics['duplicate_frames']} | "
            f"{metrics['out_of_order_frames']} | {result['verdict']} |"
        )
    lines.extend([
        "", "## Interpretação", "",
        "- **conformant:** relatório consistente e resultados previstos observados; não prova reconhecimento da causa.",
        "- **deviation:** contagens ou eventos divergentes da política predefinida.",
        "- **inconsistent:** metadados, contagens internas, ou hashes declarados não conferem.",
        "- No cenário `reorder`, há lacuna observada mas nenhum quadro foi omitido no gerador.",
        "- No cenário `drop`, a omissão é conhecida somente pelo gerador; o receptor registra uma lacuna.",
        "- Os hashes informados são comparados entre relatórios, mas os bytes originais não são revalidados.",
        "- Não estimar sensibilidade, precisão, recall ou taxa de acerto com estes casos didáticos.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Existing run-artifacts/<run_id> directory")
    parser.add_argument(
        "--policy", type=Path, default=Path(__file__).resolve().with_name("evaluation_policy.json"),
        help="Evaluation policy containing fixed expected results",
    )
    args = parser.parse_args()
    try:
        report = evaluate_run(args.run_dir, read_json(args.policy))
        json_out = args.run_dir / "evaluation.json"
        markdown_out = args.run_dir / "evaluation_summary.md"
        if json_out.exists() or markdown_out.exists():
            raise InvalidRun("evaluation already exists; prior output preserved")
        with json_out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        with markdown_out.open("x", encoding="utf-8") as stream:
            stream.write(markdown_summary(report))
    except (InvalidRun, OSError) as error:
        parser.exit(2, f"evaluation error: {error}\n")
    print(markdown_summary(report))
    return 0 if report["counts"]["conformant"] == report["counts"]["scenarios"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
