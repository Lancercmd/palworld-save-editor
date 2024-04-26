from json import load
from pathlib import Path

HOME = Path(__file__).parent / "Exports" / "Pal" / "Content"
P_DT_E = HOME / "Pal" / "DataTable" / "Exp"


def load_rows(filepath: Path):
    return load(open(filepath, encoding="utf-8"))[0]["Rows"]


DT_PET: dict = load_rows(P_DT_E / "DT_PalExpTable.json")
