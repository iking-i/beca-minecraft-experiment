"""Human connection setup before A starts; never edits configuration or identity."""

import json
from pathlib import Path
import sys

from individual.bridge import parse_minecraft_port


def choose_minecraft_port(config, override=None, use_config_port=False,
                          stream=None, prompt=None, log=print):
    if override is not None:
        return parse_minecraft_port(override)
    stream = sys.stdin if stream is None else stream
    if use_config_port or not stream.isatty():
        return None  # Preserve unattended launches: the body uses its config port.
    settings = json.loads(Path(config).read_text(encoding='utf-8-sig'))
    current = parse_minecraft_port(settings['port'])
    prompt = input if prompt is None else prompt
    while True:
        try:
            answer = prompt(f'Minecraft 当前局域网端口（回车沿用 {current}，输入 q 取消）：').strip()
        except (EOFError, KeyboardInterrupt):
            raise ValueError('已取消启动，尚未启动 A 或连接游戏') from None
        if not answer:
            return None
        if answer.lower() in ('q', 'quit', 'exit'):
            raise ValueError('已取消启动，尚未启动 A 或连接游戏')
        try:
            return parse_minecraft_port(answer)
        except ValueError as error:
            log(str(error))
