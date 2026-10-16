import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from layout import ROOT, TARGET

PROFILE = ROOT / ".soffice-profile"


def recalc(path):
    path = Path(path)
    with tempfile.TemporaryDirectory() as workdir:
        command = [
            "soffice",
            "--headless",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation=file://{PROFILE}",
            "--convert-to",
            "xlsx:Calc MS Excel 2007 XML",
            "--outdir",
            workdir,
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        produced = Path(workdir) / path.name
        if not produced.exists():
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            raise SystemExit(f"LibreOffice did not produce {produced}")
        shutil.move(str(produced), str(path))
    print(f"recalculated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    recalc(TARGET)
