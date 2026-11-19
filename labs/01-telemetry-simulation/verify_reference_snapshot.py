"""Verify frozen S01 reference ZIP, file manifest, and archived frame hashes.

Standard library only. A SHA-256 manifest is not a cryptographic signature.
"""
import argparse
import hashlib
import json
import pathlib
import re
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent / "evidence" / "reference-v1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX12 = re.compile(r"[0-9a-f]{24}\Z")
SCENARIOS = ("baseline", "corrupt", "drop", "duplicate", "reorder")


def verify_snapshot(folder: pathlib.Path) -> list[str]:
    problems = []
    try:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            return ["unsupported manifest"]
        filename = manifest.get("archive_file")
        if filename != "s01-reference-2026-11-19.zip":
            return ["unexpected archive name"]
        zip_path = folder / filename
        if zip_path.stat().st_size > 1_000_000:
            return ["archive exceeds size limit"]
        zipped = zip_path.read_bytes()
        if len(zipped) != manifest.get("archive_bytes"):
            problems.append("archive size mismatch")
        if hashlib.sha256(zipped).hexdigest() != manifest.get("archive_sha256"):
            problems.append("archive SHA-256 mismatch")
        files = manifest.get("files")
        if not isinstance(files, list) or len(files) != 19:
            return problems + ["manifest must list exactly 19 files"]
        by_path = {}
        for file in files:
            if not isinstance(file, dict):
                return problems + ["invalid manifest entry"]
            name, size, digest = file.get("path"), file.get("bytes"), file.get("sha256")
            if (not isinstance(name, str) or not name or "\\" in name or
                name.startswith("/") or ".." in pathlib.PurePosixPath(name).parts or
                name in by_path or type(size) is not int or not 0 <= size <= 100_000 or
                not isinstance(digest, str) or not HEX64.fullmatch(digest)):
                return problems + ["invalid or duplicate manifest file entry"]
            by_path[name] = file
        if len(by_path) != manifest.get("archive_contents_count"):
            problems.append("incorrect declared file count")
        with zipfile.ZipFile(zip_path) as archive:
            info = archive.infolist()
            names = [item.filename for item in info]
            if len(names) != len(set(names)) or set(names) != set(by_path):
                return problems + ["archive file list differs from manifest"]
            content = {}
            for item in info:
                if item.is_dir() or item.file_size > 100_000:
                    return problems + ["invalid archive member size/type"]
                raw = archive.read(item)
                content[item.filename] = raw
                entry = by_path[item.filename]
                if len(raw) != entry["bytes"]:
                    problems.append("file size mismatch: " + item.filename)
                if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                    problems.append("file SHA-256 mismatch: " + item.filename)
        for scenario in SCENARIOS:
            frame_data = json.loads(content[f"{scenario}/input_frames.json"])
            observation = json.loads(content[f"{scenario}/observations.json"])
            truth = json.loads(content[f"{scenario}/ground_truth.json"])
            frames = frame_data.get("frames")
            if (not isinstance(frames, list) or
                not 1 <= len(frames) <= 4096 or len(frames) != frame_data.get("frame_count")):
                problems.append("invalid frame count: " + scenario)
                continue
            hashed = hashlib.sha256()
            for index, item in enumerate(frames):
                code = item.get("bytes_hex") if isinstance(item, dict) else None
                if (not isinstance(item, dict) or type(item.get("frame_index")) is not int or
                    item["frame_index"] != index or not isinstance(code, str) or
                    not HEX12.fullmatch(code)):
                    problems.append("invalid frame at " + scenario + "/" + str(index))
                    break
                raw = bytes.fromhex(code)
                hashed.update(len(raw).to_bytes(4, "big"))
                hashed.update(raw)
            else:
                expected = hashed.hexdigest()
                for label, report in (("observations", observation), ("ground_truth", truth)):
                    if report.get("checksums", {}).get("input_frames_sha256") != expected:
                        problems.append("frame SHA-256 mismatch: " + scenario + "/" + label)
                if observation.get("measurements", {}).get("received_frames") != len(frames):
                    problems.append("receiver frame count mismatch: " + scenario)
                if truth.get("delivered_frame_count") != len(frames):
                    problems.append("generator frame count mismatch: " + scenario)
                for label, report in (("frames", frame_data), ("observations", observation),
                                      ("ground_truth", truth)):
                    if report.get("run_id") != manifest.get("source", {}).get("run_id") or report.get("scenario_id") != scenario:
                        problems.append("run metadata mismatch: " + scenario + "/" + label)
        for name, group in (("evaluation.json","evaluation"),
                            ("evidence_verification.json","integrity"),
                            ("replay_verification.json","replay")):
            actual = json.loads(content[name])
            if actual.get("counts") != manifest.get("observed_results", {}).get(group):
                problems.append("summary counters mismatch: " + name)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError,
            zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        problems.append("cannot verify reference: " + str(exc))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    errors = verify_snapshot(args.folder)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("S01 reference verified: original ZIP, 19 files, 5 frame sets and 3 summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
