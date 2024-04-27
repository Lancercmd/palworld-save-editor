from __future__ import annotations

import asyncio
import json
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sys import modules, platform
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
from unpack import DT_PET


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
        self.title(parent.l10n.get("Edit Guild"))
        self.minsize(800, 500)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.group_id_frame = ttk.Frame(self)
        self.group_id_frame.pack(fill=tk.X, expand=True)

        self.group_id_label = ttk.Label(
            self.group_id_frame, text=self.parent.l10n.get("Guild ID")
        )
        self.group_id_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

        self.group_id_stringvar = tk.StringVar(value=self.guild.group_id)
        self.group_id_entry = ttk.Entry(
            self.group_id_frame, textvariable=self.group_id_stringvar, state=tk.DISABLED
        )
        self.group_id_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.guild_name_frame = ttk.Frame(self)
        self.guild_name_frame.pack(fill=tk.X, expand=True)

        self.guild_name_label = ttk.Label(
            self.guild_name_frame, text=self.parent.l10n.get("Guild Name")
        )
        self.guild_name_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

        self.guild_name_stringvar = tk.StringVar(value=self.guild.guild_name)
        self.guild_name_entry = ttk.Entry(
            self.guild_name_frame, textvariable=self.guild_name_stringvar
        )
        self.guild_name_entry.bind("<Return>", lambda _: self.save())
        self.guild_name_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.base_camp_level_frame = ttk.Frame(self)
        self.base_camp_level_frame.pack(fill=tk.X, expand=True)

        self.base_camp_level_label = ttk.Label(
            self.base_camp_level_frame, text=self.parent.l10n.get("Base Camp Level")
        )
        self.base_camp_level_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
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
        )
        self.base_camp_level_entry.bind("<Return>", lambda _: self.save())
        self.base_camp_level_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.parent.recommended_ipadx - 6,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.save_button = ttk.Button(
            self, text=self.parent.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
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
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Guild Name cannot be empty."),
                parent=self,
            )
            return False
        if not self.base_camp_level_entry.get():
            messagebox.showerror(
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Base Camp Level cannot be empty."),
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
        self.title(parent.l10n.get("Edit Player"))
        self.minsize(800, 500)
        self.resizable(False, False)
        self.create_widgets()
        self.modified = False
        self.focus_set()

    def create_widgets(self):
        self.player_uid_frame = ttk.Frame(self)
        self.player_uid_frame.pack(fill=tk.X, expand=True)

        self.player_uid_label = ttk.Label(
            self.player_uid_frame, text=self.parent.l10n.get("Player UID")
        )
        self.player_uid_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

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
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.nickname_frame = ttk.Frame(self)
        self.nickname_frame.pack(fill=tk.X, expand=True)

        self.nickname_label = ttk.Label(
            self.nickname_frame, text=self.parent.l10n.get("Nickname")
        )
        self.nickname_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

        self.nickname_stringvar = tk.StringVar(value=self.player.nickname)
        self.nickname_entry = ttk.Entry(
            self.nickname_frame, textvariable=self.nickname_stringvar
        )
        self.nickname_entry.bind("<Return>", lambda _: self.save())
        self.nickname_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.level_frame = ttk.Frame(self)
        self.level_frame.pack(fill=tk.X, expand=True)

        self.level_label = ttk.Label(
            self.level_frame, text=self.parent.l10n.get("Level")
        )
        self.level_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

        validate_level_input_command = self.register(self.validate_level_input)

        self.level_stringvar = tk.StringVar(value=self.player.level)
        self.level_entry = ttk.Spinbox(
            self.level_frame,
            from_=max(2, self.player.level),
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
            ipadx=self.parent.recommended_ipadx - 6,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.exp_frame = ttk.Frame(self)
        self.exp_frame.pack(fill=tk.X, expand=True)

        self.exp_label = ttk.Label(self.exp_frame, text=self.parent.l10n.get("Exp"))
        self.exp_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            padx=self.parent.recommended_ipadx,
        )

        self.exp_entry_align_button = ttk.Button(
            self.exp_frame,
            text=self.parent.l10n.get("Align"),
            command=self.validate,
            width=6,
        )
        self.exp_entry_align_button.pack(
            side=tk.RIGHT,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
            padx=self.parent.recommended_ipadx,
        )

        self.exp_stringvar = tk.StringVar(value=self.player.exp)
        self.exp_entry = ttk.Entry(
            self.exp_frame, textvariable=self.exp_stringvar, state=tk.DISABLED, width=10
        )
        self.exp_entry.pack(
            side=tk.RIGHT,
            anchor=tk.E,
            fill=tk.X,
            ipadx=self.parent.recommended_ipadx + 4,
            ipady=self.parent.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self, text=self.parent.l10n.get("Save"), command=self.save
        )
        self.save_button.pack(
            fill=tk.BOTH,
            expand=True,
            ipadx=self.parent.recommended_ipadx,
            ipady=self.parent.recommended_ipady,
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
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Nickname cannot be empty."),
                parent=self,
            )
            return False
        if not self.level_entry.get():
            messagebox.showerror(
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Level cannot be empty."),
                parent=self,
            )
            return False
        if not self.level_entry.get().isdigit():
            messagebox.showerror(
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Level must be a number."),
                parent=self,
            )
            return False
        # 等级不能低于当前等级
        if int(self.level_entry.get()) < self.player.level:
            messagebox.showerror(
                self.parent.l10n.get("Error"),
                self.parent.l10n.get("Level cannot be lower than the current."),
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


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Palworld Save Editor")
        self.minsize(1920, 1200)
        self.base_font_size = 24
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

    def on_startup_threading(self):
        threading.Thread(target=self.on_startup).start()

    def on_startup(self):
        # self.state("zoomed")
        self.save_tools_version_label.config(text=asyncio.run(get_submodule_commit()))

    def create_widgets(self):
        # 创建顶栏
        self.top_bar = ttk.Frame(self)
        self.top_bar.pack(fill=tk.X)

        self.select_source_button = ttk.Button(
            self.top_bar, text="选择文件", command=self.select_source_threading
        )
        self.select_source_button.pack(
            side=tk.LEFT,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
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
            "TNotebook.Tab",
            padding=[self.recommended_ipadx, self.recommended_ipady],
        )
        set_treeview_row_height(12 + 2 * 2)
        style.configure("Treeview.Heading", padding=[10, self.recommended_ipady])

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

        self.l10n_menu_button = ttk.Menubutton(self.status_bar, text="L10N")
        self.l10n_menu = tk.Menu(self.l10n_menu_button, tearoff=False)
        self.l10n_menu_button.config(menu=self.l10n_menu)
        for locale in self.l10n.get_locales():
            self.l10n_menu.add_command(
                label=locale,
                command=lambda locale=locale: self.apply_locale(locale),
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
        self.guild_list.config(
            columns=("公会 ID", "公会名称", "据点等级", "据点数量", "成员数量")
        )  # 目的是重置行宽
        if startup:
            self.guild_list.column("公会 ID", width=12 * 36)
            self.guild_list.column("据点等级", stretch=False)
            self.guild_list.column("据点数量", stretch=False)
            self.guild_list.column("成员数量", stretch=False)
        else:
            self.guild_list.column("公会 ID", stretch=True)
            self.guild_list.column("公会名称", stretch=True)
            self.guild_list.column("据点等级", stretch=True)
            self.guild_list.column("据点数量", stretch=True)
            self.guild_list.column("成员数量", stretch=True)
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
        if startup:
            self.player_list.column("公会 ID", stretch=False)
            self.player_list.column("公会名称", stretch=False)
            self.player_list.column("玩家 UID", stretch=False)
            self.player_list.column("等级", stretch=False)
            self.player_list.column("经验值", stretch=False)
            self.player_list.column("最后在线", width=12 * 31, stretch=False)
        else:
            self.player_list.column("公会 ID", stretch=True)
            self.player_list.column("公会名称", stretch=True)
            self.player_list.column("玩家 UID", stretch=True)
            self.player_list.column("昵称", stretch=True)
            self.player_list.column("等级", stretch=True)
            self.player_list.column("经验值", stretch=True)
            self.player_list.column("最后在线", stretch=True)
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
                # "SAN 值",
            )
        )
        self.pal_list.column("帕鲁 ID", stretch=True)
        self.pal_list.column("性别", stretch=True)
        self.pal_list.column("等级", stretch=True)
        self.pal_list.column("经验值", stretch=True)
        self.pal_list.column("HP 个体值", stretch=True)
        self.pal_list.column("近战攻击 个体值", stretch=True)
        self.pal_list.column("远程攻击 个体值", stretch=True)
        self.pal_list.column("防御力 个体值", stretch=True)
        self.pal_list.column("被动技能", stretch=True)
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
        for i in [0, 2, 3, 4, 5, 6, 7]:
            self.pal_list.bind(self.sort_by(self.pal_list, i, True))

    def setup_treeviews(self, *, startup: bool = False):
        self.setup_guild_list(startup=startup)
        self.setup_player_list(startup=startup)
        self.setup_pal_list(startup=startup)

    def sort_by(self, tv: ttk.Treeview, col, descending):
        """Sort tree contents when a column is clicked on."""
        # grab values to sort
        data = [(tv.set(child, col), child) for child in tv.get_children("")]

        # reorder data
        data.sort(
            reverse=descending, key=lambda x: int(x[0]) if x[0].isdigit() else x[0]
        )
        for ix, item in enumerate(data):
            tv.move(item[1], "", ix)

        # switch the heading so that it will sort in the opposite direction
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
        if (
            container_id in self.kv_container_id
            and character_id in self.kv_character_id
        ):
            for pal in self.kv_container_id[container_id]:
                if pal["帕鲁 ID"] == character_id:
                    self.pal_list.insert("", 0, values=list(pal.values())[0:10])
        elif container_id in self.kv_container_id:
            for pal in self.kv_container_id[container_id]:
                self.pal_list.insert("", 0, values=list(pal.values())[0:10])
        elif character_id in self.kv_character_id:
            for pal in self.kv_character_id[character_id]:
                self.pal_list.insert("", 0, values=list(pal.values())[0:10])
        else:
            for pal in self.kv_container_id:
                for item in self.kv_container_id[pal]:
                    self.pal_list.insert("", 0, values=list(item.values())[0:10])

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
        self.kv_container_id = {}
        self.kv_character_id = {}
        for i in self.character_save_parameter_map:
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
            pal_data = {
                "帕鲁 ID": character_data["CharacterID"]["value"],
                "性别": get_gender(character_data),
                "等级": (
                    character_data["Level"]["value"]
                    if character_data.get("Level")
                    else 1
                ),
                "经验值": (
                    character_data["Exp"]["value"] if character_data.get("Exp") else 0
                ),
                "HP 个体值": (
                    character_data["Talent_HP"]["value"]
                    if character_data.get("Talent_HP")
                    else 0
                ),
                "近战攻击 个体值": (
                    character_data["Talent_Melee"]["value"]
                    if character_data.get("Talent_Melee")
                    else 0
                ),
                "远程攻击 个体值": (
                    character_data["Talent_Shot"]["value"]
                    if character_data.get("Talent_Shot")
                    else 0
                ),
                "防御力 个体值": (
                    character_data["Talent_Defense"]["value"]
                    if character_data.get("Talent_Defense")
                    else 0
                ),
                "被动技能": (
                    character_data["PassiveSkillList"]["value"]
                    if character_data.get("PassiveSkillList")
                    else {"values": []}
                ),
                "HP": (
                    character_data["HP"]["value"]["Value"]["value"] // 1000
                    if character_data.get("HP")
                    else 0
                ),
                "SAN 值": (
                    int(character_data["SanityValue"]["value"])
                    if character_data.get("SanityValue")
                    else 100.0
                ),
                "浓缩等级": (
                    character_data["Rank"]["value"] if character_data.get("Rank") else 0
                ),
                "HP 强化等级": (
                    character_data["Rank_HP"]["value"]
                    if character_data.get("Rank_HP")
                    else 0
                ),
                "攻击力 强化等级": (
                    character_data["Rank_Attack"]["value"]
                    if character_data.get("Rank_Attack")
                    else 0
                ),
                "防御力 强化等级": (
                    character_data["Rank_Defence"]["value"]
                    if character_data.get("Rank_Defence")
                    else 0
                ),
                "工作速度 强化等级": (
                    character_data["Rank_CraftSpeed"]["value"]
                    if character_data.get("Rank_CraftSpeed")
                    else 0
                ),
                "已装备的技能": character_data["EquipWaza"]["value"],
                "饱腹度": (
                    character_data["FullStomach"]["value"]
                    if character_data.get("FullStomach")
                    else 0.0
                ),
                "MP": character_data["MP"]["value"] if character_data.get("MP") else 0,
                "历任所有者 ID": character_data["OldOwnerPlayerUIds"]["value"],
                "制作速度": character_data["CraftSpeed"]["value"],
                "各项制作速度": character_data["CraftSpeeds"]["value"],
                "道具容器 ID": (
                    character_data["ItemContainerId"]["value"]
                    if character_data.get("ItemContainerId")
                    else ""
                ),
                "装备容器 ID": character_data["EquipItemContainerId"]["value"],
                "槽位 ID": character_data["SlotID"]["value"],
                "最大饱腹度": (
                    character_data["MaxFullStomach"]["value"]
                    if character_data.get("MaxFullStomach")
                    else 0.0
                ),
                "已使用的状态点数": (
                    character_data["GotStatusPointList"]["value"]["values"]
                    if character_data.get("GotStatusPointList")
                    else []
                ),
                "已使用的附加状态点数": (
                    character_data["GotExStatusPointList"]["value"]["values"]
                    if character_data.get("GotExStatusPointList")
                    else []
                ),
                "饱腹度下降率": (
                    character_data["DecreaseFullStomachRates"]["value"]
                    if character_data.get("DecreaseFullStomachRates")
                    else 1.0
                ),
                "SAN 值变化率": (
                    character_data["AffectSanityRates"]["value"]
                    if character_data.get("AffectSanityRates")
                    else 1.0
                ),
                "制作速度倍率": (
                    character_data["CraftSpeedRates"]["value"]
                    if character_data.get("CraftSpeedRates")
                    else 1.0
                ),
                "最近传送位置": (
                    character_data["LastJumpedLocation"]["value"]
                    if character_data.get("LastJumpedLocation")
                    else {"x": 0.0, "y": 0.0, "z": 0.0}
                ),
            }
            self.pal_list.insert("", 0, values=list(pal_data.values())[0:10])
            container_id = character_data["SlotID"]["value"]["ContainerId"]["value"][
                "ID"
            ]["value"]
            if not self.kv_container_id.get(container_id):
                self.kv_container_id[container_id] = []
            self.kv_container_id[container_id].append(pal_data)
            character_id = character_data["CharacterID"]["value"]
            if not self.kv_character_id.get(character_id):
                self.kv_character_id[character_id] = []
            self.kv_character_id[character_id].append(pal_data)
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


def get_scale_factor():
    # 获取系统的 DPI 缩放比例
    dpi = windll.user32.GetDpiForSystem()
    scale_factor = dpi / 96.0  # 默认 DPI 是 96
    return scale_factor


def set_treeview_row_height(base_height):
    if platform != "win32":
        return
    # 根据 DPI 缩放比例设置 Treeview 的行高
    scale_factor = get_scale_factor()
    new_height = int(base_height * scale_factor)
    style = ttk.Style()
    style.configure("Treeview", rowheight=new_height)


if platform == "win32":
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
