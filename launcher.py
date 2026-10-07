"""Windows startup administration UI. No A behavior, inference or runtime loop."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys

from individual.bridge import ROOT, parse_minecraft_port
from individual.lifetime import CONFIG
from individual.storage import INDIVIDUALS, create_lifetime, lifetime_entry, list_lifetimes, select_existing_lifetime


def launch_runtime_monitor(config=CONFIG):
    """Independent instrument process; launcher exit never stops it or controls A."""
    options = ({'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
               if os.name == 'nt' else {'start_new_session': True})
    return subprocess.Popen([sys.executable, '-m', 'individual.runtime_monitor', '--selection', str(config)],
        cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)


@dataclass(frozen=True)
class LaunchConfig:
    port: int
    froi: bool

    def arguments(self):
        return ['--port', str(self.port), *(['--froi'] if self.froi else [])]


class LauncherService:
    def __init__(self, storage_root=INDIVIDUALS, config=CONFIG,
                 minecraft_config=ROOT/'minecraft/config.json',
                 physical_caps=ROOT/'individual/experiment.json', limits=ROOT/'supervisor/limits.yaml'):
        self.storage_root, self.config = Path(storage_root), Path(config)
        self.minecraft_config, self.physical_caps, self.limits = map(Path, (minecraft_config, physical_caps, limits))

    def entries(self):
        return list_lifetimes(self.storage_root, self.config)

    def default_port(self):
        return str(json.loads(self.minecraft_config.read_text(encoding='utf-8-sig'))['port'])

    def missing_selection(self):
        if not self.config.exists():
            return False
        selection = json.loads(self.config.read_text(encoding='utf-8'))
        return not (ROOT / selection['database']).resolve().is_file()

    def create(self, label, confirm_missing=False):
        if self.missing_selection() and not confirm_missing:
            raise ValueError('当前选择数据库缺失；必须明确确认创建新的 A。')
        return create_lifetime(storage_root=self.storage_root, config=self.config, label=label,
                               replace_missing_selection=confirm_missing)

    def prepare(self, directory, port, froi):
        # All preflights precede pointer switching. No --db bypass or EventStore.
        entry = lifetime_entry(directory)
        port = parse_minecraft_port(port)
        from individual.formal_l0 import FormalLimits
        from individual.formal_boundary import preflight, RESOURCE_CAP_KEYS, sensor_caps
        from integration.froi import preflight as froi_preflight, load_caps
        from supervisor.supervisor import load_limits
        limits = load_limits(self.limits)
        resources = {key: limits[key] for key in RESOURCE_CAP_KEYS}
        resources['body_observation_caps'] = sensor_caps(self.minecraft_config)
        preflight(entry['database'], FormalLimits.load(self.physical_caps), resources)
        froi_preflight(entry['database'], bool(froi), load_caps())
        select_existing_lifetime(directory, self.storage_root, self.config)
        return LaunchConfig(port, bool(froi))


def show_launcher(service=None):
    """Return parameters after closing the window; cancel never starts a Core."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        window = tk.Tk()
    except Exception as error:
        raise RuntimeError('无法打开图形启动器。无图形环境请使用 main.py --froi --port <端口>。' + str(error)) from error
    service = service or LauncherService()
    result = None
    window.title('BECA 实验启动器')
    window.geometry('1080x570')
    window.minsize(800, 480)
    panel = ttk.Frame(window, padding=18)
    panel.pack(fill='both', expand=True)
    ttk.Label(panel, text='选择已有个体 A', font=('Microsoft YaHei UI', 13)).pack(anchor='w')
    table_frame = ttk.Frame(panel)
    table_frame.pack(fill='both', expand=True, pady=10)
    columns = ('label', 'identity', 'role', 'version', 'sessions', 'created', 'database')
    table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse', height=8)
    for key, label, width in zip(columns,
        ('名称 / 当前选择', 'individual_id', '角色', '状态版本', 'Session 数', '创建时间', '数据库路径'),
        (160, 300, 90, 80, 85, 170, 350)):
        table.heading(key, text=label)
        table.column(key, width=width, stretch=False)
    vertical = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview)
    horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=table.xview)
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    table.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)
    details, notice = tk.StringVar(value='尚未选择个体 A'), tk.StringVar()
    entries = {}

    def selected():
        ids = table.selection()
        if not ids:
            raise ValueError('请先选择已有个体 A，或新建个体 A。')
        return entries[ids[0]]

    def describe(*_):
        try:
            entry = selected()
            details.set(f"当前选择：{entry['individual_id']}\n数据库：{entry['database']}")
        except ValueError:
            details.set('尚未选择个体 A')

    def refresh():
        records, rejected = service.entries()
        table.delete(*table.get_children())
        entries.clear()
        for entry in records:
            key = entry['individual_id']
            entries[key] = entry
            table.insert('', 'end', iid=key, values=(
                ('★ ' if entry['selected'] else '') + (entry.get('label') or '未命名'), key, entry['role'],
                f"A{entry['state_version']}", entry['session_count'], entry.get('created_at', ''), entry['database']))
            if entry['selected']:
                table.selection_set(key)
                table.see(key)
        notice.set(f'发现 {len(records)} 个可选主线个体；忽略 {len(rejected)} 个非主线或无效目录。')
        if service.missing_selection():
            notice.set('当前选择数据库缺失。可选择另一已有 A，或明确确认新建 A。')
        describe()

    def create():
        label = simpledialog.askstring('新建个体 A', '输入名称（保留所有旧个体与历史）：', parent=window)
        if label is None:
            return
        try:
            confirmed = False
            if service.missing_selection():
                confirmed = messagebox.askyesno('原数据库缺失',
                    '当前选择数据库缺失。是否创建新的 A？\n这不会恢复原 A，也不会删除旧历史。', parent=window)
                if not confirmed:
                    return
            service.create(label, confirmed)
            refresh()
        except Exception as error:
            messagebox.showerror('新建失败', str(error), parent=window)

    ttk.Button(panel, text='新建个体 A', command=create).pack(anchor='w')
    inputs = ttk.Frame(panel)
    inputs.pack(fill='x', pady=14)
    ttk.Label(inputs, text='Minecraft 局域网端口：').pack(side='left')
    port, froi = tk.StringVar(), tk.BooleanVar(value=True)
    ttk.Entry(inputs, textvariable=port, width=12).pack(side='left', padx=8)
    ttk.Checkbutton(inputs, text='FROI-1', variable=froi).pack(side='left', padx=15)
    ttk.Label(panel, textvariable=details, wraplength=1000).pack(anchor='w', pady=8)
    ttk.Label(panel, textvariable=notice, wraplength=1000).pack(anchor='w')
    ttk.Label(panel, text='这些选择是实验者的启动操作，不是 A 的递归或自主决策。').pack(anchor='w', pady=8)
    buttons = ttk.Frame(panel)
    buttons.pack(fill='x', pady=8)

    def start():
        nonlocal result
        try:
            result = service.prepare(selected()['directory'], port.get(), froi.get())
        except Exception as error:
            messagebox.showerror('无法启动实验', str(error), parent=window)
            return
        window.destroy()

    ttk.Button(buttons, text='启动实验', command=start).pack(side='right')
    ttk.Button(buttons, text='取消', command=window.destroy).pack(side='right', padx=10)
    def open_monitor():
        try:
            launch_runtime_monitor(service.config)
        except Exception as error:
            messagebox.showerror('无法打开运行监视器', str(error), parent=window)

    ttk.Button(buttons, text='运行监视器', command=open_monitor).pack(side='left')
    table.bind('<<TreeviewSelect>>', describe)
    for initialize in (lambda: port.set(service.default_port()), refresh):
        try:
            initialize()
        except Exception as error:
            messagebox.showerror('启动配置提示', str(error), parent=window)
    try:
        window.mainloop()
    finally:
        try:
            window.destroy()
        except tk.TclError:
            pass
    return result
