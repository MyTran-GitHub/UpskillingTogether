"""Create the required submission.zip layout from the project files."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = [
    "dbt_project.yml",
    "profiles.yml",
    "Dockerfile",
    "compose.yml",
    "requirements-orchestrator.txt",
    "README.md",
    ".dockerignore",
    ".gitignore",
    "raw_customers.csv",
    "raw_orders.csv",
    "raw_payments.csv",
    "data/.gitkeep",
    "submission/customer_orders.csv",
    "submission/orchestrator_log.txt",
    "submission/NOTES.md",
]
files = [ROOT / name for name in TOP_LEVEL]
for directory in ("models", "seeds", "scripts", "orchestration"):
    files.extend(
        path for path in (ROOT / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )

destination = ROOT / "submission.zip"
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        if relative.parts[0] == "submission":
            relative = Path(*relative.parts[1:])
        archive.write(path, Path("submission") / relative)

print(f"Created {destination} with {len(files)} files")
