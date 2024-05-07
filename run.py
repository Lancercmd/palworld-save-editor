from __future__ import annotations

import asyncio
import json
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sys import modules
from tkinter import filedialog, messagebox, ttk

from save_tools import palworld_save_tools

modules["palworld_save_tools"] = palworld_save_tools
from L10N import L10N
from save_tools.palworld_save_tools.gvas import GvasFile
from save_tools.palworld_save_tools.json_tools import CustomEncoder
from save_tools.palworld_save_tools.palsav import (
    compress_gvas_to_sav,
    decompress_sav_to_gvas,
)
from save_tools.palworld_save_tools.paltypes import (
    PALWORLD_CUSTOM_PROPERTIES,
    PALWORLD_TYPE_HINTS,
)
from unpack import CHARACTER_IDS, DT_PET, KV_PASSIVE_SKILL, KV_WAZA


async def get_submodule_commit():
    result = await asyncio.create_subprocess_exec(
        "git", "submodule", "status", "save_tools", stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await result.communicate()
    commit_id, path_name, git_desc = stdout.decode().strip().partition(" ")
    return git_desc


def convert_sav_to_dict(
    file_path: Path, allow_nan=True, custom_properties_keys=["all"]
):
    print(f"Converting {file_path.name} to JSON")
    print(f"Decompressing sav file")
    raw_gvas, _ = decompress_sav_to_gvas(file_path.read_bytes())
    print(f"Loading GVAS file")
    custom_properties = {}
    if len(custom_properties_keys) > 0 and custom_properties_keys[0] == "all":
        custom_properties = PALWORLD_CUSTOM_PROPERTIES
    else:
        for prop in PALWORLD_CUSTOM_PROPERTIES:
            if prop in custom_properties_keys:
                custom_properties[prop] = PALWORLD_CUSTOM_PROPERTIES[prop]
    gvas_file = GvasFile.read(
        raw_gvas, PALWORLD_TYPE_HINTS, custom_properties, allow_nan=allow_nan
    )
    return json.loads(
        json.dumps(gvas_file.dump(), cls=CustomEncoder, allow_nan=allow_nan)
    )


def convert_dict_to_sav(data: dict, output_path: Path):
    gvas_file = GvasFile.load(data)
    print(f"Compressing SAV file")
    if (
        "Pal.PalWorldSaveGame" in gvas_file.header.save_game_class_name
        or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name
    ):
        save_type = 0x32
    else:
        save_type = 0x31
    sav_file = compress_gvas_to_sav(
        gvas_file.write(PALWORLD_CUSTOM_PROPERTIES), save_type
    )
    print(f"Writing SAV file to {output_path.name}")
    output_path.write_bytes(sav_file)


FILE_TYPES = [
    ["Palworld 主存档", "sav"],
    ["Palworld 主存档 JSON", "json"],
]
FILE_TYPES.insert(0, ["所有支持的文件类型", tuple(i[1] for i in FILE_TYPES)])


@dataclass
class Guild:
    group_data: dict

    def config(self, key: str, value):
        if key in self.keys_map:
            group_data = self.group_data
            for k in self.keys_map[key][:-1]:
                group_data = group_data[k]
            group_data[self.keys_map[key][-1]] = value
            setattr(self, key, value)
        else:
            raise ValueError(f"Guild.{key} 是无法编辑的。")

    def __post_init__(self):
        self.group_type: str = self.group_data["group_type"]
        self.group_id: str = self.group_data["group_id"]
        self.group_name: str = self.group_data["group_name"]
        self.individual_character_handle_ids: list[dict[str]] = self.group_data[
            "individual_character_handle_ids"
        ]
        self.org_type: int = self.group_data["org_type"]
        self.base_ids: list = self.group_data.get("base_ids", [])
        self.base_camp_level: int = (
            self.group_data["base_camp_level"]
            if self.group_data.get("base_camp_level")
            else 1
        )
        self.map_object_instance_ids_base_camp_points: list[str] = self.group_data[
            "map_object_instance_ids_base_camp_points"
        ]
        self.guild_name: str = self.group_data.get("guild_name")
        self.admin_player_uid: str = self.group_data.get("admin_player_uid")
        self.players: list = self.group_data.get("players", [])

        self.base_ids_count = len(self.base_ids)
        self.players_count = len(self.players)

    @property
    def keys_map(self):
        return {"guild_name": ["guild_name"], "base_camp_level": ["base_camp_level"]}

    @property
    def values(self):
        return [
            self.group_id,
            self.guild_name,
            self.base_camp_level,
            self.base_ids_count,
            self.players_count,
        ]


class GuildEditWindow(tk.Toplevel):
    def __init__(self, parent: Application, guild: Guild):
        super().__init__(parent)
        self.parent = parent
        self.guild = guild
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Edit Guild"))
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.group_id_frame = ttk.Frame(self)
        self.group_id_frame.pack(fill=tk.X, expand=True)

        self.group_id_label = ttk.Label(
            self.group_id_frame, text=self.l10n.get("Guild ID")
        )
        self.group_id_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.group_id_stringvar = tk.StringVar(value=self.guild.group_id)
        self.group_id_entry = ttk.Entry(
            self.group_id_frame, textvariable=self.group_id_stringvar, state=tk.DISABLED
        )
        self.group_id_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.guild_name_frame = ttk.Frame(self)
        self.guild_name_frame.pack(fill=tk.X, expand=True)

        self.guild_name_label = ttk.Label(
            self.guild_name_frame, text=self.l10n.get("Guild Name")
        )
        self.guild_name_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.guild_name_stringvar = tk.StringVar(value=self.guild.guild_name)
        self.guild_name_entry = ttk.Entry(
            self.guild_name_frame, textvariable=self.guild_name_stringvar
        )
        self.guild_name_entry.bind("<Return>", lambda _: self.save())
        self.guild_name_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.base_camp_level_frame = ttk.Frame(self)
        self.base_camp_level_frame.pack(fill=tk.X, expand=True)

        self.base_camp_level_label = ttk.Label(
            self.base_camp_level_frame, text=self.l10n.get("Base Camp Level")
        )
        self.base_camp_level_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        validate_level_input_command = self.register(self.validate_level_input)

        self.base_camp_level_stringvar = tk.StringVar(value=self.guild.base_camp_level)
        self.base_camp_level_entry = ttk.Spinbox(
            self.base_camp_level_frame,
            from_=1,
            to=20,
            textvariable=self.base_camp_level_stringvar,
            validate="key",
            validatecommand=(validate_level_input_command, "%P"),
            width=18,
        )
        self.base_camp_level_entry.bind("<Return>", lambda _: self.save())
        self.base_camp_level_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.save_button = ttk.Button(
            self, text=self.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def validate_level_input(self, level: str):
        if not level.isdigit():
            return False
        if int(level) < 1 or int(level) > 20:
            return False
        return True

    def validate(self):
        if not self.guild_name_entry.get():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Guild Name cannot be empty."),
                parent=self,
            )
            return False
        if not self.base_camp_level_entry.get():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Base Camp Level cannot be empty."),
                parent=self,
            )
            return False
        return True

    def save(self):
        if not self.validate():
            return
        if self.guild.guild_name != self.guild_name_entry.get():
            self.guild.config("guild_name", self.guild_name_entry.get())
            self.modified = True
        if self.guild.base_camp_level != int(self.base_camp_level_entry.get()):
            self.guild.config("base_camp_level", int(self.base_camp_level_entry.get()))
            self.modified = True
        self.destroy()

        if not self.modified:
            return
        # 更新父窗口的数据
        self.parent.guild_list.delete(*self.parent.guild_list.get_children())
        guild_map = {k: v for k, v in self.parent.guild_map.items()}
        self.parent.guild_map.clear()
        for guild in guild_map.values():
            row_id = self.parent.guild_list.insert("", "end", values=guild.values)
            self.parent.guild_map[row_id] = guild

    def destroy(self) -> None:
        self.parent.focus_set()
        return super().destroy()


@dataclass
class Player:
    character_data: dict
    guild_data: Guild
    player_uid: str
    last_online_real_time: str

    def config(self, key: str, value):
        if key in self.keys_map:
            character_data = self.character_data
            for k in self.keys_map[key][:-1]:

                if not k in character_data:
                    if k == "Exp":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "NickName":
                        character_data[k] = {
                            "id": None,
                            "value": "",
                            "type": "StrProperty",
                        }

                character_data = character_data[k]
            character_data[self.keys_map[key][-1]] = value
            setattr(self, key, value)
        else:
            raise ValueError(f"Player.{key} 是无法编辑的。")

    def __post_init__(self):
        self.level: int = (
            self.character_data["Level"]["value"]
            if self.character_data.get("Level")
            else 1
        )
        self.exp: int = (
            self.character_data["Exp"]["value"] if self.character_data.get("Exp") else 0
        )
        self.nickname: str = self.character_data["NickName"]["value"]
        self.hp: int = self.character_data["HP"]["value"]["Value"]["value"]
        self.full_stomach: float = self.character_data["FullStomach"]["value"]
        self.is_player: bool = self.character_data["IsPlayer"]["value"]
        self.support: int = self.character_data["Support"]["value"]
        self.craft_speed: int = self.character_data["CraftSpeed"]["value"]
        self.craft_speeds: list = self.character_data["CraftSpeeds"]["value"]["values"]
        self.shield_hp: int = (
            self.character_data["ShieldHP"]["value"]["Value"]["value"]
            if self.character_data.get("ShieldHP")
            else 0
        )
        self.shield_max_hp: int = (
            self.character_data["ShieldMaxHP"]["value"]["Value"]["value"]
            if self.character_data.get("ShieldMaxHP")
            else 0
        )
        self.max_sp: int = (
            self.character_data["MaxSP"]["value"]
            if self.character_data.get("MaxSP")
            else 0
        )
        self.sanity_value: float = (
            self.character_data["SanityValue"]["value"]
            if self.character_data.get("SanityValue")
            else 100.0
        )
        self.unused_status_point: int = (
            self.character_data["UnusedStatusPoint"]["value"]
            if self.character_data.get("UnusedStatusPoint")
            else 0
        )
        self.got_status_point_list: list[dict] = (
            self.character_data["GotStatusPointList"]["value"]["values"]
            if self.character_data.get("GotStatusPointList")
            else []
        )
        self.got_ex_status_point_list: list[dict] = (
            self.character_data["GotExStatusPointList"]["value"]["values"]
            if self.character_data.get("GotExStatusPointList")
            else []
        )
        self.last_jumped_location: dict = (
            self.character_data["LastJumpedLocation"]["value"]
            if self.character_data.get("LastJumpedLocation")
            else {"x": 0.0, "y": 0.0, "z": 0.0}
        )
        self.voice_id: int = self.character_data["VoiceID"]["value"]

        self.group_id = self.guild_data.group_id
        self.guild_name = self.guild_data.guild_name

    @property
    def keys_map(self):
        return {"exp": ["Exp", "value"], "nickname": ["NickName", "value"]}

    @property
    def values(self):
        return [
            self.group_id,
            self.guild_name,
            self.player_uid,
            self.nickname,
            self.level,
            self.exp,
            self.last_online_real_time,
        ]


class PlayerEditWindow(tk.Toplevel):
    def __init__(self, parent: Application, player: Player):
        super().__init__(parent)
        self.parent = parent
        self.player = player
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Edit Player"))
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.player_uid_frame = ttk.Frame(self)
        self.player_uid_frame.pack(fill=tk.X, expand=True)

        self.player_uid_label = ttk.Label(
            self.player_uid_frame, text=self.l10n.get("Player UID")
        )
        self.player_uid_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.player_uid_stringvar = tk.StringVar(value=self.player.player_uid)
        self.player_uid_entry = ttk.Entry(
            self.player_uid_frame,
            textvariable=self.player_uid_stringvar,
            state=tk.DISABLED,
        )
        self.player_uid_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.nickname_frame = ttk.Frame(self)
        self.nickname_frame.pack(fill=tk.X, expand=True)

        self.nickname_label = ttk.Label(
            self.nickname_frame, text=self.l10n.get("Nickname")
        )
        self.nickname_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.nickname_stringvar = tk.StringVar(value=self.player.nickname)
        self.nickname_entry = ttk.Entry(
            self.nickname_frame, textvariable=self.nickname_stringvar
        )
        self.nickname_entry.bind("<Return>", lambda _: self.save())
        self.nickname_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.level_frame = ttk.Frame(self)
        self.level_frame.pack(fill=tk.X, expand=True)

        self.level_label = ttk.Label(self.level_frame, text=self.l10n.get("Level"))
        self.level_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        validate_level_input_command = self.register(self.validate_level_input)

        self.level_stringvar = tk.StringVar(value=self.player.level)
        self.level_entry = ttk.Spinbox(
            self.level_frame,
            from_=max(2, self.player.level),
            to=50,
            textvariable=self.level_stringvar,
            validate="key",
            validatecommand=(validate_level_input_command, "%P"),
            width=17,
        )
        self.level_entry.bind("<Return>", lambda _: self.save())
        self.level_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 4,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.exp_frame = ttk.Frame(self)
        self.exp_frame.pack(fill=tk.X, expand=True)

        self.exp_label = ttk.Label(self.exp_frame, text=self.l10n.get("Exp"))
        self.exp_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.exp_entry_align_button = ttk.Button(
            self.exp_frame, text=self.l10n.get("Align"), command=self.validate, width=6
        )
        self.exp_entry_align_button.pack(
            side=tk.RIGHT,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.exp_stringvar = tk.StringVar(value=self.player.exp)
        self.exp_entry = ttk.Entry(
            self.exp_frame, textvariable=self.exp_stringvar, state=tk.DISABLED, width=10
        )
        self.exp_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 2,
            ipady=self.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self, text=self.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def validate_level_input(self, level: str):
        if not level.isdigit():
            return False
        if int(level) > 50:
            return False
        if int(self.level_entry.get()) != self.player.level:
            self.exp_stringvar.set(DT_PET[level]["TotalEXP"] - 1)
        else:
            self.exp_stringvar.set(self.player.exp)
        return True

    def validate(self):
        if not self.nickname_entry.get():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Nickname cannot be empty."),
                parent=self,
            )
            return False
        if not self.level_entry.get():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Level cannot be empty."),
                parent=self,
            )
            return False
        if not self.level_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Level must be a number."),
                parent=self,
            )
            return False
        # 等级不能低于当前等级
        if int(self.level_entry.get()) < self.player.level:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Level cannot be lower than the current."),
                parent=self,
            )
            return False
        if int(self.level_entry.get()) != self.player.level:
            self.exp_stringvar.set(DT_PET[self.level_entry.get()]["TotalEXP"] - 1)
        else:
            self.exp_stringvar.set(self.player.exp)
        return True

    def save(self):
        if not self.validate():
            return
        if self.player.nickname != self.nickname_entry.get():
            self.player.config("nickname", self.nickname_entry.get())
            self.modified = True
        if self.player.level != int(self.level_entry.get()) and self.player.exp != int(
            self.exp_entry.get()
        ):
            self.player.config("exp", int(self.exp_entry.get()))
            self.modified = True
        self.destroy()

        if not self.modified:
            return
        # 更新父窗口的数据
        self.parent.player_list.delete(*self.parent.player_list.get_children())
        player_map = {k: v for k, v in self.parent.player_map.items()}
        self.parent.player_map.clear()
        for player in player_map.values():
            row_id = self.parent.player_list.insert("", "end", values=player.values)
            self.parent.player_map[row_id] = player

    def destroy(self) -> None:
        self.parent.focus_set()
        return super().destroy()


def encode_gender(gender: str):
    return "EPalGenderType::" + gender


@dataclass
class Pal:
    instance_id: str
    character_data: dict

    def config(self, key: str, value):
        if key in self.keys_map:
            character_data = self.character_data
            for k in self.keys_map[key][:-1]:

                if not k in character_data:
                    if k == "CharacterID":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "NameProperty",
                        }
                    elif k == "Gender":
                        character_data[k] = {
                            "id": None,
                            "value": {
                                "type": "EPalGenderType",
                                "value": "EPalGenderType::Male",
                            },
                            "type": "EnumProperty",
                        }
                    elif k == "Rank":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Rank_HP":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Rank_Attack":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Rank_Defence":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Rank_CraftSpeed":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Exp":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "IsRarePal":
                        character_data[k] = {
                            "id": None,
                            "value": False,
                            "type": "BoolProperty",
                        }
                    elif k == "EquipWaza":
                        character_data[k] = {
                            "array_type": "EnumProperty",
                            "id": None,
                            "value": {"values": []},
                            "type": "ArrayProperty",
                        }
                    elif k == "MasteredWaza":
                        character_data[k] = {
                            "array_type": "EnumProperty",
                            "id": None,
                            "value": {"values": []},
                            "type": "ArrayProperty",
                        }
                    elif k == "Talent_HP":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Talent_Melee":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Talent_Shot":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "Talent_Defense":
                        character_data[k] = {
                            "id": None,
                            "value": 0,
                            "type": "IntProperty",
                        }
                    elif k == "PassiveSkillList":
                        character_data[k] = {
                            "array_type": "EnumProperty",
                            "id": None,
                            "value": {"values": []},
                            "type": "ArrayProperty",
                        }

                character_data = character_data[k]
            if key == "gender":
                character_data[self.keys_map[key][-1]] = encode_gender(value)
            else:
                character_data[self.keys_map[key][-1]] = value
            setattr(self, key, value)
        else:
            raise ValueError(f"Pal.{key} 是无法编辑的。")

    def __post_init__(self):
        self.character_id: str = self.character_data["CharacterID"]["value"]
        self.gender = get_gender(self.character_data)
        self.level: int = (
            self.character_data["Level"]["value"]
            if self.character_data.get("Level")
            else 1
        )
        self.rank: int = (
            self.character_data["Rank"]["value"]
            if self.character_data.get("Rank")
            else 0
        )
        self.rank_hp: int = (
            self.character_data["Rank_HP"]["value"]
            if self.character_data.get("Rank_HP")
            else 0
        )
        self.rank_attack: int = (
            self.character_data["Rank_Attack"]["value"]
            if self.character_data.get("Rank_Attack")
            else 0
        )
        self.rank_defense: int = (
            self.character_data["Rank_Defence"]["value"]
            if self.character_data.get("Rank_Defence")
            else 0
        )
        self.rank_craft_speed: int = (
            self.character_data["Rank_CraftSpeed"]["value"]
            if self.character_data.get("Rank_CraftSpeed")
            else 0
        )
        self.exp: int = (
            self.character_data["Exp"]["value"] if self.character_data.get("Exp") else 0
        )
        self.is_rare_pal: bool = (
            self.character_data["IsRarePal"]["value"]
            if self.character_data.get("IsRarePal")
            else False
        )
        self.equip_waza: list = (
            self.character_data["EquipWaza"]["value"]["values"]
            if self.character_data.get("EquipWaza")
            else []
        )
        self.mastered_waza: list = (
            self.character_data["MasteredWaza"]["value"]["values"]
            if self.character_data.get("MasteredWaza")
            else []
        )
        self.hp: int = (
            self.character_data["HP"]["value"]["Value"]["value"] // 1000
            if self.character_data.get("HP")
            else 0
        )
        self.talent_hp: int = (
            self.character_data["Talent_HP"]["value"]
            if self.character_data.get("Talent_HP")
            else 0
        )
        self.talent_melee: int = (
            self.character_data["Talent_Melee"]["value"]
            if self.character_data.get("Talent_Melee")
            else 0
        )
        self.talent_shot: int = (
            self.character_data["Talent_Shot"]["value"]
            if self.character_data.get("Talent_Shot")
            else 0
        )
        self.talent_defense: int = (
            self.character_data["Talent_Defense"]["value"]
            if self.character_data.get("Talent_Defense")
            else 0
        )
        self.full_stomach: float = (
            self.character_data["FullStomach"]["value"]
            if self.character_data.get("FullStomach")
            else 0.0
        )
        self.passive_skill_list = (
            self.character_data["PassiveSkillList"]["value"]["values"]
            if self.character_data.get("PassiveSkillList")
            else []
        )
        self.mp: int = (
            self.character_data["MP"]["value"] if self.character_data.get("MP") else 0
        )
        self.old_owner_player_uids: list[str] = self.character_data[
            "OldOwnerPlayerUIds"
        ]["value"]
        self.max_hp: int = (
            self.character_data["MaxHP"]["value"]["Value"]["value"]
            if self.character_data.get("MaxHP")
            else 0
        )
        self.craft_speed: int = self.character_data["CraftSpeed"]["value"]
        self.craft_speeds: list[dict] = self.character_data["CraftSpeeds"]["value"]
        self.sanity_value: float = (
            int(self.character_data["SanityValue"]["value"])
            if self.character_data.get("SanityValue")
            else 100.0
        )
        self.item_container_id: str = (
            self.character_data["ItemContainerId"]["value"]
            if self.character_data.get("ItemContainerId")
            else ""
        )
        self.equip_item_container_id: str = self.character_data["EquipItemContainerId"][
            "value"
        ]
        self.slot_id: str = self.character_data["SlotID"]["value"]["ContainerId"][
            "value"
        ]["ID"]["value"]
        self.max_full_stomach: float = (
            self.character_data["MaxFullStomach"]["value"]
            if self.character_data.get("MaxFullStomach")
            else 0.0
        )
        self.got_status_point_list: list[dict] = (
            self.character_data["GotStatusPointList"]["value"]["values"]
            if self.character_data.get("GotStatusPointList")
            else []
        )
        self.got_ex_status_point_list: list[dict] = (
            self.character_data["GotExStatusPointList"]["value"]["values"]
            if self.character_data.get("GotExStatusPointList")
            else []
        )
        self.decrease_full_stomach_rates = (
            self.character_data["DecreaseFullStomachRates"]["value"]
            if self.character_data.get("DecreaseFullStomachRates")
            else {}
        )
        self.affect_sanity_rates = (
            self.character_data["AffectSanityRates"]["value"]
            if self.character_data.get("AffectSanityRates")
            else {}
        )
        self.craft_speed_rates = (
            self.character_data["CraftSpeedRates"]["value"]
            if self.character_data.get("CraftSpeedRates")
            else {}
        )
        self.last_jumped_location = (
            self.character_data["LastJumpedLocation"]["value"]
            if self.character_data.get("LastJumpedLocation")
            else {"x": 0.0, "y": 0.0, "z": 0.0}
        )

    @property
    def keys_map(self):
        return {
            "character_id": ["CharacterID", "value"],
            "gender": ["Gender", "value", "value"],
            "rank": ["Rank", "value"],
            "rank_hp": ["Rank_HP", "value"],
            "rank_attack": ["Rank_Attack", "value"],
            "rank_defense": ["Rank_Defence", "value"],
            "rank_craft_speed": ["Rank_CraftSpeed", "value"],
            "exp": ["Exp", "value"],
            "is_rare_pal": ["IsRarePal", "value"],
            "equip_waza": ["EquipWaza", "value", "values"],
            "mastered_waza": ["MasteredWaza", "value", "values"],
            "talent_hp": ["Talent_HP", "value"],
            "talent_melee": ["Talent_Melee", "value"],
            "talent_shot": ["Talent_Shot", "value"],
            "talent_defense": ["Talent_Defense", "value"],
            "passive_skill_list": ["PassiveSkillList", "value", "values"],
        }

    @property
    def values(self):
        return [
            self.character_id,
            self.gender,
            self.level,
            self.exp,
            self.talent_hp,
            self.talent_melee,
            self.talent_shot,
            self.talent_defense,
            self.passive_skill_list,
        ]


class PalEditWindow(tk.Toplevel):
    def __init__(self, parent: Application, pal: Pal):
        super().__init__(parent)
        self.parent = parent
        self.pal = pal
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Edit Pal"))
        self.minsize(600, 400)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.instance_id_frame = ttk.Frame(self)
        self.instance_id_frame.pack(fill=tk.X, pady=self.recommended_ipady)

        self.instance_id_label = ttk.Label(
            self.instance_id_frame, text=self.l10n.get("Instance ID")
        )
        self.instance_id_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.instance_id_stringvar = tk.StringVar(value=self.pal.instance_id)
        self.instance_id_entry = ttk.Entry(
            self.instance_id_frame,
            textvariable=self.instance_id_stringvar,
            state=tk.DISABLED,
        )
        self.instance_id_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.character_id_frame = ttk.Frame(self)
        self.character_id_frame.pack(fill=tk.X, pady=self.recommended_ipady)

        self.character_id_label = ttk.Label(
            self.character_id_frame, text=self.l10n.get("Character ID")
        )
        self.character_id_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.is_rare_pal_boolvar = tk.Variable(value=self.pal.is_rare_pal)
        self.is_rare_pal_checkbutton = ttk.Checkbutton(
            self.character_id_frame, variable=self.is_rare_pal_boolvar
        )
        self.is_rare_pal_checkbutton.pack(
            side=tk.RIGHT,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.is_rare_pal_label = ttk.Label(
            self.character_id_frame, text=self.l10n.get("Rare / Shining")
        )
        self.is_rare_pal_label.pack(
            side=tk.RIGHT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.character_id_entry_enable_button = ttk.Button(
            self.character_id_frame,
            text=self.l10n.get("Edit"),
            command=self.enable_character_id_entry,
        )
        self.character_id_entry_enable_button.pack(
            side=tk.RIGHT,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.character_id_stringvar = tk.StringVar(value=self.pal.character_id)
        self.character_id_entry = ttk.Entry(
            self.character_id_frame,
            textvariable=self.character_id_stringvar,
            state=tk.DISABLED,
        )
        self.character_id_entry.bind("<Return>", lambda _: self.save())
        self.character_id_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.frame_container = ttk.Frame(self)
        self.frame_container.pack(fill=tk.BOTH, expand=True)

        self.frame_left = ttk.Frame(self.frame_container)
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.frame_right = ttk.Frame(self.frame_container)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.gender_frame = ttk.Frame(self.frame_left)
        self.gender_frame.pack(fill=tk.X, expand=True)

        self.gender_frame_left = ttk.Frame(self.gender_frame)
        self.gender_frame_left.pack(side=tk.LEFT, fill=tk.BOTH)

        self.gender_frame_right = ttk.Frame(self.gender_frame)
        self.gender_frame_right.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.gender_label = ttk.Label(
            self.gender_frame_left, text=self.l10n.get("Gender")
        )
        self.gender_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.gender_button = ttk.Button(
            self.gender_frame_right,
            text=self.pal.gender,
            state=tk.NORMAL if self.pal.gender else tk.DISABLED,
            command=self.switch_gender,
            width=13,
        )
        self.gender_button.pack(
            side=tk.RIGHT,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.tips_label = ttk.Label(
            self.gender_frame_right,
            text=self.l10n.get("Click to switch" if self.pal.gender else ""),
            state=tk.DISABLED,
        )
        self.tips_label.pack(side=tk.LEFT)

        self.rank_frame = ttk.Frame(self.frame_left)
        self.rank_frame.pack(fill=tk.X, expand=True)

        self.rank_label = ttk.Label(self.rank_frame, text=self.l10n.get("Rank"))
        self.rank_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.validate_rank_input_command = self.register(self.validate_rank_input)

        self.rank_stringvar = tk.StringVar(value=self.pal.rank)
        self.rank_entry = ttk.Spinbox(
            self.rank_frame,
            from_=0,
            to=5,
            textvariable=self.rank_stringvar,
            validate="key",
            validatecommand=(self.validate_rank_input_command, "%P"),
        )
        self.rank_entry.bind("<Return>", lambda _: self.save())
        self.rank_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.rank_hp_frame = ttk.Frame(self.frame_left)
        self.rank_hp_frame.pack(fill=tk.X, expand=True)

        self.rank_hp_label = ttk.Label(
            self.rank_hp_frame, text=self.l10n.get("Rank HP")
        )
        self.rank_hp_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.validate_rank_hp_input_command = self.register(self.validate_rank_hp_input)

        self.rank_hp_stringvar = tk.StringVar(value=self.pal.rank_hp)
        self.rank_hp_entry = ttk.Spinbox(
            self.rank_hp_frame,
            from_=0,
            to=10,
            textvariable=self.rank_hp_stringvar,
            validate="key",
            validatecommand=(self.validate_rank_hp_input_command, "%P"),
        )
        self.rank_hp_entry.bind("<Return>", lambda _: self.save())
        self.rank_hp_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.rank_attack_frame = ttk.Frame(self.frame_left)
        self.rank_attack_frame.pack(fill=tk.X, expand=True)

        self.rank_attack_label = ttk.Label(
            self.rank_attack_frame, text=self.l10n.get("Rank Attack")
        )
        self.rank_attack_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_rank_attack_input_command = self.register(
            self.validate_rank_attack_input
        )

        self.rank_attack_stringvar = tk.StringVar(value=self.pal.rank_attack)
        self.rank_attack_entry = ttk.Spinbox(
            self.rank_attack_frame,
            from_=0,
            to=10,
            textvariable=self.rank_attack_stringvar,
            validate="key",
            validatecommand=(self.validate_rank_attack_input_command, "%P"),
        )
        self.rank_attack_entry.bind("<Return>", lambda _: self.save())
        self.rank_attack_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.rank_defense_frame = ttk.Frame(self.frame_left)
        self.rank_defense_frame.pack(fill=tk.X, expand=True)

        self.rank_defense_label = ttk.Label(
            self.rank_defense_frame, text=self.l10n.get("Rank Defense")
        )
        self.rank_defense_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_rank_defense_input_command = self.register(
            self.validate_rank_defense_input
        )

        self.rank_defense_stringvar = tk.StringVar(value=self.pal.rank_defense)
        self.rank_defense_entry = ttk.Spinbox(
            self.rank_defense_frame,
            from_=0,
            to=10,
            textvariable=self.rank_defense_stringvar,
            validate="key",
            validatecommand=(self.validate_rank_defense_input_command, "%P"),
        )
        self.rank_defense_entry.bind("<Return>", lambda _: self.save())
        self.rank_defense_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.rank_craft_speed_frame = ttk.Frame(self.frame_left)
        self.rank_craft_speed_frame.pack(fill=tk.X, expand=True)

        self.rank_craft_speed_label = ttk.Label(
            self.rank_craft_speed_frame, text=self.l10n.get("Rank CraftSpeed")
        )
        self.rank_craft_speed_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_rank_craft_speed_input_command = self.register(
            self.validate_rank_craft_speed_input
        )

        self.rank_craft_speed_stringvar = tk.StringVar(value=self.pal.rank_craft_speed)
        self.rank_craft_speed_entry = ttk.Spinbox(
            self.rank_craft_speed_frame,
            from_=0,
            to=10,
            textvariable=self.rank_craft_speed_stringvar,
            validate="key",
            validatecommand=(self.validate_rank_craft_speed_input_command, "%P"),
        )
        self.rank_craft_speed_entry.bind("<Return>", lambda _: self.save())
        self.rank_craft_speed_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.level_frame = ttk.Frame(self.frame_left)
        self.level_frame.pack(fill=tk.X, expand=True)

        self.level_label = ttk.Label(self.level_frame, text=self.l10n.get("Level"))
        self.level_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        validate_level_input_command = self.register(self.validate_level_input)

        self.level_stringvar = tk.StringVar(value=self.pal.level)
        self.level_entry = ttk.Spinbox(
            self.level_frame,
            from_=max(2, self.pal.level),
            to=50,
            textvariable=self.level_stringvar,
            validate="key",
            validatecommand=(validate_level_input_command, "%P"),
        )
        self.level_entry.bind("<Return>", lambda _: self.save())
        self.level_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.exp_frame = ttk.Frame(self.frame_left)
        self.exp_frame.pack(fill=tk.X, expand=True)

        self.exp_label = ttk.Label(self.exp_frame, text=self.l10n.get("Exp"))
        self.exp_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.exp_entry_align_button = ttk.Button(
            self.exp_frame, text=self.l10n.get("Align"), command=self.validate, width=6
        )
        self.exp_entry_align_button.pack(
            side=tk.RIGHT,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.exp_stringvar = tk.StringVar(value=self.pal.exp)
        self.exp_entry = ttk.Entry(
            self.exp_frame, textvariable=self.exp_stringvar, state=tk.DISABLED, width=10
        )
        self.exp_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 8,
            ipady=self.recommended_ipady,
            # padx=self.recommended_ipadx
        )

        self.equip_waza_frame = ttk.Frame(self.frame_right)
        self.equip_waza_frame.pack(fill=tk.X, expand=True)

        self.equip_waza_label = ttk.Label(
            self.equip_waza_frame, text=self.l10n.get("Equip Waza")
        )
        self.equip_waza_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.equip_waza_listvar = tk.Variable(value=self.pal.equip_waza)
        self.equip_waza_button = ttk.Button(
            self.equip_waza_frame,
            text=self.l10n.get("Editor"),
            command=self.on_click_equip_waza_button,
            width=14,
        )
        self.equip_waza_button.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 2,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.equip_waza_modified_stringvar = tk.StringVar(
            value=(
                self.l10n.get("Modified")
                if list(self.equip_waza_listvar.get()) != self.pal.equip_waza
                else None
            )
        )
        self.equip_waza_modified_label = ttk.Label(
            self.equip_waza_frame,
            textvariable=self.equip_waza_modified_stringvar,
            state=tk.DISABLED,
        )
        self.equip_waza_modified_label.pack(side=tk.RIGHT, anchor=tk.E, fill=tk.X)

        self.mastered_waza_frame = ttk.Frame(self.frame_right)
        self.mastered_waza_frame.pack(fill=tk.X, expand=True)

        self.mastered_waza_label = ttk.Label(
            self.mastered_waza_frame, text=self.l10n.get("Mastered Waza")
        )
        self.mastered_waza_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.mastered_waza_listvar = tk.Variable(value=self.pal.mastered_waza)
        self.mastered_waza_button = ttk.Button(
            self.mastered_waza_frame,
            text=self.l10n.get("Editor"),
            command=self.on_click_mastered_waza_button,
            width=14,
        )
        self.mastered_waza_button.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 2,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.mastered_waza_modified_stringvar = tk.StringVar(
            value=(
                self.l10n.get("Modified")
                if list(self.mastered_waza_listvar.get()) != self.pal.mastered_waza
                else None
            )
        )
        self.mastered_waza_modified_label = ttk.Label(
            self.mastered_waza_frame,
            textvariable=self.mastered_waza_modified_stringvar,
            state=tk.DISABLED,
        )
        self.mastered_waza_modified_label.pack(side=tk.RIGHT, anchor=tk.E, fill=tk.X)

        self.talent_hp_frame = ttk.Frame(self.frame_right)
        self.talent_hp_frame.pack(fill=tk.X, expand=True)

        self.talent_hp_label = ttk.Label(
            self.talent_hp_frame, text=self.l10n.get("Talent: HP")
        )
        self.talent_hp_label.pack(side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx)

        self.validate_talent_hp_input_command = self.register(
            self.validate_talent_hp_input
        )

        self.talent_hp_stringvar = tk.StringVar(value=self.pal.talent_hp)
        self.talent_hp_entry = ttk.Spinbox(
            self.talent_hp_frame,
            from_=0,
            to=100,
            textvariable=self.talent_hp_stringvar,
            validate="key",
            validatecommand=(self.validate_talent_hp_input_command, "%P"),
        )
        self.talent_hp_entry.bind("<Return>", lambda _: self.save())
        self.talent_hp_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.talent_melee_frame = ttk.Frame(self.frame_right)
        self.talent_melee_frame.pack(fill=tk.X, expand=True)

        self.talent_melee_label = ttk.Label(
            self.talent_melee_frame, text=self.l10n.get("Talent: Melee")
        )
        self.talent_melee_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_talent_melee_input_command = self.register(
            self.validate_talent_melee_input
        )

        self.talent_melee_stringvar = tk.StringVar(value=self.pal.talent_melee)
        self.talent_melee_entry = ttk.Spinbox(
            self.talent_melee_frame,
            from_=0,
            to=100,
            textvariable=self.talent_melee_stringvar,
            validate="key",
            validatecommand=(self.validate_talent_melee_input_command, "%P"),
        )
        self.talent_melee_entry.bind("<Return>", lambda _: self.save())
        self.talent_melee_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.talent_shot_frame = ttk.Frame(self.frame_right)
        self.talent_shot_frame.pack(fill=tk.X, expand=True)

        self.talent_shot_label = ttk.Label(
            self.talent_shot_frame, text=self.l10n.get("Talent: Shot")
        )
        self.talent_shot_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_talent_shot_input_command = self.register(
            self.validate_talent_shot_input
        )

        self.talent_shot_stringvar = tk.StringVar(value=self.pal.talent_shot)
        self.talent_shot_entry = ttk.Spinbox(
            self.talent_shot_frame,
            from_=0,
            to=100,
            textvariable=self.talent_shot_stringvar,
            validate="key",
            validatecommand=(self.validate_talent_shot_input_command, "%P"),
        )
        self.talent_shot_entry.bind("<Return>", lambda _: self.save())
        self.talent_shot_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.talent_defense_frame = ttk.Frame(self.frame_right)
        self.talent_defense_frame.pack(fill=tk.X, expand=True)

        self.talent_defense_label = ttk.Label(
            self.talent_defense_frame, text=self.l10n.get("Talent: Defense")
        )
        self.talent_defense_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.validate_talent_defense_input_command = self.register(
            self.validate_talent_defense_input
        )

        self.talent_defense_stringvar = tk.StringVar(value=self.pal.talent_defense)
        self.talent_defense_entry = ttk.Spinbox(
            self.talent_defense_frame,
            from_=0,
            to=100,
            textvariable=self.talent_defense_stringvar,
            validate="key",
            validatecommand=(self.validate_talent_defense_input_command, "%P"),
        )
        self.talent_defense_entry.bind("<Return>", lambda _: self.save())
        self.talent_defense_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.passive_skill_list_frame = ttk.Frame(self.frame_right)
        self.passive_skill_list_frame.pack(fill=tk.X, expand=True)

        self.passive_skill_list_label = ttk.Label(
            self.passive_skill_list_frame, text=self.l10n.get("Passive Skills")
        )
        self.passive_skill_list_label.pack(
            side=tk.LEFT, fill=tk.X, padx=self.recommended_ipadx
        )

        self.passive_skill_list_listvar = tk.Variable(value=self.pal.passive_skill_list)
        self.passive_skill_list_button = ttk.Button(
            self.passive_skill_list_frame,
            text=self.l10n.get("Editor"),
            command=self.on_click_passive_skill_list_button,
            width=14,
        )
        self.passive_skill_list_button.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.recommended_ipadx + 2,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.passive_skill_list_modified_stringvar = tk.StringVar(
            value=(
                self.l10n.get("Modified")
                if list(self.passive_skill_list_listvar.get())
                != self.pal.passive_skill_list
                else None
            )
        )
        self.passive_skill_list_modified_label = ttk.Label(
            self.passive_skill_list_frame,
            textvariable=self.passive_skill_list_modified_stringvar,
            state=tk.DISABLED,
        )
        self.passive_skill_list_modified_label.pack(
            side=tk.RIGHT, anchor=tk.E, fill=tk.X
        )

        self.quick_action_frame = ttk.Frame(self.frame_right)
        self.quick_action_frame.pack(fill=tk.X, expand=True)

        self.ranks_max_button = ttk.Button(
            self.quick_action_frame,
            text=self.l10n.get("Ranks MAX"),
            command=self.on_click_ranks_max_button,
        )
        self.ranks_max_button.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.talents_max_button = ttk.Button(
            self.quick_action_frame,
            text=self.l10n.get("Talents MAX"),
            command=self.on_click_talents_max_button,
        )
        self.talents_max_button.pack(
            side=tk.RIGHT,
            fill=tk.X,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            padx=self.recommended_ipadx,
        )

        self.save_button = ttk.Button(
            self, text=self.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def on_click_ranks_max_button(self):
        self.rank_stringvar.set(5)
        self.rank_hp_stringvar.set(10)
        self.rank_attack_stringvar.set(10)
        self.rank_defense_stringvar.set(10)
        self.rank_craft_speed_stringvar.set(10)

    def on_click_talents_max_button(self):
        self.talent_hp_stringvar.set(100)
        self.talent_melee_stringvar.set(100)
        self.talent_shot_stringvar.set(100)
        self.talent_defense_stringvar.set(100)

    def on_click_equip_waza_button(self):
        self.waza_edit_window = WazaEditWindow(
            self, self.equip_waza_listvar, is_equip_waza=True
        )
        self.waza_edit_window.grab_set()

    def on_click_mastered_waza_button(self):
        self.waza_edit_window = WazaEditWindow(self, self.mastered_waza_listvar)
        self.waza_edit_window.grab_set()

    def on_click_passive_skill_list_button(self):
        self.passive_skill_list_edit_window = PassiveSkillListEditWindow(
            self, self.passive_skill_list_listvar
        )
        self.passive_skill_list_edit_window.grab_set()

    def validate_rank_input(self, rank: str):
        if not rank.isdigit():
            return False
        if int(rank) > 5:
            return False
        return True

    def validate_rank_hp_input(self, rank_hp: str):
        if not rank_hp.isdigit():
            return False
        if int(rank_hp) > 10:
            return False
        return True

    def validate_rank_attack_input(self, rank_attack: str):
        if not rank_attack.isdigit():
            return False
        if int(rank_attack) > 10:
            return False
        return True

    def validate_rank_defense_input(self, rank_defense: str):
        if not rank_defense.isdigit():
            return False
        if int(rank_defense) > 10:
            return False
        return True

    def validate_rank_craft_speed_input(self, rank_craft_speed: str):
        if not rank_craft_speed.isdigit():
            return False
        if int(rank_craft_speed) > 10:
            return False
        return True

    def validate_talent_hp_input(self, talent_hp: str):
        if not talent_hp.isdigit():
            return False
        if int(talent_hp) > 100:
            return False
        return True

    def validate_talent_melee_input(self, talent_melee: str):
        if not talent_melee.isdigit():
            return False
        if int(talent_melee) > 100:
            return False
        return True

    def validate_talent_shot_input(self, talent_shot: str):
        if not talent_shot.isdigit():
            return False
        if int(talent_shot) > 100:
            return False
        return True

    def validate_talent_defense_input(self, talent_defense: str):
        if not talent_defense.isdigit():
            return False
        if int(talent_defense) > 100:
            return False
        return True

    def validate_level_input(self, level: str):
        if not level.isdigit():
            return False
        if int(level) > 50:
            return False
        if int(self.level_entry.get()) != self.pal.level:
            self.exp_stringvar.set(DT_PET[level]["PalTotalEXP"] - 1)
        else:
            self.exp_stringvar.set(self.pal.exp)
        return True

    def switch_gender(self):
        if self.gender_button.cget("text") == "Male":
            self.gender_button.config(text="Female")
        else:
            self.gender_button.config(text="Male")

    def enable_character_id_entry(self):
        self.character_id_entry.config(state=tk.NORMAL)

    def validate(self):
        if str(self.character_id_entry.cget("state")) != tk.DISABLED:
            if not self.character_id_stringvar.get():
                messagebox.showerror(
                    self.l10n.get("Error"),
                    self.l10n.get("Character ID cannot be empty."),
                    parent=self,
                )
                return False
            if not self.character_id_stringvar.get() in CHARACTER_IDS:
                messagebox.showerror(
                    self.l10n.get("Error"),
                    self.l10n.get("Character ID is invalid."),
                    parent=self,
                )
                return False
        if not self.rank_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank must be a number."),
                parent=self,
            )
            return False
        if int(self.rank_entry.get()) > 5:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank cannot be higher than 5."),
                parent=self,
            )
            return False
        if not self.rank_hp_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank HP must be a number."),
                parent=self,
            )
            return False
        if int(self.rank_hp_entry.get()) > 10:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank HP cannot be higher than 10."),
                parent=self,
            )
            return False
        if not self.rank_attack_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank Attack must be a number."),
                parent=self,
            )
            return False
        if int(self.rank_attack_entry.get()) > 10:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank Attack cannot be higher than 10."),
                parent=self,
            )
            return False
        if not self.rank_defense_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank Defense must be a number."),
                parent=self,
            )
            return False
        if int(self.rank_defense_entry.get()) > 10:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank Defense cannot be higher than 10."),
                parent=self,
            )
            return False
        if not self.rank_craft_speed_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank CraftSpeed must be a number."),
                parent=self,
            )
            return False
        if int(self.rank_craft_speed_entry.get()) > 10:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Rank CraftSpeed cannot be higher than 10."),
                parent=self,
            )
            return False
        if not self.talent_hp_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent HP must be a number."),
                parent=self,
            )
            return False
        if int(self.talent_hp_entry.get()) > 100:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent HP cannot be higher than 100."),
                parent=self,
            )
            return False
        if not self.talent_melee_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Melee must be a number."),
                parent=self,
            )
            return False
        if int(self.talent_melee_entry.get()) > 100:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Melee cannot be higher than 100."),
                parent=self,
            )
            return False
        if not self.talent_shot_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Shot must be a number."),
                parent=self,
            )
            return False
        if int(self.talent_shot_entry.get()) > 100:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Shot cannot be higher than 100."),
                parent=self,
            )
            return False
        if not self.talent_defense_entry.get().isdigit():
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Defense must be a number."),
                parent=self,
            )
            return False
        if int(self.talent_defense_entry.get()) > 100:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Talent Defense cannot be higher than 100."),
                parent=self,
            )
            return False
        if int(self.level_entry.get()) != self.pal.level:
            self.exp_stringvar.set(DT_PET[self.level_entry.get()]["PalTotalEXP"] - 1)
        else:
            self.exp_stringvar.set(self.pal.exp)
        return True

    def save(self):
        if not self.validate():
            return
        if self.character_id_stringvar.get() != self.pal.character_id:
            self.pal.config("character_id", self.character_id_stringvar.get())
            self.modified = True
        if self.gender_button.cget("text") != self.pal.gender:
            self.pal.config("gender", self.gender_button.cget("text"))
            self.modified = True
        if int(self.rank_entry.get()) != self.pal.rank:
            self.pal.config("rank", int(self.rank_entry.get()))
            self.modified = True
        if int(self.rank_hp_entry.get()) != self.pal.rank_hp:
            self.pal.config("rank_hp", int(self.rank_hp_entry.get()))
            self.modified = True
        if int(self.rank_attack_entry.get()) != self.pal.rank_attack:
            self.pal.config("rank_attack", int(self.rank_attack_entry.get()))
            self.modified = True
        if int(self.rank_defense_entry.get()) != self.pal.rank_defense:
            self.pal.config("rank_defense", int(self.rank_defense_entry.get()))
            self.modified = True
        if int(self.rank_craft_speed_entry.get()) != self.pal.rank_craft_speed:
            self.pal.config("rank_craft_speed", int(self.rank_craft_speed_entry.get()))
            self.modified = True
        if (
            int(self.level_entry.get()) != self.pal.level
            and int(self.exp_stringvar.get()) != self.pal.exp
        ):
            self.pal.config("exp", int(self.exp_stringvar.get()))
            self.modified = True
        if self.is_rare_pal_boolvar.get() != self.pal.is_rare_pal:
            self.pal.config("is_rare_pal", self.is_rare_pal_boolvar.get())
            self.modified = True
        if list(self.equip_waza_listvar.get()) != self.pal.equip_waza:
            self.pal.config("equip_waza", list(self.equip_waza_listvar.get()))
            self.modified = True
        if list(self.mastered_waza_listvar.get()) != self.pal.mastered_waza:
            self.pal.config("mastered_waza", list(self.mastered_waza_listvar.get()))
            self.modified = True
        if int(self.talent_hp_entry.get()) != self.pal.talent_hp:
            self.pal.config("talent_hp", int(self.talent_hp_entry.get()))
            self.modified = True
        if int(self.talent_melee_entry.get()) != self.pal.talent_melee:
            self.pal.config("talent_melee", int(self.talent_melee_entry.get()))
            self.modified = True
        if int(self.talent_shot_entry.get()) != self.pal.talent_shot:
            self.pal.config("talent_shot", int(self.talent_shot_entry.get()))
            self.modified = True
        if int(self.talent_defense_entry.get()) != self.pal.talent_defense:
            self.pal.config("talent_defense", int(self.talent_defense_entry.get()))
            self.modified = True
        if list(self.passive_skill_list_listvar.get()) != self.pal.passive_skill_list:
            self.pal.config(
                "passive_skill_list", list(self.passive_skill_list_listvar.get())
            )
            self.modified = True
        self.destroy()

        if not self.modified:
            return
        # 更新父窗口的数据
        self.parent.pal_list.delete(*self.parent.pal_list.get_children())
        pal_map = {k: v for k, v in self.parent.pal_map.items()}
        self.parent.pal_map.clear()
        for pal in pal_map.values():
            row_id = self.parent.pal_list.insert("", "end", values=pal.values)
            self.parent.pal_map[row_id] = pal

    def destroy(self) -> None:
        self.parent.focus_set()
        return super().destroy()


class WazaEditWindow(tk.Toplevel):
    def __init__(
        self, parent: PalEditWindow, variable: tk.Variable, is_equip_waza: bool = False
    ):
        super().__init__(parent)
        self.parent = parent
        self.listvar = variable
        self.is_equip_waza = is_equip_waza
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(
            self.l10n.get(
                "Edit Equip Waza" if self.is_equip_waza else "Edit Mastered Waza"
            )
        )
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.frame_top = ttk.Frame(self)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        self.frame_left = ttk.Frame(self.frame_top)
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.waza_list_frame = ttk.Frame(self.frame_left)
        self.waza_list_frame.pack(fill=tk.BOTH, expand=True)

        self.waza_list_listvar = tk.Variable(value=self.listvar.get())
        self.waza_list_listbox = tk.Listbox(
            self.waza_list_frame, listvariable=self.waza_list_listvar
        )
        self.waza_list_listbox.pack(fill=tk.BOTH, expand=True)
        self.waza_list_listbox.bind("<Button-3>", self.on_right_click_waza_list)

        self.frame_right = ttk.Frame(self.frame_top)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)

        self.insert_button = ttk.Button(
            self.frame_right, text="+", command=self.insert, width=4
        )
        self.insert_button.pack(fill=tk.Y, expand=True)

        self.move_up_button = ttk.Button(
            self.frame_right, text="↑", command=self.move_up, width=4
        )
        self.move_up_button.pack(fill=tk.Y, expand=True)

        self.move_down_button = ttk.Button(
            self.frame_right, text="↓", command=self.move_down, width=4
        )
        self.move_down_button.pack(fill=tk.Y, expand=True)

        self.remove_frame = ttk.Frame(self)
        self.remove_frame.pack(fill=tk.BOTH, expand=True)

        self.remove_selected_button = ttk.Button(
            self.remove_frame,
            text=self.l10n.get("Remove Selected"),
            command=self.remove,
        )
        self.remove_selected_button.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.remove_all_button = ttk.Button(
            self.remove_frame, text=self.l10n.get("Remove All"), command=self.remove_all
        )
        self.remove_all_button.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self, text=self.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def on_right_click_waza_list(self, event):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            selected = (-1,)
        selected = selected[0]
        print(
            "Current select:",
            self.waza_list_listbox.get(selected) or None,
            ", Cursor point at:",
            self.waza_list_listbox.get(self.waza_list_listbox.nearest(event.y)),
        )

    def insert(self):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            selected = (-1,)
        selected = selected[0]
        l = list(self.waza_list_listvar.get())
        if self.is_equip_waza and len(l) == 3:
            messagebox.showinfo(
                self.l10n.get("Info"),
                self.l10n.get("Equip Waza cannot have more than 3."),
                parent=self,
            )
            self.focus_set()
            return
        # waza_id = simpledialog.askstring(
        #     self.l10n.get("Waza ID"),
        #     self.l10n.get("Enter Waza ID"),
        #     initialvalue="EPalWazaID::",
        #     parent=self
        # )
        # if not waza_id:
        #     return
        # if not waza_id in ACTION_SKILLS:
        #     messagebox.showerror(
        #         self.l10n.get("Error"),
        #         self.l10n.get("Waza ID is invalid."),
        #         parent=self
        #     )
        #     self.focus_set()
        #     return
        # if waza_id in l:
        #     messagebox.showerror(
        #         self.l10n.get("Error"),
        #         self.l10n.get("Duplicate Waza ID is not allowed."),
        #         parent=self
        #     )
        #     self.focus_set()
        #     return
        # l.insert(selected, waza_id)
        # self.waza_list_listvar.set(l)
        waza_select_window = WazaSelectWindow(self)
        waza_select_window.grab_set()

    def move_up(self):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.waza_list_listvar.get())
        if selected == 0:
            return
        l[selected], l[selected - 1] = l[selected - 1], l[selected]
        self.waza_list_listvar.set(l)
        self.waza_list_listbox.selection_clear(0, "end")
        self.waza_list_listbox.selection_set(selected - 1, selected - 1)

    def move_down(self):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.waza_list_listvar.get())
        if selected == len(l) - 1:
            return
        l[selected], l[selected + 1] = l[selected + 1], l[selected]
        self.waza_list_listvar.set(l)
        self.waza_list_listbox.selection_clear(0, "end")
        self.waza_list_listbox.selection_set(selected + 1, selected + 1)

    def remove(self):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.waza_list_listvar.get())
        if self.is_equip_waza and len(l) == 1:
            return
        l.pop(selected)
        self.waza_list_listvar.set(l)

    def remove_all(self):
        l = [self.waza_list_listvar.get()[0]] if self.is_equip_waza else []
        self.waza_list_listvar.set(l)

    def save(self):
        if self.listvar.get() == self.waza_list_listvar.get():
            self.destroy()
            return
        self.listvar.set(self.waza_list_listvar.get())
        self.parent.modified = True
        if self.is_equip_waza:
            self.parent.equip_waza_modified_stringvar.set(self.l10n.get("Modified"))
        else:
            self.parent.mastered_waza_modified_stringvar.set(self.l10n.get("Modified"))
        self.destroy()

    def destroy(self) -> None:
        self.parent.focus_set()
        return super().destroy()


class WazaSelectWindow(tk.Toplevel):
    def __init__(self, parent: WazaEditWindow):
        super().__init__(parent)
        self.parent = parent
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Select Waza"))
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.focus_set()

    def create_widgets(self):
        self.waza_list_frame = ttk.Frame(self)
        self.waza_list_frame.pack(fill=tk.BOTH, expand=True)

        self.waza_list_listbox = tk.Listbox(
            self.waza_list_frame, yscrollcommand=self.update_waza_list_scrollbar
        )
        self.waza_list_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for waza in sorted(list(KV_WAZA[self.l10n.get_locale()])):
            self.waza_list_listbox.insert(tk.END, waza)

        self.waza_list_scrollbar = ttk.Scrollbar(
            self.waza_list_frame, command=self.waza_list_listbox.yview
        )
        self.waza_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.confirm_button = ttk.Button(
            self, text=self.l10n.get("Confirm"), command=self.confirm
        )
        self.confirm_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def update_waza_list_scrollbar(self, first, last):
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            self.waza_list_scrollbar.pack_forget()
        else:
            self.waza_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.waza_list_scrollbar.set(first, last)

    def confirm(self):
        selected = self.waza_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        waza_id = KV_WAZA[self.l10n.get_locale()][self.waza_list_listbox.get(selected)]
        l = list(self.parent.waza_list_listvar.get())
        if waza_id in l:
            messagebox.showerror(
                self.l10n.get("Error"),
                self.l10n.get("Duplicate Waza ID is not allowed."),
                parent=self,
            )
            self.focus_set()
            return
        l.insert(selected, waza_id)
        self.parent.waza_list_listvar.set(l)
        self.destroy()


class PassiveSkillListEditWindow(tk.Toplevel):
    def __init__(self, parent: PalEditWindow, variable: tk.Variable):
        super().__init__(parent)
        self.parent = parent
        self.listvar = variable
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Edit Passive Skills"))
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.frame_top = ttk.Frame(self)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        self.frame_left = ttk.Frame(self.frame_top)
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.passive_skill_list_frame = ttk.Frame(self.frame_left)
        self.passive_skill_list_frame.pack(fill=tk.BOTH, expand=True)

        self.passive_skill_list_listvar = tk.Variable(value=self.listvar.get())
        self.passive_skill_list_listbox = tk.Listbox(
            self.passive_skill_list_frame, listvariable=self.passive_skill_list_listvar
        )
        self.passive_skill_list_listbox.pack(fill=tk.BOTH, expand=True)
        self.passive_skill_list_listbox.bind(
            "<Button-3>", self.on_right_click_passive_skill_list
        )

        self.frame_right = ttk.Frame(self.frame_top)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)

        self.insert_button = ttk.Button(
            self.frame_right, text="+", command=self.insert, width=4
        )
        self.insert_button.pack(fill=tk.Y, expand=True)

        self.move_up_button = ttk.Button(
            self.frame_right, text="↑", command=self.move_up, width=4
        )
        self.move_up_button.pack(fill=tk.Y, expand=True)

        self.move_down_button = ttk.Button(
            self.frame_right, text="↓", command=self.move_down, width=4
        )
        self.move_down_button.pack(fill=tk.Y, expand=True)

        self.remove_frame = ttk.Frame(self)
        self.remove_frame.pack(fill=tk.BOTH, expand=True)

        self.remove_selected_button = ttk.Button(
            self.remove_frame,
            text=self.l10n.get("Remove Selected"),
            command=self.remove,
        )
        self.remove_selected_button.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.remove_all_button = ttk.Button(
            self.remove_frame, text=self.l10n.get("Remove All"), command=self.remove_all
        )
        self.remove_all_button.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self, text=self.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def on_right_click_passive_skill_list(self, event):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            selected = (-1,)
        selected = selected[0]
        print(
            "Current select:",
            self.passive_skill_list_listbox.get(selected) or None,
            ", Cursor point at:",
            self.passive_skill_list_listbox.get(
                self.passive_skill_list_listbox.nearest(event.y)
            ),
        )

    def insert(self):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            selected = (-1,)
        selected = selected[0]
        l = list(self.passive_skill_list_listvar.get())
        if len(l) == 4:
            messagebox.showinfo(
                self.l10n.get("Info"),
                self.l10n.get("Passive Skills cannot have more than 4."),
                parent=self,
            )
            self.focus_set()
            return
        # passive_skill_id = simpledialog.askstring(
        #     self.l10n.get("Passive Skill ID"),
        #     self.l10n.get("Enter Passive Skill ID"),
        #     # initialvalue="EPalPassiveSkillID::",
        #     parent=self
        # )
        # if not passive_skill_id:
        #     return
        # if not passive_skill_id in PASSIVE_SKILLS:
        #     messagebox.showerror(
        #         self.l10n.get("Error"),
        #         self.l10n.get("Passive Skill ID is invalid."),
        #         parent=self
        #     )
        #     self.focus_set()
        #     return
        # if passive_skill_id in l:
        #     messagebox.showerror(
        #         self.l10n.get("Error"),
        #         self.l10n.get("Duplicate Passive Skill ID is not allowed."),
        #         parent=self
        #     )
        #     self.focus_set()
        #     return
        # l.insert(selected, passive_skill_id)
        # self.passive_skill_list_listvar.set(l)
        passive_skill_select_window = PassiveSkillSelectWindow(self)
        passive_skill_select_window.grab_set()

    def move_up(self):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.passive_skill_list_listvar.get())
        if selected == 0:
            return
        l[selected], l[selected - 1] = l[selected - 1], l[selected]
        self.passive_skill_list_listvar.set(l)
        self.passive_skill_list_listbox.selection_clear(0, "end")
        self.passive_skill_list_listbox.selection_set(selected - 1, selected - 1)

    def move_down(self):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.passive_skill_list_listvar.get())
        if selected == len(l) - 1:
            return
        l[selected], l[selected + 1] = l[selected + 1], l[selected]
        self.passive_skill_list_listvar.set(l)
        self.passive_skill_list_listbox.selection_clear(0, "end")
        self.passive_skill_list_listbox.selection_set(selected + 1, selected + 1)

    def remove(self):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        l = list(self.passive_skill_list_listvar.get())
        l.pop(selected)
        self.passive_skill_list_listvar.set(l)

    def remove_all(self):
        self.passive_skill_list_listvar.set([])

    def save(self):
        if self.listvar.get() == self.passive_skill_list_listvar.get():
            self.destroy()
            return
        self.listvar.set(self.passive_skill_list_listvar.get())
        self.parent.modified = True
        self.parent.passive_skill_list_modified_stringvar.set(self.l10n.get("Modified"))
        self.destroy()

    def destroy(self) -> None:
        self.parent.focus_set()
        return super().destroy()


class PassiveSkillSelectWindow(tk.Toplevel):
    def __init__(self, parent: PassiveSkillListEditWindow):
        super().__init__(parent)
        self.parent = parent
        self.l10n = parent.l10n
        self.recommended_ipadx = parent.recommended_ipadx
        self.recommended_ipady = parent.recommended_ipady
        self.title(self.l10n.get("Select Passive Skill"))
        self.minsize(300, 200)
        self.resizable(False, False)
        self.create_widgets()
        self.focus_set()

    def create_widgets(self):
        self.passive_skill_list_frame = ttk.Frame(self)
        self.passive_skill_list_frame.pack(fill=tk.BOTH, expand=True)

        self.passive_skill_list_listbox = tk.Listbox(
            self.passive_skill_list_frame,
            yscrollcommand=self.update_passive_skill_list_scrollbar,
        )
        self.passive_skill_list_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for passive_skill in sorted(list(KV_PASSIVE_SKILL[self.l10n.get_locale()])):
            self.passive_skill_list_listbox.insert(tk.END, passive_skill)

        self.passive_skill_list_scrollbar = ttk.Scrollbar(
            self.passive_skill_list_frame, command=self.passive_skill_list_listbox.yview
        )
        self.passive_skill_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.confirm_button = ttk.Button(
            self, text=self.l10n.get("Confirm"), command=self.confirm
        )
        self.confirm_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

    def update_passive_skill_list_scrollbar(self, first, last):
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            self.passive_skill_list_scrollbar.pack_forget()
        else:
            self.passive_skill_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.passive_skill_list_scrollbar.set(first, last)

    def confirm(self):
        selected = self.passive_skill_list_listbox.curselection()
        if not selected:
            return
        selected = selected[0]
        passive_skill_id = KV_PASSIVE_SKILL[self.l10n.get_locale()][
            self.passive_skill_list_listbox.get(selected)
        ]
        l = list(self.parent.passive_skill_list_listvar.get())
        l.insert(selected, passive_skill_id)
        self.parent.passive_skill_list_listvar.set(l)
        self.destroy()


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Palworld Save Editor")
        self.geometry("800x500")
        self.minsize(800, 500)
        self.base_font_size = 7
        self.recommended_ipadx = self.base_font_size - 2
        self.recommended_ipady = (self.base_font_size - 2) // 2
        self.l10n = L10N()
        self.create_widgets()
        self.on_startup_threading()
        self.apply_locale(startup=True)

    def apply_locale(self, locale: str = None, *, startup: bool = False):
        self.l10n.set_locale(locale)
        FILE_TYPES[0][0] = self.l10n.get("All supported file types")
        FILE_TYPES[1][0] = self.l10n.get("Palworld main save")
        FILE_TYPES[2][0] = self.l10n.get("Palworld main save JSON")
        self.title(self.l10n.get("Palworld Save Editor"))
        self.select_source_button.config(text=self.l10n.get("Choose File"))
        self.save_and_convert_button.config(
            text=self.l10n.get("Save and Convert to SAV")
        )
        self.save_button.config(text=self.l10n.get("Save"))
        self.tab_frame.tab(0, text=self.l10n.get("Guild List"))
        self.tab_frame.tab(1, text=self.l10n.get("Player List"))
        self.tab_frame.tab(2, text=self.l10n.get("Pal List"))
        self.setup_treeviews(startup=startup)
        self.pal_container_label.config(text=self.l10n.get("Filter by Container ID"))
        self.character_id_label.config(text=self.l10n.get("Filter by Character ID"))
        if self.container_id_list.cget("values"):
            self.container_id_list.config(
                values=[self.l10n.get("All")]
                + sorted(list(self.container_id_list.cget("values")[1:]))
            )
            current = self.container_id_list.current()
            current = 0 if current < 0 else current
            self.container_id_list.current(current)
        if self.character_id_list.cget("values"):
            self.character_id_list.config(
                values=[self.l10n.get("All")]
                + sorted(list(self.character_id_list.cget("values")[1:]))
            )
            current = self.character_id_list.current()
            current = 0 if current < 0 else current
            self.character_id_list.current(current)
        self.status_label.config(text=self.l10n.get("Ready"))
        self.tips_label.config(
            text=self.l10n.get("MB1 to select items, MB3 to edit.")
            + self.l10n.get(" Please keep a backup in case of data loss.")
        )

    def on_startup_threading(self):
        threading.Thread(target=self.on_startup).start()

    def on_startup(self):
        self.save_tools_version_label.config(text=asyncio.run(get_submodule_commit()))

    def create_widgets(self):

        # 创建顶栏
        self.top_bar = ttk.Frame(self)
        self.top_bar.pack(fill=tk.X)

        self.select_source_button = ttk.Button(
            self.top_bar, text="选择文件", command=self.select_source_threading
        )
        self.select_source_button.pack(
            side=tk.LEFT, ipadx=self.recommended_ipadx, ipady=self.recommended_ipady
        )

        # 创建文件名显示框
        self.source_filename = tk.StringVar()
        self.source_filename_entry = ttk.Entry(
            self.top_bar, state=tk.DISABLED, textvariable=self.source_filename
        )
        self.source_filename_entry.pack(fill=tk.X, ipady=self.recommended_ipady + 2)

        self.save_and_convert_button = ttk.Button(
            self.top_bar,
            text="保存并转换为 SAV 文件",
            state=tk.DISABLED,
            command=self.save_and_convert_threading,
        )
        self.save_and_convert_button.pack(
            side=tk.RIGHT,
            before=self.source_filename_entry,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self.top_bar,
            text="保存",
            width=4,
            state=tk.DISABLED,
            command=self.save_threading,
        )
        self.save_button.pack(
            side=tk.RIGHT,
            before=self.source_filename_entry,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        # 创建标签页框架
        self.tab_frame = ttk.Notebook(self)
        self.tab_frame.pack(fill=tk.BOTH, expand=True)

        # 创建样式
        style = ttk.Style()
        style.configure(
            "TNotebook.Tab", padding=[self.recommended_ipadx, self.recommended_ipady]
        )

        # 创建公会列表标签页
        self.guild_list_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.guild_list_tab, text="公会列表")

        self.guild_list = ttk.Treeview(
            self.guild_list_tab,
            show="headings",
            yscrollcommand=self.update_guild_list_scrollbar,
        )
        self.setup_guild_list(startup=True)
        self.guild_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.guild_list_scrollbar = ttk.Scrollbar(
            self.guild_list_tab, orient=tk.VERTICAL, command=self.guild_list.yview
        )
        self.guild_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建玩家列表标签页
        self.player_list_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.player_list_tab, text="玩家列表")

        self.player_list = ttk.Treeview(
            self.player_list_tab,
            show="headings",
            yscrollcommand=self.update_player_list_scrollbar,
        )
        self.setup_player_list(startup=True)
        self.player_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.player_list_scrollbar = ttk.Scrollbar(
            self.player_list_tab, orient=tk.VERTICAL, command=self.player_list.yview
        )
        self.player_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建帕鲁列表标签页
        self.pal_list_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.pal_list_tab, text="帕鲁列表")

        self.pal_list_filter_frame = ttk.Frame(self.pal_list_tab)
        self.pal_list_filter_frame.pack(side=tk.TOP, fill=tk.X)

        self.pal_container_label = ttk.Label(
            self.pal_list_filter_frame, text="按容器 ID 筛选"
        )
        self.pal_container_label.pack(
            side=tk.LEFT, padx=self.recommended_ipadx, pady=self.recommended_ipady
        )

        self.container_id_list = ttk.Combobox(
            self.pal_list_filter_frame, justify=tk.CENTER
        )
        self.container_id_list.bind(
            "<<ComboboxSelected>>", lambda _: self.filter_pal_list()
        )
        self.container_id_list.bind("<Return>", lambda _: self.filter_pal_list())
        self.container_id_list.pack(
            side=tk.LEFT,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            expand=True,
        )

        self.character_id_label = ttk.Label(
            self.pal_list_filter_frame, text="按帕鲁 ID 筛选"
        )
        self.character_id_label.pack(
            side=tk.LEFT, padx=self.recommended_ipadx, pady=self.recommended_ipady
        )

        self.character_id_list = ttk.Combobox(
            self.pal_list_filter_frame, justify=tk.CENTER
        )
        self.character_id_list.bind(
            "<<ComboboxSelected>>", lambda _: self.filter_pal_list()
        )
        self.character_id_list.bind("<Return>", lambda _: self.filter_pal_list())
        self.character_id_list.pack(
            side=tk.LEFT,
            fill=tk.X,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
            expand=True,
        )

        self.pal_list = ttk.Treeview(
            self.pal_list_tab,
            show="headings",
            yscrollcommand=self.update_pal_list_scrollbar,
        )
        self.setup_pal_list(startup=True)
        self.pal_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.pal_list_scrollbar = ttk.Scrollbar(
            self.pal_list_tab, orient=tk.VERTICAL, command=self.pal_list.yview
        )
        self.pal_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建状态栏
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_bar = ttk.Progressbar(self.status_bar, mode="determinate")
        self.progress_bar.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        self.status_label = ttk.Label(self.status_bar, text="准备就绪")
        self.status_label.pack(
            fill=tk.X,
            side=tk.LEFT,
            padx=self.recommended_ipadx,
            pady=self.recommended_ipady,
        )

        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(fill=tk.Y, side=tk.LEFT)

        self.tips_label = ttk.Label(
            self.status_bar,
            text="左键选取列表项，右键编辑。请注意保留备份，以防数据丢失。",
        )
        self.tips_label.pack(
            side=tk.LEFT, padx=self.recommended_ipadx, pady=self.recommended_ipady
        )

        self.l10n_menu_button = ttk.Menubutton(self.status_bar, text="L10N")
        self.l10n_menu = tk.Menu(self.l10n_menu_button, tearoff=False)
        self.l10n_menu_button.config(menu=self.l10n_menu)
        for locale in self.l10n.get_locales():
            self.l10n_menu.add_command(
                label=locale, command=lambda locale=locale: self.apply_locale(locale)
            )
        self.l10n_menu_button.pack(
            side=tk.RIGHT, ipadx=self.recommended_ipadx, ipady=self.recommended_ipady
        )

        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(
            fill=tk.Y, side=tk.RIGHT
        )

        self.save_tools_version_label = ttk.Label(self.status_bar)
        self.save_tools_version_label.pack(
            fill=tk.X,
            side=tk.RIGHT,
            padx=self.recommended_ipadx,
            pady=self.recommended_ipady,
        )

        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(
            fill=tk.Y, side=tk.RIGHT
        )

    def setup_guild_list(self, *, startup: bool = False):
        if startup:
            self.guild_list.config(
                columns=("公会 ID", "公会名称", "据点等级", "据点数量", "成员数量")
            )
        if self.l10n.get_locale() == "zh_Hans":
            self.guild_list.column(
                "公会 ID", width=self.base_font_size * 37, stretch=False
            )
            self.guild_list.column(
                "据点等级", width=self.base_font_size * 10, stretch=False
            )
            self.guild_list.column(
                "据点数量", width=self.base_font_size * 10, stretch=False
            )
            self.guild_list.column(
                "成员数量", width=self.base_font_size * 10, stretch=False
            )
        elif self.l10n.get_locale() == "en":
            self.guild_list.column(
                "公会 ID", width=self.base_font_size * 37, stretch=False
            )
            self.guild_list.column(
                "据点等级", width=self.base_font_size * 16, stretch=False
            )
            self.guild_list.column(
                "据点数量", width=self.base_font_size * 17, stretch=False
            )
            self.guild_list.column(
                "成员数量", width=self.base_font_size * 15, stretch=False
            )
        self.guild_list.heading("公会 ID", text=self.l10n.get("Guild ID"))
        self.guild_list.heading("公会名称", text=self.l10n.get("Guild Name"))
        self.guild_list.heading("据点等级", text=self.l10n.get("Base Camp Level"))
        self.guild_list.heading("据点数量", text=self.l10n.get("Base Camp Count"))
        self.guild_list.heading("成员数量", text=self.l10n.get("Member Count"))
        # for i in range(len(self.guild_list.cget("columns"))):
        for i in [0, 2, 3, 4]:
            self.guild_list.bind(self.sort_by(self.guild_list, i, True))
        self.guild_list.bind("<Button-3>", self.on_guild_list_right_click)

    def on_guild_list_right_click(self, event):
        guild = self.get_selected_guild()
        if not guild:
            return
        self.guild_edit_window = GuildEditWindow(self, guild)
        self.guild_edit_window.grab_set()

    def get_selected_guild(self):
        item = self.guild_list.focus()
        if not item:
            return
        return self.guild_map[item]

    def setup_player_list(self, *, startup: bool = False):
        if startup:
            self.player_list.config(
                columns=(
                    "公会 ID",
                    "公会名称",
                    "玩家 UID",
                    "昵称",
                    "等级",
                    "经验值",
                    "最后在线",
                )
            )
        if self.l10n.get_locale() == "zh_Hans":
            self.player_list.column(
                "公会 ID", width=self.base_font_size * 10, stretch=False
            )
            self.player_list.column(
                "公会名称", width=self.base_font_size * 12, stretch=False
            )
            self.player_list.column(
                "玩家 UID", width=self.base_font_size * 37, stretch=False
            )
            self.player_list.column(
                "等级", width=self.base_font_size * 7, stretch=False
            )
            self.player_list.column(
                "经验值", width=self.base_font_size * 10, stretch=False
            )
            self.player_list.column(
                "最后在线", width=self.base_font_size * 19, stretch=False
            )
        elif self.l10n.get_locale() == "en":
            self.player_list.column(
                "公会 ID", width=self.base_font_size * 10, stretch=False
            )
            self.player_list.column(
                "公会名称", width=self.base_font_size * 12, stretch=False
            )
            self.player_list.column(
                "玩家 UID", width=self.base_font_size * 37, stretch=False
            )
            self.player_list.column(
                "等级", width=self.base_font_size * 7, stretch=False
            )
            self.player_list.column(
                "经验值", width=self.base_font_size * 10, stretch=False
            )
            self.player_list.column(
                "最后在线", width=self.base_font_size * 19, stretch=False
            )
        self.player_list.heading("公会 ID", text=self.l10n.get("Guild ID"))
        self.player_list.heading("公会名称", text=self.l10n.get("Guild Name"))
        self.player_list.heading("玩家 UID", text=self.l10n.get("Player UID"))
        self.player_list.heading("昵称", text=self.l10n.get("Nickname"))
        self.player_list.heading("等级", text=self.l10n.get("Level"))
        self.player_list.heading("经验值", text=self.l10n.get("Exp"))
        self.player_list.heading("最后在线", text=self.l10n.get("Last Online"))
        # for i in range(len(self.player_list.cget("columns"))):
        for i in [0, 2, 4, 5, 6]:
            self.player_list.bind(self.sort_by(self.player_list, i, True))
        self.player_list.bind("<Button-3>", self.on_player_list_right_click)

    def on_player_list_right_click(self, event):
        player = self.get_selected_player()
        if not player:
            return
        self.player_edit_window = PlayerEditWindow(self, player)
        self.player_edit_window.grab_set()

    def get_selected_player(self):
        item = self.player_list.focus()
        if not item:
            return
        return self.player_map[item]

    def setup_pal_list(self, *, startup: bool = False):
        if startup:
            self.pal_list.config(
                columns=(
                    "帕鲁 ID",
                    "性别",
                    "等级",
                    "经验值",
                    "HP 个体值",
                    "近战攻击 个体值",
                    "远程攻击 个体值",
                    "防御力 个体值",
                    "被动技能",
                    # "HP",
                    # "SAN 值"
                )
            )
        self.pal_list.column("帕鲁 ID", width=self.base_font_size * 14, stretch=False)
        self.pal_list.column("性别", width=self.base_font_size * 8, stretch=False)
        self.pal_list.column("等级", width=self.base_font_size * 7, stretch=False)
        self.pal_list.column("经验值", width=self.base_font_size * 9, stretch=False)
        self.pal_list.column("HP 个体值", width=self.base_font_size * 10, stretch=False)
        self.pal_list.column(
            "近战攻击 个体值", width=self.base_font_size * 13, stretch=False
        )
        self.pal_list.column(
            "远程攻击 个体值", width=self.base_font_size * 11, stretch=False
        )
        self.pal_list.column(
            "防御力 个体值", width=self.base_font_size * 14, stretch=False
        )
        self.pal_list.column("被动技能", width=self.base_font_size * 9)
        self.pal_list.heading("帕鲁 ID", text=self.l10n.get("Character ID"))
        self.pal_list.heading("性别", text=self.l10n.get("Gender"))
        self.pal_list.heading("等级", text=self.l10n.get("Level"))
        self.pal_list.heading("经验值", text=self.l10n.get("Exp"))
        self.pal_list.heading("HP 个体值", text=self.l10n.get("Talent: HP"))
        self.pal_list.heading("近战攻击 个体值", text=self.l10n.get("Talent: Melee"))
        self.pal_list.heading("远程攻击 个体值", text=self.l10n.get("Talent: Shot"))
        self.pal_list.heading("防御力 个体值", text=self.l10n.get("Talent: Defense"))
        self.pal_list.heading("被动技能", text=self.l10n.get("Passive Skills"))
        # self.pal_list.heading("HP", text="HP")
        # self.pal_list.heading("SAN 值", text="SAN 值")
        # for i in range(len(self.pal_list.cget("columns"))):
        for i in [0, 2, 3, 7, 6, 5, 4]:
            self.pal_list.bind(self.sort_by(self.pal_list, i, True))
        self.pal_list.bind("<Button-3>", self.on_pal_list_right_click)

    def on_pal_list_right_click(self, event):
        pal = self.get_selected_pal()
        if not pal:
            return
        self.pal_edit_window = PalEditWindow(self, pal)
        self.pal_edit_window.grab_set()

    def get_selected_pal(self):
        item = self.pal_list.focus()
        if not item:
            return
        return self.pal_map[item]

    def setup_treeviews(self, *, startup: bool = False):
        self.setup_guild_list(startup=startup)
        self.setup_player_list(startup=startup)
        self.setup_pal_list(startup=startup)

    def sort_by(self, tv: ttk.Treeview, col, descending):
        data = [(tv.set(child, col), child) for child in tv.get_children("")]
        data.sort(
            reverse=descending, key=lambda x: int(x[0]) if x[0].isdigit() else x[0]
        )
        for ix, item in enumerate(data):
            tv.move(item[1], "", ix)
        tv.heading(
            col, command=lambda col=col: self.sort_by(tv, col, int(not descending))
        )

    def update_guild_list_scrollbar(self, first, last):
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            self.guild_list_scrollbar.pack_forget()
        else:
            self.guild_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.guild_list_scrollbar.set(first, last)

    def update_player_list_scrollbar(self, first, last):
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            self.player_list_scrollbar.pack_forget()
        else:
            self.player_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.player_list_scrollbar.set(first, last)

    def update_pal_list_scrollbar(self, first, last):
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            self.pal_list_scrollbar.pack_forget()
        else:
            self.pal_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.pal_list_scrollbar.set(first, last)

    def filter_pal_list(self):
        container_id = self.container_id_list.get()
        character_id = self.character_id_list.get()
        container_id = None if container_id == self.l10n.get("All") else container_id
        character_id = None if character_id == self.l10n.get("All") else character_id
        self.pal_list.delete(*self.pal_list.get_children())
        # pal_map = {k: v for k, v in self.pal_map.items()}
        self.pal_map.clear()
        if (
            container_id in self.kv_container_id
            and character_id in self.kv_character_id
        ):
            for pal in self.kv_container_id[container_id]:
                if pal.character_id == character_id:
                    row_id = self.pal_list.insert("", 0, values=pal.values)
                    self.pal_map[row_id] = pal
        elif container_id in self.kv_container_id:
            for pal in self.kv_container_id[container_id]:
                row_id = self.pal_list.insert("", 0, values=pal.values)
                self.pal_map[row_id] = pal
        elif character_id in self.kv_character_id:
            for pal in self.kv_character_id[character_id]:
                row_id = self.pal_list.insert("", 0, values=pal.values)
                self.pal_map[row_id] = pal
        else:
            for item in self.kv_container_id:
                for pal in self.kv_container_id[item]:
                    row_id = self.pal_list.insert("", 0, values=pal.values)
                    self.pal_map[row_id] = pal

    def update_source_filename(self, filename: str = ""):
        self.source_filename.set(filename)
        self.source_filename_entry.update()

    def switch_state(self, state):
        self.select_source_button.config(state=state)
        self.save_and_convert_button.config(state=state)
        self.save_button.config(state=state)
        self.tab_frame.tab(self.player_list_tab, state=state)
        self.tab_frame.tab(self.pal_list_tab, state=state)

    def switch_state_to_normal(self):
        self.switch_state(tk.NORMAL)
        self.status_label.config(text=self.l10n.get("Ready"))

    def switch_state_to_disabled(self):
        self.switch_state(tk.DISABLED)
        self.status_label.config(text=self.l10n.get("Processing"))

    def switch_state_decorator(func):
        def wrapper(self: Application, *args, **kwargs):
            self.switch_state_to_disabled()
            try:
                func(self, *args, **kwargs)
            except:
                self.switch_state_to_normal()
                raise
            self.switch_state_to_normal()

        return wrapper

    def clean_all(self):
        if hasattr(self, "data"):
            del self.data
        self.guild_list.delete(*self.guild_list.get_children())
        self.player_list.delete(*self.player_list.get_children())
        if hasattr(self, "kv_container_id"):
            del self.kv_container_id
        self.container_id_list.config(values=[])
        self.pal_list.delete(*self.pal_list.get_children())
        if hasattr(self, "kv_character_id"):
            del self.kv_character_id
        self.character_id_list.config(values=[])
        if hasattr(self, "guild_map"):
            del self.guild_map
        if hasattr(self, "player_map"):
            del self.player_map
        if hasattr(self, "pal_map"):
            del self.pal_map

        # 离开帕鲁列表标签页，不然加载速度会很慢
        # if self.tab_frame.index("current") == self.tab_frame.index(self.pal_list_tab):
        #     self.tab_frame.select(self.player_list_tab)
        self.progress(0)

    def progress(self, value):
        self.progress_bar.config(value=value)

    def select_source_threading(self):
        threading.Thread(target=self.select_source).start()

    @switch_state_decorator
    def select_source(self):
        filename = filedialog.askopenfilename(
            title=self.l10n.get("Choose Palworld main save"), filetypes=FILE_TYPES
        )
        if not filename:
            return
        self.update_source_filename(filename)
        self.file_path = Path(self.source_filename.get())
        if not self.file_path.exists():
            messagebox.showerror(
                self.l10n.get("Error"), self.l10n.get("File not exists.")
            )
            return
        self.clean_all()
        self.progress(1)
        if self.file_path.suffix == ".sav":
            self.data = convert_sav_to_dict(self.file_path)
        elif self.file_path.suffix == ".json":
            self.data = json.loads(self.file_path.read_text(encoding="utf-8"))
        self.progress(2)
        # print(find_value_path(self.data, "无名公会"))
        # print(find_value_path(self.data, "Unnamed Guild"))
        self.world_save_data = self.data["properties"]["worldSaveData"]["value"]
        self.real_date_time_ticks = self.world_save_data["GameTimeSaveData"]["value"][
            "RealDateTimeTicks"
        ]["value"]
        self.guild_map: dict[str, Guild] = {}
        self.player_map: dict[str, Player] = {}
        self.pal_map: dict[str, Pal] = {}
        for i in self.world_save_data["GroupSaveDataMap"]["value"]:
            group_data: dict = i["value"]["RawData"]["value"]
            print(group_data.keys())
            if not group_data.get("base_camp_level"):
                print(
                    "Warning: Unknown data structure for group_id:",
                    f"{group_data['group_id']}, skipping",
                )
                continue
            guild = Guild(group_data)
            row_id = self.guild_list.insert("", "end", values=guild.values)
            self.guild_map[row_id] = guild
            self.progress(3)
            for player in group_data.get("players", []):
                print(player)
                keys = find_value_path(
                    self.world_save_data["CharacterSaveParameterMap"],
                    player["player_info"]["player_name"],
                )
                character_data = {
                    k: v
                    for k, v in self.world_save_data[
                        "CharacterSaveParameterMap"
                    ].items()
                }
                for k in keys[:-2]:
                    character_data = character_data[k]
                # print(character_data.keys())
                # print(character_data["NickName"]["value"])
                player_uid = player["player_uid"]
                last_online_real_time = self.strtime(
                    player["player_info"]["last_online_real_time"]
                )
                player = Player(
                    character_data, guild, player_uid, last_online_real_time
                )
                row_id = self.player_list.insert("", "end", values=player.values)
                self.player_map[row_id] = player
            self.progress(4)
        self.sort_by(self.player_list, 6, True)
        self.character_save_parameter_map = self.world_save_data[
            "CharacterSaveParameterMap"
        ]["value"]
        len_ = len(self.character_save_parameter_map)
        count = 0
        self.kv_container_id: dict[str, Pal] = {}
        self.kv_character_id: dict[str, Pal] = {}
        for i in self.character_save_parameter_map:
            instance_id = i["key"]["InstanceId"]["value"]
            character_data: dict = i["value"]["RawData"]["value"]["object"][
                "SaveParameter"
            ]["value"]
            # print(character_data)
            if not character_data.get("CharacterID"):
                if (
                    character_data["IsPlayer"]["value"]
                    if character_data.get("IsPlayer")
                    else False
                ):
                    continue
                print(
                    "Warning: Unknown data structure for character_id:",
                    f"{character_data['CharacterID']}, skipping",
                )
            pal = Pal(instance_id, character_data)
            row_id = self.pal_list.insert("", 0, values=pal.values)
            self.pal_map[row_id] = pal
            container_id = pal.slot_id
            if not self.kv_container_id.get(container_id):
                self.kv_container_id[container_id] = []
            self.kv_container_id[container_id].append(pal)
            character_id = pal.character_id
            if not self.kv_character_id.get(character_id):
                self.kv_character_id[character_id] = []
            self.kv_character_id[character_id].append(pal)
            count += 1
            self.progress(4 + (count / len_) * 96)
        self.container_id_list.config(
            values=[self.l10n.get("All")] + sorted(list(self.kv_container_id))
        )
        self.character_id_list.config(
            values=[self.l10n.get("All")] + sorted(list(self.kv_character_id))
        )
        self.container_id_list.current(0)
        self.character_id_list.current(0)
        self.progress(100)

    def strtime(self, ticks: int):
        timestamp = (
            self.file_path.stat().st_mtime + (ticks - self.real_date_time_ticks) / 1e7
        )
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def save_threading(self):
        threading.Thread(target=self.save).start()

    @switch_state_decorator
    def save(self, filename: str = "", *, silent: bool = False):
        filename = filename or filedialog.asksaveasfilename(
            title=self.l10n.get("Save as JSON"),
            filetypes=[FILE_TYPES[2]],
            defaultextension=FILE_TYPES[2][1],
            initialfile=self.file_path.stem,
        )
        if not filename:
            return
        if not filename.endswith(".json"):
            filename += ".json"
        if not silent:
            self.progress(1)
        Path(filename).write_text(
            json.dumps(self.data, ensure_ascii=False, indent="\t"), encoding="utf-8"
        )
        if not silent:
            self.progress(100)
            messagebox.showinfo(
                self.l10n.get("Save as JSON"), self.l10n.get("Save successfully.")
            )

    def save_and_convert_threading(self):
        threading.Thread(target=self.save_and_convert).start()

    @switch_state_decorator
    def save_and_convert(self):
        filename = filedialog.asksaveasfilename(
            title=self.l10n.get("Save and Convert to SAV"),
            filetypes=[FILE_TYPES[1]],
            defaultextension=FILE_TYPES[1][1],
            initialfile=self.file_path.stem,
        )
        if not filename:
            return
        self.progress(1)
        self.save(filename, silent=True)
        self.progress(50)
        self.switch_state_to_disabled()
        convert_dict_to_sav(self.data, Path(filename))
        self.progress(100)
        messagebox.showinfo(
            self.l10n.get("Save and Convert to SAV"),
            self.l10n.get("Save successfully."),
        )


def get_gender(character_data: dict):
    if not character_data.get("Gender"):
        return ""
    gender_data = character_data["Gender"]["value"]
    if gender_data["value"] == "EPalGenderType::Male":
        return "Male"
    elif gender_data["value"] == "EPalGenderType::Female":
        return "Female"
    else:
        return gender_data["value"]


def find_value_path(nested_dict: dict, target_value, path=None):
    if path is None:
        path = []
    for key, value in nested_dict.items():
        new_path = path + [key]
        if value == target_value:
            return new_path
        elif isinstance(value, dict):
            result_path = find_value_path(value, target_value, new_path)
            if result_path:
                return result_path
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    result_path = find_value_path(
                        item, target_value, new_path + [index]
                    )
                    if result_path:
                        return result_path


if __name__ == "__main__":
    app = Application()
    app.mainloop()
