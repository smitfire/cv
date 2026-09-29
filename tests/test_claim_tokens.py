import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from review import _claim_tokens  # noqa: E402

CASES = {
    "raised €9.9M seed": {"9.9m"},
    "10x faster": {"10x"},
    "50k users": {"50k"},
    "3,370× faster": {"3,370×"},
    "5% to 85%": {"5%", "85%"},
    "on 162,000, rows": {"162,000"},
    "320+ merged PRs": {"320+"},
    "in 2019 and 12 months": set(),
}

for text, want in CASES.items():
    got = _claim_tokens(text)
    assert got == want, f"{text!r}: got {got}, want {want}"
print(f"ok: {len(CASES)} cases")
