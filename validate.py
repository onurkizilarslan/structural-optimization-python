"""Run each lesson's checks in isolation; GA outputs stay in a temporary folder."""
from pathlib import Path
import csv
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def main():
    for folder in sorted(ROOT.glob("0[2-6]-*")):
        print(f"Checking {folder.name}", flush=True)
        subprocess.run([sys.executable, "-m", "unittest", "test_hesap.py", "-v"], cwd=folder, check=True)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        shutil.copy2(ROOT / "01-genetic-algorithm-column" / "kolon_optimizasyonu.py", path)
        subprocess.run([sys.executable, "kolon_optimizasyonu.py"], cwd=path, check=True)
        for filename, expected in [("tum_adaylar.csv", 588), ("ga_sonuclari.csv", 10)]:
            with (path / filename).open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            if len(rows) != expected:
                raise AssertionError(f"{filename}: expected {expected} rows, got {len(rows)}")
    print("All lesson checks passed; GA smoke run produced expected row counts.")

if __name__ == "__main__":
    main()
