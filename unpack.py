from json import load
from pathlib import Path

HOME = Path(__file__).parent / "Exports" / "Pal" / "Content"
P_DT_C = HOME / "Pal" / "DataTable" / "Character"
P_DT_W = HOME / "Pal" / "DataTable" / "Waza"
P_DT_E = HOME / "Pal" / "DataTable" / "Exp"
P_DT_P = HOME / "Pal" / "DataTable" / "PassiveSkill"


def load_rows(filepath: Path):
    return load(open(filepath, encoding="utf-8"))[0]["Rows"]


DT_PMP: dict = load_rows(P_DT_C / "DT_PalMonsterParameter.json")
DT_PET: dict = load_rows(P_DT_E / "DT_PalExpTable.json")
DT_WDT: dict = load_rows(P_DT_W / "DT_WazaDataTable.json")
DT_PSM: dict[str, dict[str, str]] = load_rows(P_DT_P / "DT_PassiveSkill_Main.json")


def rich_zukan_index(param: dict):
    return f"{param['ZukanIndex']}{param['ZukanIndexSuffix']}".zfill(
        4 if param["ZukanIndexSuffix"] else 3
    )


CHARACTER_IDS = [
    k
    for k, v in DT_PMP.items()
    if v["ZukanIndex"] > 0 and rich_zukan_index(v) != "013B"
]
CHARACTER_IDS += [f"BOSS_{i}" for i in CHARACTER_IDS]
ACTION_SKILLS = [v["WazaType"] for v in DT_WDT.values()]
PASSIVE_SKILLS = [
    k
    for k, v in DT_PSM.items()
    if v["OverrideDescMsgID"].startswith("PASSIVE_") or v["AddPal"] or v["AddRarePal"]
]
