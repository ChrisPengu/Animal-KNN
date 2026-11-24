"""Sửa activation và các lệnh .exe của môi trường đã chuyển sang thư mục mới.

Chạy bằng .venv\Scripts\python.exe; không thay phiên bản thư viện hay trọng số.
"""
from pathlib import Path
import importlib.metadata as metadata
import sys
import venv

from pip._vendor.distlib.scripts import ScriptMaker


def main():
    project = Path(__file__).resolve().parents[1]
    environment = project / ".venv"
    if Path(sys.prefix).resolve() != environment.resolve():
        raise SystemExit("Hãy chạy bằng .venv\\Scripts\\python.exe của dự án.")
    builder = venv.EnvBuilder(with_pip=False)
    builder.setup_scripts(builder.ensure_directories(str(environment)))
    maker = ScriptMaker(None, str(environment / "Scripts"))
    maker.executable = str(environment / "Scripts/python.exe")
    maker.variants = {""}
    maker.clobber = True
    count = 0
    for distribution in metadata.distributions():
        for entry in distribution.entry_points:
            if entry.group in {"console_scripts", "gui_scripts"}:
                maker.make(f"{entry.name} = {entry.value}", options={"gui": entry.group == "gui_scripts"})
                count += 1
    # pip còn có alias theo phiên bản Python, không luôn nằm trong entry_points.
    maker.make(f"pip{sys.version_info.major}.{sys.version_info.minor} = pip._internal.cli.main:main")
    print(f"Đã sửa activation, {count} lệnh và alias pip tại {environment}")


if __name__ == "__main__":
    main()
