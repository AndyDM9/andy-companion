import shutil
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from andy_companion import reading  # noqa: E402


def page(lines, size=(900, 1200)):
    img = np.full((size[0], size[1], 3), 255, np.uint8)
    for i, line in enumerate(lines):
        cv2.putText(img, line, (40, 90 + i * 70), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 3, cv2.LINE_AA)
    return img


TSV = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
       "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t96\tYour\n"
       "5\t1\t1\t1\t1\t2\t0\t0\t10\t10\t95\tbill\n"
       "5\t1\t1\t1\t2\t1\t0\t0\t10\t10\t91\tDue\n")


def test_parse_tsv_keeps_lines_in_order():
    out = reading.parse_tsv(TSV)
    assert out["text"] == "Your bill\nDue" and out["words"] == 3 and not out["uncertain"]


def test_low_confidence_marks_the_reading_uncertain():
    low = TSV.replace("\t96\t", "\t20\t").replace("\t95\t", "\t30\t")
    assert reading.parse_tsv(low)["uncertain"]


def test_malformed_output_is_refused():
    assert "error" in reading.parse_tsv("garbage")


def test_the_sharpest_of_three_frames_is_used():
    sharp = page(["Hello there"])
    blurry = cv2.GaussianBlur(sharp, (31, 31), 0)
    frames = iter([blurry, sharp, blurry])
    chosen = reading.best_frame(lambda: next(frames), sleep=lambda s: None)
    assert np.array_equal(chosen, sharp)


def test_no_camera_picture_is_a_kind_error():
    assert "error" in reading.read(lambda: None, sleep=lambda s: None)


def test_dark_blank_view_asks_for_light():
    dark = np.full((480, 640, 3), 10, np.uint8)
    empty = SimpleNamespace(returncode=0, stdout=TSV.split("\n")[0].encode() + b"\n")
    out = reading.read(lambda: dark, runner=lambda *a, **k: empty, sleep=lambda s: None)
    if "error" not in out:
        assert out["text"] == "" and "light" in out["ask"]


def test_the_picture_goes_to_tesseract_on_stdin_and_never_to_a_file(monkeypatch):
    calls = []

    def runner(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0, stdout=TSV.encode())

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/tesseract")
    out = reading.ocr(page(["Your bill"]), runner=runner)
    (cmd, kwargs), = calls
    assert cmd[1:3] == ["stdin", "stdout"] and isinstance(kwargs["input"], bytes) and kwargs["timeout"]
    assert out["text"].startswith("Your bill")


@pytest.mark.skipif(not shutil.which("tesseract"), reason="Tesseract not installed")
def test_reads_a_real_letter_with_tesseract():
    letter = page(["CITY WATER DEPARTMENT", "Amount due 42.10", "Pay by October 30"])
    out = reading.read(lambda: letter, runner=subprocess.run, sleep=lambda s: None)
    text = out["text"].upper()
    assert "WATER" in text and "OCTOBER" in text
