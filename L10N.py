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
}
