from json import load
from pathlib import Path

HOME = Path(__file__).parent / "Exports" / "Pal" / "Content"
P_DT_C = HOME / "Pal" / "DataTable" / "Character"
P_DT_W = HOME / "Pal" / "DataTable" / "Waza"
P_DT_E = HOME / "Pal" / "DataTable" / "Exp"
P_DT_P = HOME / "Pal" / "DataTable" / "PassiveSkill"
P_L10N_ZH = HOME / "L10N" / "zh-Hans" / "Pal" / "DataTable" / "Text"
P_L10N_EN = HOME / "L10N" / "en" / "Pal" / "DataTable" / "Text"


def load_rows(filepath: Path):
    return load(open(filepath, encoding="utf-8"))[0]["Rows"]


DT_PMP: dict = load_rows(P_DT_C / "DT_PalMonsterParameter.json")
DT_SNT_ZH: dict[str] = load_rows(P_L10N_ZH / "DT_SkillNameText.json")
DT_SNT_EN: dict[str] = load_rows(P_L10N_EN / "DT_SkillNameText.json")
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
PREFIX_ACTION_SKILL = "ACTION_SKILL_"
PREFIX_E_PAL_WAZA_ID = "EPalWazaID::"
ACTION_SKILLS_NAME_TEXT_ZH = {
    k: v["TextData"]["LocalizedString"]
    for k, v in DT_SNT_ZH.items()
    if k.startswith(PREFIX_ACTION_SKILL)
}
ACTION_SKILLS_NAME_TEXT_EN = {
    k: v["TextData"]["LocalizedString"]
    for k, v in DT_SNT_EN.items()
    if k.startswith(PREFIX_ACTION_SKILL)
}
ACTION_SKILLS = [v["WazaType"] for v in DT_WDT.values()]
PREFIX_PASSIVE_SKILL = "PASSIVE_"
PASSIVE_SKILLS = [
    k
    for k, v in DT_PSM.items()
    if v["OverrideDescMsgID"].startswith(PREFIX_PASSIVE_SKILL)
    or v["AddPal"]
    or v["AddRarePal"]
]
PASSIVE_SKILLS_NAME_TEXT_ZH = {
    k.replace(PREFIX_PASSIVE_SKILL, ""): v["TextData"]["LocalizedString"]
    for k, v in DT_SNT_ZH.items()
    if k.replace(PREFIX_PASSIVE_SKILL, "") in PASSIVE_SKILLS
}
PASSIVE_SKILLS_NAME_TEXT_EN = {
    k.replace(PREFIX_PASSIVE_SKILL, ""): v["TextData"]["LocalizedString"]
    for k, v in DT_SNT_EN.items()
    if k.replace(PREFIX_PASSIVE_SKILL, "") in PASSIVE_SKILLS
}
KV_WAZA_ZH = {
    v: k.replace(PREFIX_ACTION_SKILL, PREFIX_E_PAL_WAZA_ID)
    for k, v in ACTION_SKILLS_NAME_TEXT_ZH.items()
    if k.replace(PREFIX_ACTION_SKILL, PREFIX_E_PAL_WAZA_ID) in ACTION_SKILLS
}
KV_WAZA_EN = {
    v: k.replace(PREFIX_ACTION_SKILL, PREFIX_E_PAL_WAZA_ID)
    for k, v in ACTION_SKILLS_NAME_TEXT_EN.items()
    if k.replace(PREFIX_ACTION_SKILL, PREFIX_E_PAL_WAZA_ID) in ACTION_SKILLS
}
KV_WAZA = {"en": KV_WAZA_EN, "zh_Hans": KV_WAZA_ZH}
KV_PASSIVE_SKILL_ZH = {
    v: k.replace(PREFIX_PASSIVE_SKILL, "")
    for k, v in PASSIVE_SKILLS_NAME_TEXT_ZH.items()
}
KV_PASSIVE_SKILL_EN = {
    v: k.replace(PREFIX_PASSIVE_SKILL, "")
    for k, v in PASSIVE_SKILLS_NAME_TEXT_EN.items()
}
KV_PASSIVE_SKILL = {"en": KV_PASSIVE_SKILL_EN, "zh_Hans": KV_PASSIVE_SKILL_ZH}
