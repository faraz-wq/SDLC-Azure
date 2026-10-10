import pty, os, sys, select, time, termios, struct, fcntl, re
from pathlib import Path

root = Path('/Users/faraz/Projects/SDLC-Azure')
transcripts_dir = root / 'audit' / 'session_transcripts'
raw_dir = transcripts_dir / 'raw_ansi'

fakehome = str(root / 'audit' / 'sandbox' / 'fakehome')
fakerepo = str(root / 'audit' / 'sandbox' / 'fakerepo')

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\([B0]|\x1b\][^\a\x1b]*(?:\a|\x1b\\)')

def strip_ansi(text):
    return ANSI_REGEX.sub('', text)

def run_interactive(name, title, mode_cmd, script, cols=120, rows=40, timeout=12, custom_env=None):
    master, slave = pty.openpty()
    winsize = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)

    env = os.environ.copy()
    env['HOME'] = fakehome
    env['XDG_CONFIG_HOME'] = fakehome + '/.config'
    env['TERM'] = 'xterm-256color'
    env['COLUMNS'] = str(cols)
    env['LINES'] = str(rows)
    if custom_env:
        env.update(custom_env)

    cmd = mode_cmd

    pid = os.fork()
    if pid == 0:
        os.close(master)
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        if slave > 2:
            os.close(slave)
        os.chdir(str(root))
        os.execvpe(cmd[0], cmd, env)
        os._exit(1)

    os.close(slave)

    full_output = b''
    start_time = time.time()
    step_idx = 0

    while time.time() - start_time < timeout:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                data = os.read(master, 4096)
                if not data:
                    break
                full_output += data
            except OSError:
                break

        elapsed = time.time() - start_time
        if step_idx < len(script):
            delay, key_data, desc = script[step_idx]
            if elapsed >= delay:
                if isinstance(key_data, str):
                    os.write(master, key_data.encode('utf-8'))
                else:
                    os.write(master, key_data)
                step_idx += 1

    try:
        os.close(master)
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    except Exception:
        pass

    raw_text = full_output.decode('utf-8', errors='replace')
    plain_text = strip_ansi(raw_text)

    (raw_dir / f'{name}.raw').write_bytes(full_output)

    md_content = f"""# Session Transcript: {title}
**Session ID:** `{name}`  
**Terminal Dimensions:** {cols}x{rows}  
**Environment:** `TERM={env.get("TERM", "xterm-256color")}`, sandbox=`{fakerepo}`  
**Wall Clock Duration:** {time.time() - start_time:.2f}s  

---

## Scripted Keystrokes & Events
"""
    for delay, key_data, desc in script:
        key_repr = repr(key_data) if isinstance(key_data, bytes) else key_data.replace('\n', '\\n')
        md_content += f"- **+{delay}s**: `{desc}` (Input: `{key_repr}`)\n"

    md_content += f"""
---

## Complete Rendered Output (Plain Text Screen Capture)

```text
{plain_text}
```
"""
    (transcripts_dir / f'{name}.md').write_text(md_content)
    print(f'Logged transcript: {name}')

# 1. First Contact & Welcome Screen (bare chat)
run_interactive(
    '01_first_contact',
    'First Contact - Launching Chat REPL in clean sandbox',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [(1.5, '/help\n', 'Request /help'), (3.0, '/exit\n', 'Exit session')]
)

# 2. In-Session Slash Command Discovery & Typos
run_interactive(
    '02_slash_commands_and_typos',
    'Slash Commands Discovery, Typos and Unknown Commands',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.2, '/status\n', 'Check active sessions status'),
        (2.5, '/ado\n', 'Check Azure DevOps connection status'),
        (3.8, '/hepl\n', 'Typo in /help command'),
        (5.0, '/invalid_command_xyz\n', 'Unknown slash command'),
        (6.2, '/exit\n', 'Exit session')
    ]
)

# 3. Input Box Resilience: Whitespace, 10k chars, Newlines, Pasting
huge_input = 'A' * 2000 + '\n'
run_interactive(
    '03_input_stress_and_edge_cases',
    'Input Stress: Empty, Whitespace, Multiline Newlines and Huge Inputs',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.2, '\n', 'Empty enter key'),
        (2.0, '   \t  \n', 'Whitespace-only input'),
        (2.8, 'first line\\nsecond line\n', 'Escaped multiline text'),
        (4.0, huge_input, '2000-character single line input'),
        (6.5, '/exit\n', 'Exit session')
    ],
    timeout=10
)

# 4. Interruption & Signal Handling: Ctrl+C at idle, Ctrl+D at idle
run_interactive(
    '04_interruption_signals',
    'Signal Handling: Ctrl+C, Ctrl+D, EOF at Idle Prompt',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.5, b'\x03', 'Send SIGINT (Ctrl+C) at idle prompt'),
        (3.0, b'\x04', 'Send EOF (Ctrl+D) at idle prompt')
    ],
    timeout=5
)

# 5. Natural Language Query & Pi Agent Fallback (Unconfigured Environment)
run_interactive(
    '05_natural_query_agent_chat',
    'Natural Coding Query & Pi Agent Fallback in Sandbox',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.5, 'Can you review the files in this repository?\n', 'Natural language coding query'),
        (5.0, '/exit\n', 'Exit session')
    ],
    timeout=8
)

# 6. Destructive & Dangerous Operations: /clean in-session without prompt
run_interactive(
    '06_in_session_clean_command',
    'In-Session Slash Command: /clean nonexistent and active tickets',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.2, '/clean 42\n', 'Clean ticket 42 via slash command'),
        (2.5, '/clean invalid_id\n', 'Clean invalid ticket id'),
        (3.8, '/exit\n', 'Exit session')
    ]
)

# 7. Odd Terminals & Accessibility: 40x15 small terminal and NO_COLOR
run_interactive(
    '07_small_terminal_and_no_color',
    'Environment: 40x15 Terminal Window with NO_COLOR=1',
    ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'chat', '--repo', fakerepo],
    [
        (1.2, '/help\n', 'Help in small terminal'),
        (3.0, '/exit\n', 'Exit session')
    ],
    cols=40,
    rows=15,
    custom_env={'NO_COLOR': '1'}
)

print('All 7 interactive PTY test sessions logged successfully.')
