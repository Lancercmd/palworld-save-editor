class L10N:
    def __init__(self, locale: str = "zh_Hans"):
        self.locale = locale

    def get(self, key):
        if key in LOCALE and self.locale in LOCALE[key]:
            return LOCALE[key][self.locale]
        return key

    def get_locale(self):
        return self.locale

    def set_locale(self, locale):
        self.locale = locale or self.locale

    def get_locales(self):
        locales = set()
        for k in LOCALE:
            for k2 in LOCALE[k]:
                locales.add(k2)
        return sorted(locales)


LOCALE = {
    "Palworld main save": {
        "en": "Palworld main save",
        "zh_Hans": "Palworld 主存档",
    },
    "Palworld main save JSON": {
        "en": "Palworld main save JSON",
        "zh_Hans": "Palworld 主存档 JSON",
    },
    "All supported file types": {
        "en": "All supported file types",
        "zh_Hans": "所有支持的文件类型",
    },
    "Palworld Save Editor": {
        "en": "Palworld Save Editor",
        "zh_Hans": "Palworld 存档编辑器",
    },
    "Choose File": {
        "en": "Choose File",
        "zh_Hans": "选择文件",
    },
    "Save and Convert to SAV": {
        "en": "Save and Convert to SAV",
        "zh_Hans": "保存并转换为 SAV 文件",
    },
    "Save": {
        "en": "Save",
        "zh_Hans": "保存",
    },
    "Guild List": {
        "en": "Guild List",
        "zh_Hans": "公会列表",
    },
    "Guild ID": {
        "en": "Guild ID",
        "zh_Hans": "公会 ID",
    },
    "Guild Name": {
        "en": "Guild Name",
        "zh_Hans": "公会名称",
    },
    "Base Camp Level": {
        "en": "Base Camp Level",
        "zh_Hans": "据点等级",
    },
    "Base Camp Count": {
        "en": "Base Camp Count",
        "zh_Hans": "据点数量",
    },
    "Member Count": {
        "en": "Member Count",
        "zh_Hans": "成员数量",
    },
    "Ready": {
        "en": "Ready",
        "zh_Hans": "准备就绪",
    },
    "Processing": {
        "en": "Processing",
        "zh_Hans": "正在处理",
    },
    "Choose Palworld main save": {
        "en": "Choose Palworld main save",
        "zh_Hans": "选择 Palworld 主存档",
    },
    "Error": {
        "en": "Error",
        "zh_Hans": "错误",
    },
    "File not exists.": {
        "en": "File not exists.",
        "zh_Hans": "文件不存在。",
    },
    "Guild Admin ID": {
        "en": "Guild Admin ID",
        "zh_Hans": "公会会长 ID",
    },
    "Player List": {
        "en": "Player List",
        "zh_Hans": "玩家列表",
    },
    "Player UID": {
        "en": "Player UID",
        "zh_Hans": "玩家 UID",
    },
    "Nickname": {
        "en": "Nickname",
        "zh_Hans": "昵称",
    },
    "Level": {
        "en": "Level",
        "zh_Hans": "等级",
    },
    "Exp": {
        "en": "Exp",
        "zh_Hans": "经验值",
    },
    "Last Online": {
        "en": "Last Online",
        "zh_Hans": "最后在线",
    },
    "Pal List": {
        "en": "Pal List",
        "zh_Hans": "帕鲁列表",
    },
    "Filter by Container ID": {
        "en": "Filter by Container ID",
        "zh_Hans": "按容器 ID 筛选",
    },
    "Filter by Character ID": {
        "en": "Filter by Character ID",
        "zh_Hans": "按帕鲁 ID 筛选",
    },
    "Instance ID": {
        "en": "Instance ID",
        "zh_Hans": "实例 ID",
    },
    "Character ID": {
        "en": "Character ID",
        "zh_Hans": "帕鲁 ID",
    },
    "Gender": {
        "en": "Gender",
        "zh_Hans": "性别",
    },
    "Exp": {
        "en": "Exp",
        "zh_Hans": "经验值",
    },
    "Talent: HP": {
        "en": "Talent: HP",
        "zh_Hans": "个体：HP",
    },
    "Talent: Melee": {
        "en": "Talent: Melee",
        "zh_Hans": "个体：近战",
    },
    "Talent: Shot": {
        "en": "Talent: Shot",
        "zh_Hans": "个体：远程",
    },
    "Talent: Defense": {
        "en": "Talent: Defense",
        "zh_Hans": "个体：防御",
    },
    "Passive Skills": {
        "en": "Passive Skills",
        "zh_Hans": "被动技能",
    },
    "All": {
        "en": "All",
        "zh_Hans": "全部",
    },
    "Edit Guild": {
        "en": "Edit Guild",
        "zh_Hans": "编辑公会",
    },
    "Guild Name cannot be empty.": {
        "en": "Guild Name cannot be empty.",
        "zh_Hans": "公会名称不能为空。",
    },
    "Base Camp Level cannot be empty.": {
        "en": "Base Camp Level cannot be empty.",
        "zh_Hans": "据点等级不能为空。",
    },
    "Edit Player": {
        "en": "Edit Player",
        "zh_Hans": "编辑玩家",
    },
    "Align": {
        "en": "Align",
        "zh_Hans": "对齐",
    },
    "Nickname cannot be empty.": {
        "en": "Nickname cannot be empty.",
        "zh_Hans": "昵称不能为空。",
    },
    "Level cannot be empty.": {
        "en": "Level cannot be empty.",
        "zh_Hans": "等级不能为空。",
    },
    "Level must be a number.": {
        "en": "Level must be a number.",
        "zh_Hans": "等级必须是数字。",
    },
    "Level cannot be lower than the current.": {
        "en": "Level cannot be lower than the current.",
        "zh_Hans": "等级不能低于当前等级。",
    },
    "Save as JSON": {
        "en": "Save as JSON",
        "zh_Hans": "保存为 JSON 文件",
    },
    "Info": {
        "en": "Info",
        "zh_Hans": "信息",
    },
    "Save successfully.": {
        "en": "Save successfully.",
        "zh_Hans": "保存成功。",
    },
    "MB1 to select items, MB3 to edit.": {
        "en": "MB1 to select items, MB3 to edit.",
        "zh_Hans": "左键选取列表项，右键编辑。",
    },
    "Please keep a backup in case of data loss.": {
        "en": "Please keep a backup in case of data loss.",
        "zh_Hans": "请注意保留备份，以防数据丢失。",
    },
    " Please keep a backup in case of data loss.": {
        "en": " Please keep a backup in case of data loss.",
        "zh_Hans": "请注意保留备份，以防数据丢失。",
    },
    "Edit Pal": {
        "en": "Edit Pal",
        "zh_Hans": "编辑帕鲁",
    },
    "Click to switch": {
        "en": "Click to switch",
        "zh_Hans": "点击切换",
    },
    "Rank": {
        "en": "Rank",
        "zh_Hans": "浓缩等级",
    },
    "Rank HP": {
        "en": "Rank HP",
        "zh_Hans": "最大 HP 强化等级",
    },
    "Rank Attack": {
        "en": "Rank Attack",
        "zh_Hans": "攻击 强化等级",
    },
    "Rank Defense": {
        "en": "Rank Defense",
        "zh_Hans": "防御 强化等级",
    },
    "Rank CraftSpeed": {
        "en": "Rank CraftSpeed",
        "zh_Hans": "工作速度 强化等级",
    },
    "Rare / Shining": {
        "en": "Rare / Shining",
        "zh_Hans": "稀有 / 闪光",
    },
    "Equip Waza": {
        "en": "Equip Waza",
        "zh_Hans": "装备技能",
    },
    "Mastered Waza": {
        "en": "Mastered Waza",
        "zh_Hans": "已掌握技能",
    },
    "Edit": {
        "en": "Edit",
        "zh_Hans": "编辑",
    },
    "Editor": {
        "en": "Editor",
        "zh_Hans": "编辑器",
    },
    "Ranks MAX": {
        "en": "Ranks MAX",
        "zh_Hans": "浓缩等级和强化等级 MAX",
    },
    "Talents MAX": {
        "en": "Talents MAX",
        "zh_Hans": "个体值 MAX",
    },
    "Edit Equip Waza": {
        "en": "Edit Equip Waza",
        "zh_Hans": "编辑装备技能",
    },
    "Edit Mastered Waza": {
        "en": "Edit Mastered Waza",
        "zh_Hans": "编辑已掌握技能",
    },
    "Equip Waza cannot have more than 3.": {
        "en": "Equip Waza cannot have more than 3.",
        "zh_Hans": "装备技能不能超过 3 个。",
    },
    "Waza ID": {
        "en": "Waza ID",
        "zh_Hans": "技能 ID",
    },
    "Enter Waza ID": {
        "en": "Enter Waza ID",
        "zh_Hans": "输入技能 ID",
    },
    "Duplicate Waza ID is not allowed.": {
        "en": "Duplicate Waza ID is not allowed.",
        "zh_Hans": "不允许重复的技能 ID。",
    },
    "Waza ID is invalid.": {
        "en": "Waza ID is invalid.",
        "zh_Hans": "技能 ID 无效。",
    },
    "Remove Selected": {
        "en": "Remove Selected",
        "zh_Hans": "删除选中",
    },
    "Remove All": {
        "en": "Remove All",
        "zh_Hans": "删除所有",
    },
    "Modified": {
        "en": "Modified",
        "zh_Hans": "已修改",
    },
    "Character ID cannot be empty.": {
        "en": "Character ID cannot be empty.",
        "zh_Hans": "帕鲁 ID 不能为空。",
    },
    "Character ID is invalid.": {
        "en": "Character ID is invalid.",
        "zh_Hans": "帕鲁 ID 无效。",
    },
    "Rank must be a number.": {
        "en": "Rank must be a number.",
        "zh_Hans": "浓缩等级必须是数字。",
    },
    "Rank cannot be higher than 5.": {
        "en": "Rank cannot be higher than 5.",
        "zh_Hans": "浓缩等级不能高于 5。",
    },
    "Rank HP must be a number.": {
        "en": "Rank HP must be a number.",
        "zh_Hans": "最大 HP 强化等级必须是数字。",
    },
    "Rank HP cannot be higher than 10.": {
        "en": "Rank HP cannot be higher than 10.",
        "zh_Hans": "最大 HP 强化等级不能高于 10。",
    },
    "Rank Attack must be a number.": {
        "en": "Rank Attack must be a number.",
        "zh_Hans": "攻击 强化等级必须是数字。",
    },
    "Rank Attack cannot be higher than 10.": {
        "en": "Rank Attack cannot be higher than 10.",
        "zh_Hans": "攻击 强化等级不能高于 10。",
    },
    "Rank Defense must be a number.": {
        "en": "Rank Defense must be a number.",
        "zh_Hans": "防御 强化等级必须是数字。",
    },
    "Rank Defense cannot be higher than 10.": {
        "en": "Rank Defense cannot be higher than 10.",
        "zh_Hans": "防御 强化等级不能高于 10。",
    },
    "Rank CraftSpeed must be a number.": {
        "en": "Rank CraftSpeed must be a number.",
        "zh_Hans": "工作速度 强化等级必须是数字。",
    },
    "Rank CraftSpeed cannot be higher than 10.": {
        "en": "Rank CraftSpeed cannot be higher than 10.",
        "zh_Hans": "工作速度 强化等级不能高于 10。",
    },
    "Talent HP must be a number.": {
        "en": "Talent HP must be a number.",
        "zh_Hans": "个体：HP 必须是数字。",
    },
    "Talent HP cannot be higher than 100.": {
        "en": "Talent HP cannot be higher than 100.",
        "zh_Hans": "个体：HP 不能高于 100。",
    },
    "Talent Melee must be a number.": {
        "en": "Talent Melee must be a number.",
        "zh_Hans": "个体：近战 必须是数字。",
    },
    "Talent Melee cannot be higher than 100.": {
        "en": "Talent Melee cannot be higher than 100.",
        "zh_Hans": "个体：近战 不能高于 100。",
    },
    "Talent Shot must be a number.": {
        "en": "Talent Shot must be a number.",
        "zh_Hans": "个体：远程 必须是数字。",
    },
    "Talent Shot cannot be higher than 100.": {
        "en": "Talent Shot cannot be higher than 100.",
        "zh_Hans": "个体：远程 不能高于 100。",
    },
    "Talent Defense must be a number.": {
        "en": "Talent Defense must be a number.",
        "zh_Hans": "个体：防御 必须是数字。",
    },
    "Talent Defense cannot be higher than 100.": {
        "en": "Talent Defense cannot be higher than 100.",
        "zh_Hans": "个体：防御 不能高于 100。",
    },
    "Select Waza": {
        "en": "Select Waza",
        "zh_Hans": "选择技能",
    },
    "Confirm": {
        "en": "Confirm",
        "zh_Hans": "确认",
    },
    "Edit Passive Skills": {
        "en": "Edit Passive Skills",
        "zh_Hans": "编辑被动技能",
    },
    "Passive Skill ID": {
        "en": "Passive Skill ID",
        "zh_Hans": "被动技能 ID",
    },
    "Passive Skills cannot have more than 4.": {
        "en": "Passive Skills cannot have more than 4.",
        "zh_Hans": "被动技能不能超过 4 个。",
    },
    "Enter Passive Skill ID": {
        "en": "Enter Passive Skill ID",
        "zh_Hans": "输入被动技能 ID",
    },
    "Passive Skill ID is invalid.": {
        "en": "Passive Skill ID is invalid.",
        "zh_Hans": "被动技能 ID 无效。",
    },
    "Duplicate Passive Skill ID is not allowed.": {
        "en": "Duplicate Passive Skill ID is not allowed.",
        "zh_Hans": "不允许重复的被动技能 ID。",
    },
    "Select Passive Skill": {
        "en": "Select Passive Skill",
        "zh_Hans": "选择被动技能",
    },
}
