from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from individual.bridge import MinecraftBridge, ROOT, parse_minecraft_port
from supervisor.connection import choose_minecraft_port


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / 'minecraft.json'
        self.original = json.dumps({'host': '127.0.0.1', 'port': 25565,
                                    'username': 'TestBody', 'auth': 'offline'})
        self.config.write_text(self.original, encoding='utf-8')
        self.terminal = Mock()
        self.terminal.isatty.return_value = True

    def test_interactive_port_retries_invalid_input_without_changing_file(self):
        prompt = Mock(side_effect=['hello', '0', '70000', ' 62227 '])
        log = Mock()
        self.assertEqual(choose_minecraft_port(self.config, stream=self.terminal,
                         prompt=prompt, log=log), 62227)
        self.assertEqual(log.call_count, 3)
        self.assertEqual(self.config.read_text(encoding='utf-8'), self.original)

    def test_enter_keeps_config_and_cancel_or_eof_never_selects_a_port(self):
        self.assertIsNone(choose_minecraft_port(self.config, stream=self.terminal,
                          prompt=Mock(return_value='')))
        for prompt in (Mock(return_value='q'), Mock(side_effect=EOFError),
                       Mock(side_effect=KeyboardInterrupt)):
            with self.assertRaisesRegex(ValueError, '取消启动'):
                choose_minecraft_port(self.config, stream=self.terminal, prompt=prompt)

    def test_explicit_port_and_unattended_modes_do_not_prompt(self):
        forbidden = Mock(side_effect=AssertionError('Must not prompt'))
        self.assertEqual(choose_minecraft_port(self.config, override=62227,
                         stream=self.terminal, prompt=forbidden), 62227)
        self.assertIsNone(choose_minecraft_port(self.config, use_config_port=True,
                          stream=self.terminal, prompt=forbidden))
        self.assertIsNone(choose_minecraft_port(self.config, stream=io.StringIO(),
                          prompt=forbidden))
        forbidden.assert_not_called()

    def test_invalid_port_is_rejected_before_launch(self):
        for value in (0, 65536, -1, True, 3.5, '1.0', '１２３', 'localhost:25565'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MinecraftBridge(self.config, port=value)
        self.assertEqual(parse_minecraft_port('1'), 1)
        self.assertEqual(parse_minecraft_port('65535'), 65535)

    def test_supervisor_forwards_alias_to_child_without_starting_real_core(self):
        from supervisor.supervisor import cli
        with patch('sys.argv', ['main.py', '--port', '62227']), \
             patch('individual.lifetime.resolve_runtime_database', return_value=Path(self.temp.name) / 'fixture.db'), \
             patch('supervisor.supervisor.Supervisor') as factory, \
             patch('supervisor.supervisor.threading.Thread'), redirect_stdout(io.StringIO()):
            factory.return_value.run.return_value = 0
            self.assertEqual(cli(), 0)
        child_args = factory.return_value.start.call_args.args[0]
        self.assertEqual(child_args[child_args.index('--minecraft-port') + 1], '62227')
        factory.return_value.close.assert_called_once()

    def test_core_records_actual_port_and_original_config_hash(self):
        from individual.core import main
        with patch('sys.argv', ['individual.core', '--minecraft-config', str(self.config),
                               '--minecraft-port', '62227']), \
             patch('individual.lifetime.resolve_runtime_database', return_value=Path(self.temp.name) / 'fixture.db'), \
             patch('individual.core.ACore') as factory, \
             patch('individual.core.threading.Thread'), patch('individual.core.signal.signal'), \
             redirect_stdout(io.StringIO()):
            factory.return_value.state = SimpleNamespace(individual_id='A-test', state_version=0, session_id='S-test')
            factory.return_value.start.side_effect = RuntimeError('TEST_ONLY stop before connecting')
            self.assertEqual(main(), 1)
        context = factory.call_args.args[4]
        self.assertEqual(context['minecraft_connection']['port'], 62227)
        self.assertEqual(context['minecraft_port_override'], 62227)
        self.assertEqual(context['configuration_hash'], sha256(self.original.encode()).hexdigest())
        self.assertEqual(factory.call_args.args[1].port, 62227)
        self.assertEqual(self.config.read_text(encoding='utf-8'), self.original)

    def test_port_reaches_real_node_adapter_without_a_game_connection(self):
        bridge = MinecraftBridge(self.config, port=62227, timeout=5)
        try:
            bridge.launch()  # Construction only; do not request body.start().
            status = bridge.call('status')
            self.assertEqual(status['port'], 62227)
            self.assertEqual(status['host'], '127.0.0.1')
            self.assertEqual(status['state'], 'stopped')
            self.assertFalse(status['connected'])
        finally:
            bridge.close()
        self.assertEqual(self.config.read_text(encoding='utf-8'), self.original)
