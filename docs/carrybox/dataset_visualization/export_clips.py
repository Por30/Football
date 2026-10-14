"""Export frame-exact per-motion MP4s from the verified FindBox recording."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "outputs/carrybox/findbox_dataset"
CLIPS = OUTPUT / "clips"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_recording():
    record = json.loads((OUTPUT / "recording.json").read_text())
    manifest = ROOT / "findbox/amp_manifest.json"
    assert sha256(manifest) == record["dataset"]["manifest_sha256"]
    expected = {c["file"] for c in record["clips"]}
    actual = {p.relative_to(ROOT / "findbox").as_posix()
              for p in (ROOT / "findbox").rglob("*.pt")}
    assert expected == actual and len(expected) == 17
    for clip in record["clips"]:
        assert sha256(ROOT / "findbox" / clip["file"]) == clip["source_sha256"]
        assert clip["video_frames"] == (clip["source_frames"] + 1) // 2
    assert record["video_frames"] == sum(c["video_frames"] for c in record["clips"])
    return record


def open_video(path):
    return imageio.get_reader(path, input_params=["-threads", "2"])


def export(record):
    paths = [CLIPS / Path(c["file"]).with_suffix(".mp4") for c in record["clips"]]
    assert not any(p.exists() for p in paths), "Refusing to overwrite existing clips"
    entries = []
    offset = 0
    with open_video(OUTPUT / record["video"]) as source:
        frames = iter(source)
        for clip, path in zip(record["clips"], paths):
            path.parent.mkdir(parents=True, exist_ok=True)
            with imageio.get_writer(
                path, fps=record["fps"], codec="libx264", pixelformat="yuv420p",
                macro_block_size=1, quality=None,
                ffmpeg_params=["-crf", "18", "-preset", "fast", "-threads", "2",
                               "-movflags", "+faststart"],
            ) as writer:
                for _ in range(clip["video_frames"]):
                    writer.append_data(next(frames))
            entries.append({**clip, "video": path.relative_to(CLIPS).as_posix(),
                            "start_frame": offset, "sha256": sha256(path)})
            offset += clip["video_frames"]
            print(f"Exported {path.relative_to(ROOT)} ({clip['video_frames']} frames)", flush=True)
        assert next(frames, None) is None
    index = {"combined_video_sha256": sha256(OUTPUT / record["video"]),
             "fps": record["fps"], "resolution": record["resolution"], "clips": entries}
    (CLIPS / "index.json").write_text(json.dumps(index, indent=2) + "\n")


def verify(record):
    index = json.loads((CLIPS / "index.json").read_text())
    assert index["combined_video_sha256"] == sha256(OUTPUT / record["video"])
    assert index["fps"] == record["fps"] == 30
    assert index["resolution"] == record["resolution"] == [960, 720]
    assert len(index["clips"]) == len(record["clips"])
    assert {p.relative_to(CLIPS).as_posix() for p in CLIPS.rglob("*.mp4")} == {
        c["video"] for c in index["clips"]}
    total, max_error = 0, 0.0
    with open_video(OUTPUT / record["video"]) as original:
        source = iter(original)
        for clip, recorded in zip(index["clips"], record["clips"]):
            assert all(clip[key] == value for key, value in recorded.items())
            assert clip["start_frame"] == total
            path = CLIPS / clip["video"]
            assert sha256(path) == clip["sha256"]
            count = 0
            with open_video(path) as video:
                meta = video.get_meta_data()
                assert meta["size"] == (960, 720) and meta["fps"] == 30
                assert meta["codec"] == "h264" and meta["pix_fmt"].startswith("yuv420p")
                for frame in video:
                    assert frame.shape == (720, 960, 3)
                    reference = next(source)
                    # Lossy encoding changes pixels; compare every frame to its exact source index.
                    error = float(np.abs(frame.astype(np.int16) - reference).mean())
                    assert error < 8.0, (clip["file"], count, error)
                    max_error = max(max_error, error)
                    count += 1
            assert count == clip["video_frames"]
            total += count
        assert next(source, None) is None
    assert total == record["video_frames"] == 2318
    result = {"status": "PASS", "clips": len(index["clips"]), "decoded_frames": total,
              "fps": 30, "resolution": [960, 720], "duration_seconds": total / 30,
              "all_source_hashes_match_recording": True, "all_frame_positions_compared": True,
              "maximum_frame_mean_absolute_error_8bit": max_error}
    (CLIPS / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    record = checked_recording()
    if args.verify_only:
        verify(record)
    else:
        export(record)
