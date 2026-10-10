import pty, os, sys, select, time, termios, struct, fcntl, re
from pathlib import Path

root = Path('/Users/faraz/Projects/SDLC-Azure')
transcripts_dir = root / 'audit' / 'session_transcripts'
fakehome = str(root / 'audit' / 'sandbox' / 'fakehome')
fakerepo = str(root / 'audit' / 'sandbox' / 'fakerepo')

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\([B0]|\x1b\][^\a\x1b]*(?:\a|\x1b\\)')

master, slave = pty.openpty()
winsize = struct.pack('HHHH', 35, 120, 0, 0)
fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)

env = os.environ.copy()
env['HOME'] = fakehome
env['XDG_CONFIG_HOME'] = fakehome + '/.config'
env['TERM'] = 'xterm-256color'

cmd = ['uv', 'run', 'python', '-m', 'agent.ui.cli.main', 'tui', '--repo', fakerepo]

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
start = time.time()
sent_q = False

while time.time() - start < 4:
    r, _, _ = select.select([master], [], [], 0.1)
    if r:
        try:
            d = os.read(master, 4096)
            if not d: break
            full_output += d
        except OSError:
            break
    if time.time() - start > 1.8 and not sent_q:
        os.write(master, b'r') # refresh
        time.sleep(0.3)
        os.write(master, b'\x11') # Ctrl+Q to exit
        sent_q = True

try:
    os.close(master)
    os.kill(pid, 9)
    os.waitpid(pid, 0)
except:
    pass

plain = ANSI_REGEX.sub('', full_output.decode('utf-8', errors='replace'))
(transcripts_dir / '08_tui_app_interface.md').write_text(f"""# Session Transcript: Textual TUI Interface

```text
{plain}
```
""")
print('TUI output length:', len(plain))
print('TUI sample preview:\n', plain[:500])
