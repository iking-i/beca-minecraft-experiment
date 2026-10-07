"""External read-only runtime instrument. No Core, actions or experiment controls."""
from collections import Counter, deque
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import sqlite3
import threading
import time

from .lifetime import CONFIG, ROOT
from .current_state import current_metadata, ends_table, session_mode


COUNT_TYPES = {
    'Observations': 'WORLD_OBSERVATION', 'Action requests': 'ACTION_REQUESTED',
    'Actions executed': 'ACTION_EXECUTED', 'Experiences': 'EXPERIENCE_FORMED',
    'Recursive outputs': 'RECURSIVE_PARTIAL_OUTPUT', 'Integrations': 'INTEGRATION_COMPLETED',
}
KEY_TYPES = tuple(dict.fromkeys((*COUNT_TYPES.values(), 'OBSERVATION_FRAME',
    'DOWNWARD_FEEDBACK_UPDATED', 'RECURSIVE_FEEDBACK_STORED', 'RECURSION_GENERATED',
    'RECURSIVE_PROCESS_CREATED', 'CHANGE_DETECTED', 'SESSION_STARTED', 'SESSION_ENDED',
    'SESSION_INTERRUPTED', 'CARRIER_STOPPED', 'BRIDGE_CONNECTED', 'BRIDGE_RECONNECTED',
    'SUPERVISOR_PAUSED', 'SUPERVISOR_RESUMED', 'RESOURCE_OBSERVED',
    'LIVE_BODY_CONNECTION_READ', 'LIVE_BODY_STRUCTURE_FORMATION', 'FROI_JOB_EXECUTION')))
STAGES = ('真实输入', 'A 内部处理', '身体输出请求', '身体真实执行', '新的现实输入返回', '继续递归')


def is_failure(kind):
    return any(token in kind for token in ('FAILED', 'FAILURE', 'ERROR', 'REJECTED',
        'DISCONNECTED', 'INTERRUPTED', 'LIMIT_ENCOUNTER'))


@dataclass(frozen=True)
class Event:
    sequence: int
    version: int
    timestamp: str
    kind: str
    data: dict = field(default_factory=dict)

    def evidence(self):
        return f'#{self.sequence} / A{self.version} / {self.timestamp}'

    def summary(self):
        parts = [f'{k}={v}' for k, v in self.data.items()
                 if v is not None and k in ('action_id', 'code', 'frame_id', 'status', 'reason', 'error')]
        return ' '.join(parts)[:240]


class LoopEvidence:
    """Recorded execution-loop order, not a theoretical or causal-law verdict."""
    def __init__(self):
        self.stages = [('○', None) for _ in STAGES]
        self.latest_input = self.latest_processing = None
        self.request = self.executed = self.renewed = None
        self.complete = False

    def accept(self, event):
        kind, data = event.kind, event.data
        if kind == 'WORLD_OBSERVATION':
            self.latest_input = event
            if self.request is None:
                self.stages[0] = ('●', event)
            if (self.executed and not self.renewed and event.sequence > self.executed.sequence
                    and event.version > self.executed.version
                    and data.get('frame_id') and data['frame_id'] != self.request.data.get('frame_id')):
                self.renewed = event
                self.stages[4] = ('●', event)
        elif kind in ('RECURSIVE_PARTIAL_OUTPUT', 'RECURSIVE_PROCESS_CREATED', 'CHANGE_DETECTED'):
            if self.latest_input and event.version == self.latest_input.version:
                self.latest_processing = event
                if self.request is None:
                    self.stages[1] = ('●', event)
            if (kind == 'RECURSIVE_PARTIAL_OUTPUT' and self.renewed
                    and event.sequence > self.renewed.sequence
                    and event.version == self.renewed.version
                    and data.get('frame_id') == self.renewed.data.get('frame_id')
                    and self.request.data.get('action_id') in (data.get('action_ids') or [])
                    and self.stages[0][0] == self.stages[1][0] == '●'):
                self.stages[5] = ('●', event)
                self.complete = True
        elif kind == 'ACTION_REQUESTED':
            self.request, self.executed, self.renewed, self.complete = event, None, None, False
            before = self.latest_input
            matches = before and data.get('frame_id') == before.data.get('frame_id')
            processing = self.latest_processing
            self.stages = [
                ('●', before) if matches else ('?', None),
                ('●', processing) if matches and processing and processing.version == before.version else ('?', None),
                ('●', event), ('○', None), ('○', None), ('○', None)]
        elif kind in ('ACTION_EXECUTED', 'ACTION_FAILED'):
            if (self.request and event.sequence > self.request.sequence
                    and isinstance(self.request.data.get('action_id'), str)
                    and self.request.data['action_id']
                    and data.get('action_id') == self.request.data.get('action_id')):
                if kind == 'ACTION_EXECUTED':
                    self.executed = event
                    self.stages[3] = ('●', event)
                else:
                    self.stages[3] = ('×', event)
                    self.executed = None
        elif kind in ('OBSERVATION_FAILED', 'INPUT_REJECTED'):
            self.stages[4 if self.executed else 0] = ('×', event)
            self.complete = False

    def status(self):
        if self.stages[0][0] == '×' or self.stages[4][0] == '×':
            return 'WAITING', '已记录输入失败；等待新的 WORLD_OBSERVATION'
        if self.complete:
            return 'RUNNING', '已记录完整执行—新输入—递归输出顺序；不推断世界效果因果律'
        if self.request:
            if self.stages[3][0] == '×':
                return 'WAITING', '已记录 ACTION_FAILED；等待后续真实事件'
            if not self.executed:
                return 'WAITING', '等待：ACTION_EXECUTED（须匹配 action_id）'
            if not self.renewed:
                return 'WAITING', '等待：执行后的 WORLD_OBSERVATION'
            return 'WAITING', '等待：关联该 action_id / 新 frame 的 RECURSIVE_PARTIAL_OUTPUT'
        return 'WAITING', '尚未记录 ACTION_REQUESTED；不判断原因'


@dataclass
class View:
    database: str = ''
    individual: str = '—'
    session: str = '—'
    version: int | None = None
    timestamp: str = '—'
    state: str = 'IDLE'
    message: str = '未运行 / 等待实验启动'
    loop: str = 'IDLE'
    waiting: str = '等待实验启动'
    stages: list = field(default_factory=lambda: [('○', None) for _ in STAGES])
    counts: dict = field(default_factory=dict)
    events: tuple = ()


class MonitorReader:
    """One lightweight read transaction per refresh; never instantiate EventStore."""
    def __init__(self, selection=CONFIG, root=ROOT, batch_size=256):
        self.selection, self.root = Path(selection), Path(root)
        self.batch_size = batch_size
        self.attachment = None
        self.cursor = 0
        self.counts = Counter()
        self.events = deque(maxlen=100)
        self.loop = LoopEvidence()

    @staticmethod
    def connect(database):
        # Never immutable=1 for a live WAL database: committed WAL changes must be visible.
        db = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True, timeout=0.2)
        db.execute('PRAGMA query_only=ON')
        return db

    @staticmethod
    def key_filter():
        return '(' + ' OR '.join((
            'e.event_type IN (' + ','.join('?' for _ in KEY_TYPES) + ')',
            "e.event_type LIKE '%FAILED%'", "e.event_type LIKE '%FAILURE%'",
            "e.event_type LIKE '%ERROR%'", "e.event_type LIKE '%REJECTED%'",
            "e.event_type LIKE '%DISCONNECTED%'", "e.event_type LIKE '%INTERRUPTED%'",
            "e.event_type LIKE '%RESOURCE%'", "e.event_type LIKE '%LIMIT_ENCOUNTER%'")) + ')'

    def read_events(self, db, session, upper, initial):
        # Extract just linkage fields; huge provenance/state/audit payloads stay in SQLite.
        fields = """json_object(
            'action_id',json_extract(e.payload,'$.action_id'),
            'code',coalesce(json_extract(e.payload,'$.action_code'),json_extract(e.payload,'$.code')),
            'frame_id',coalesce(json_extract(e.payload,'$.frame_id'),
                json_extract(e.payload,'$.experience.frame_id'),json_extract(e.payload,'$.provenance.frame_id')),
            'action_ids',json_extract(e.payload,'$.experience.action_ids'),
            'status',json_extract(e.payload,'$.status'),
            'reason',json_extract(e.payload,'$.reason'),
            'error',json_extract(e.payload,'$.error.code'))"""
        sql = f"""SELECT e.event_sequence,e.state_version,e.timestamp,e.event_type,{fields}
            FROM events e CROSS JOIN state_sessions ss ON ss.state_version=e.state_version
            WHERE e.event_sequence>? AND e.event_sequence<=? AND ss.session_id=?
            AND {self.key_filter()} ORDER BY e.event_sequence {'DESC' if initial else 'ASC'} LIMIT ?"""
        rows = db.execute(sql, (0 if initial else self.cursor, upper, session, *KEY_TYPES, self.batch_size)).fetchall()
        if initial:
            rows.reverse()
        return [Event(seq, version, stamp, kind, json.loads(raw)) for seq, version, stamp, kind, raw in rows]

    def poll(self):
        if not self.selection.exists():
            return View()
        try:
            selected = json.loads(self.selection.read_text(encoding='utf-8-sig'))
            database = (self.root / selected['database']).resolve()
            individual = selected['individual_id']
            if not database.is_file():
                return View(individual=individual, state='UNKNOWN', loop='WAITING',
                            message='等待所选数据库出现', waiting='数据库尚不可读；继续重试')
            with closing(self.connect(database)) as db:
                db.execute('BEGIN')
                owner = db.execute('SELECT individual_id FROM experiment WHERE singleton=1').fetchone()
                if not owner or owner[0] != individual:
                    raise ValueError('selection / database identity 尚未一致')
                latest = current_metadata(db)
                session_row = db.execute(f"""SELECT s.session_id,se.ended_at,se.reason
                    FROM sessions s LEFT JOIN {ends_table(db)} se USING(session_id)
                    ORDER BY (se.session_id IS NULL) DESC,s.start_version DESC,s.rowid DESC LIMIT 1""").fetchone()
                if not session_row:
                    self.attachment = None
                    return View(str(database), individual, version=latest[0] if latest else None,
                                timestamp=latest[1] if latest else '—')
                session, ended, reason = session_row
                full_history_enabled = session_mode(db, session)
                attachment = (str(database), individual, session)
                initial = attachment != self.attachment
                upper = db.execute('SELECT coalesce(max(event_sequence),0) FROM events').fetchone()[0]
                if initial:
                    counts = Counter(dict(db.execute("""SELECT e.event_type,count(*) FROM events e
                        WHERE e.state_version IN (SELECT state_version FROM state_sessions WHERE session_id=?)
                        GROUP BY e.event_type""", (session,))))
                events = self.read_events(db, session, upper, initial)
            # Update the local display only after a successful, consistent read transaction.
            if initial:
                self.attachment, self.cursor = attachment, 0
                self.counts, self.events, self.loop = counts, deque(maxlen=100), LoopEvidence()
            for event in events:
                if not initial:
                    self.counts[event.kind] += 1
                self.events.append(event)
                self.loop.accept(event)
            self.cursor = upper if initial or len(events) < self.batch_size else events[-1].sequence
            state, message = ('ENDED', f'已结束：{reason}') if ended else ('RUNNING', '运行中（Session 尚未结束）')
            if not ended and latest:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(latest[1])).total_seconds()
                if age > 15:
                    state, message = 'UNKNOWN', 'Session 未记录结束，但超过 15 秒没有状态更新；进程是否运行未知'
            loop, waiting = self.loop.status()
            if ended:
                loop, waiting = 'ENDED', f'Session 已结束：{reason}；保留最后记录'
            elif state == 'UNKNOWN':
                loop = 'UNKNOWN'
            counts_view = {label: self.counts[kind] for label, kind in COUNT_TYPES.items()}
            counts_view['Failures'] = sum(n for kind, n in self.counts.items() if is_failure(kind))
            if not full_history_enabled:
                counts_view = {key: '未记录' for key in counts_view}
                loop, waiting = 'UNKNOWN', 'FULL HISTORY: OFF；逐轮闭环证据未记录'
                message += ' / FULL HISTORY: OFF'
                if ended:
                    loop = 'ENDED'
            else:
                message += ' / FULL HISTORY: ON'
            return View(str(database), individual, session, latest[0] if latest else None,
                        latest[1] if latest else '—', state, message, loop, waiting,
                        list(self.loop.stages), counts_view, tuple(self.events))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            return View(state='UNKNOWN', loop='WAITING', message='等待 / 数据暂不可读', waiting=str(error))

    def payload(self, database, individual, session, sequence):
        with closing(self.connect(database)) as db:
            row = db.execute("""SELECT e.payload FROM events e JOIN state_sessions ss USING(state_version)
                WHERE e.event_sequence=? AND e.individual_id=? AND ss.session_id=?""",
                (sequence, individual, session)).fetchone()
            if row is None:
                raise ValueError('该事件不属于当前 A / Session')
            raw = row[0]
            return json.dumps(json.loads(raw), ensure_ascii=False, indent=2) if len(raw) < 1000000 else raw


class MonitorWorker:
    """Only this daemon performs queries. Closing the UI stops only the instrument."""
    def __init__(self, reader, interval=1.0):
        self.reader, self.interval = reader, interval
        self.stopped = threading.Event()
        self.results = queue.Queue(maxsize=4)
        self.details = queue.Queue()
        self.thread = threading.Thread(target=self.run, daemon=True, name='BECA-read-only-monitor')

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()

    def publish(self, result):
        if self.results.full():
            try:
                self.results.get_nowait()
            except queue.Empty:
                pass
        self.results.put_nowait(result)

    def run(self):
        while not self.stopped.is_set():
            self.publish(('view', self.reader.poll()))
            deadline = time.monotonic() + self.interval
            while not self.stopped.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    token, args = self.details.get(timeout=min(remaining, 0.1))
                except queue.Empty:
                    continue
                try:
                    text = self.reader.payload(*args)
                except (OSError, ValueError, sqlite3.Error) as error:
                    text = '无法读取 payload：' + str(error)
                self.publish(('payload', (token, text)))


class MonitorWindow:
    def __init__(self, window, reader=None):
        import tkinter as tk
        from tkinter import ttk
        self.window = window
        self.closed = False
        self.detail_token = 0
        self.view = View()
        self.worker = MonitorWorker(reader or MonitorReader())
        window.title('BECA 运行监视器')
        window.geometry('1100x850')
        window.minsize(800, 650)
        panel = ttk.Frame(window, padding=12)
        panel.pack(fill='both', expand=True)
        self.header, self.status, self.counts = (tk.StringVar() for _ in range(3))
        ttk.Label(panel, textvariable=self.header, wraplength=1050).pack(anchor='w')
        ttk.Label(panel, textvariable=self.status, wraplength=1050).pack(anchor='w', pady=6)
        stages = ttk.LabelFrame(panel, text='真实运行事件链（只读；不是理论验收）', padding=8)
        stages.pack(fill='x')
        self.stage_text = []
        for index, name in enumerate(STAGES):
            value = tk.StringVar(value=f'○ {name} — 等待')
            self.stage_text.append(value)
            ttk.Label(stages, textvariable=value, wraplength=1000).pack(anchor='w')
            if index < len(STAGES) - 1:
                ttk.Label(stages, text='↓').pack(anchor='w', padx=12)
        ttk.Label(panel, textvariable=self.counts, wraplength=1050).pack(anchor='w', pady=8)
        split = ttk.Panedwindow(panel, orient='vertical')
        split.pack(fill='both', expand=True)
        list_panel, payload_panel = ttk.Frame(split), ttk.Frame(split)
        split.add(list_panel, weight=2)
        split.add(payload_panel, weight=1)
        self.table = ttk.Treeview(list_panel, columns=('time', 'version', 'kind', 'summary'), show='headings')
        for key, title, width in (('time', '时间 / event sequence', 240), ('version', 'A版本', 75),
                                   ('kind', 'event type', 245), ('summary', '简短内容', 400)):
            self.table.heading(key, text=title)
            self.table.column(key, width=width)
        scroll = ttk.Scrollbar(list_panel, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        ttk.Label(payload_panel, text='点击事件查看完整 payload（仅按需读取）').pack(anchor='w')
        self.payload_text = tk.Text(payload_panel, height=9, wrap='word', state='disabled')
        payload_scroll = ttk.Scrollbar(payload_panel, orient='vertical', command=self.payload_text.yview)
        self.payload_text.configure(yscrollcommand=payload_scroll.set)
        self.payload_text.pack(side='left', fill='both', expand=True)
        payload_scroll.pack(side='right', fill='y')
        self.table.bind('<<TreeviewSelect>>', self.select_event)
        window.protocol('WM_DELETE_WINDOW', self.close)
        self.render(self.view)
        self.worker.start()
        window.after(100, self.drain)

    def render(self, view):
        changed = (view.database, view.session) != (self.view.database, self.view.session)
        self.view = view
        self.header.set(f'当前 A：{view.individual}\n当前 Session：{view.session}    '
                        f'当前 state version：{"—" if view.version is None else "A" + str(view.version)}\n'
                        f'最后更新时间：{view.timestamp}')
        self.status.set(f'状态：{view.message}\n闭环状态：{view.loop} — {view.waiting}')
        for name, value, (marker, event) in zip(STAGES, self.stage_text, view.stages):
            value.set(f'{marker} {name}   {event.evidence() if event else "等待 / 无对应记录"}')
        self.counts.set('当前 Session：' + ' | '.join(f'{k}: {v}' for k, v in view.counts.items()))
        if changed:
            self.detail_token += 1
            self.set_payload('')
            self.table.delete(*self.table.get_children())
        wanted = {str(event.sequence) for event in view.events}
        for iid in self.table.get_children():
            if iid not in wanted:
                self.table.delete(iid)
        added = False
        for event in view.events:
            iid = str(event.sequence)
            if not self.table.exists(iid):
                self.table.insert('', 'end', iid=iid, values=(
                    f'{event.timestamp} / #{event.sequence}', f'A{event.version}', event.kind, event.summary()))
                added = True
        if added and view.events and not self.table.selection():
            self.table.see(str(view.events[-1].sequence))

    def set_payload(self, text):
        self.payload_text.configure(state='normal')
        self.payload_text.delete('1.0', 'end')
        self.payload_text.insert('end', text)
        self.payload_text.configure(state='disabled')

    def select_event(self, _event=None):
        ids = self.table.selection()
        if not ids:
            return
        self.detail_token += 1
        self.set_payload('正在读取完整 payload…')
        args = (self.view.database, self.view.individual, self.view.session, int(ids[0]))
        self.worker.details.put((self.detail_token, args))

    def append_payload(self, token, text, offset=0):
        if self.closed or token != self.detail_token:
            return
        if offset == 0:
            self.set_payload('')
        self.payload_text.configure(state='normal')
        self.payload_text.insert('end', text[offset:offset + 16000])
        self.payload_text.configure(state='disabled')
        if offset + 16000 < len(text):
            self.window.after(10, self.append_payload, token, text, offset + 16000)

    def drain(self):
        if self.closed:
            return
        for _ in range(4):
            try:
                kind, result = self.worker.results.get_nowait()
            except queue.Empty:
                break
            if kind == 'view':
                self.render(result)
            else:
                self.append_payload(*result)
        self.window.after(100, self.drain)

    def close(self):
        self.closed = True
        self.worker.stop()
        self.window.destroy()


def main(argv=None):
    import argparse
    import tkinter as tk
    parser = argparse.ArgumentParser(description='BECA external read-only runtime monitor')
    parser.add_argument('--selection', type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    window = tk.Tk()
    MonitorWindow(window, MonitorReader(args.selection))
    window.mainloop()


if __name__ == '__main__':
    main()
