from __future__ import annotations

import asyncio
import json
import threading
import tkinter as tk
from pathlib import Path
from sys import modules
from tkinter import filedialog, messagebox, ttk

from save_tools import palworld_save_tools

modules["palworld_save_tools"] = palworld_save_tools
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


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Palworld Save Editor")
        self.geometry("800x500")
        self.minsize(800, 500)
        self.base_font_size = 7
        self.recommended_ipadx = self.base_font_size - 2
        self.recommended_ipady = (self.base_font_size - 2) // 2
        self.create_widgets()
        self.on_startup_threading()

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
            self.top_bar, text="保存并转换为 SAV 文件", state=tk.DISABLED
        )
        self.save_and_convert_button.pack(
            side=tk.RIGHT,
            before=self.source_filename_entry,
            ipadx=self.recommended_ipadx,
            ipady=self.recommended_ipady,
        )

        self.save_button = ttk.Button(
            self.top_bar, text="保存", width=4, state=tk.DISABLED
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
        self.guild_list.config(
            columns=("公会 ID", "公会名称", "据点等级", "据点数量", "成员数量")
        )
        self.guild_list.column("公会 ID", width=self.base_font_size * 37, stretch=False)
        self.guild_list.column(
            "据点等级", width=self.base_font_size * 10, stretch=False
        )
        self.guild_list.column(
            "据点数量", width=self.base_font_size * 10, stretch=False
        )
        self.guild_list.column(
            "成员数量", width=self.base_font_size * 10, stretch=False
        )
        self.guild_list.heading("公会 ID", text="公会 ID")
        self.guild_list.heading("公会名称", text="公会名称")
        self.guild_list.heading("据点等级", text="据点等级")
        self.guild_list.heading("据点数量", text="据点数量")
        self.guild_list.heading("成员数量", text="成员数量")
        # for i in range(len(self.guild_list["columns"])):
        for i in [0, 2, 3, 4]:
            self.guild_list.bind(self.sort_by(self.guild_list, i, True))
        self.guild_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.guild_list_scrollbar = ttk.Scrollbar(
            self.guild_list_tab, orient=tk.VERTICAL, command=self.guild_list.yview
        )
        self.guild_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

    def update_source_filename(self, filename: str = ""):
        self.source_filename.set(filename)
        self.source_filename_entry.update()

    def switch_state(self, state):
        self.select_source_button.config(state=state)
        # self.save_and_convert_button.config(state=state)
        # self.save_button.config(state=state)

    def switch_state_to_normal(self):
        self.switch_state(tk.NORMAL)
        self.status_label.config(text="准备就绪")

    def switch_state_to_disabled(self):
        self.switch_state(tk.DISABLED)
        self.status_label.config(text="正在处理")

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
        self.progress(0)

    def progress(self, value):
        self.progress_bar.config(value=value)

    def select_source_threading(self):
        threading.Thread(target=self.select_source).start()

    @switch_state_decorator
    def select_source(self):
        filename = filedialog.askopenfilename(
            title="选择 Palworld 主存档", filetypes=FILE_TYPES
        )
        if not filename:
            return
        self.update_source_filename(filename)
        self.file_path = Path(self.source_filename.get())
        if not self.file_path.exists():
            messagebox.showerror("错误", "文件不存在。")
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
        for i in self.world_save_data["GroupSaveDataMap"]["value"]:
            group_data: dict = i["value"]["RawData"]["value"]
            print(group_data.keys())
            if not group_data.get("base_camp_level"):
                print(
                    "Warning: Unknown data structure for group_id:",
                    f"{group_data['group_id']}, skipping",
                )
                continue
            guild_data = {
                "公会 ID": group_data["group_id"],
                "公会名称": group_data.get("guild_name"),
                "据点等级": group_data.get("base_camp_level"),
                "据点数量": len(group_data.get("base_ids", [])),
                "成员数量": len(group_data.get("players", [])),
                "公会会长 ID": group_data.get("admin_player_uid"),
                "group_type": group_data["group_type"],
                "group_name": group_data["group_name"],
                "individual_character_handle_ids": group_data[
                    "individual_character_handle_ids"
                ],
                "org_type": group_data["org_type"],
                "map_object_instance_ids_base_camp_points": group_data[
                    "map_object_instance_ids_base_camp_points"
                ],
            }
            self.guild_list.insert("", "end", values=list(guild_data.values())[0:5])
            self.progress(3)
        self.progress(100)


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
