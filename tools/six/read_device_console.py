#!/usr/bin/env python3
"""Read-only FM-1 CDC diagnostics. Never sends writes, reset, or boot commands."""
import argparse, json, os, re, select, struct, termios, time
from pathlib import Path


class Console:
    def __init__(self, port):
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        a = termios.tcgetattr(self.fd)
        a[0] = a[1] = a[3] = 0
        a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        a[4] = a[5] = termios.B115200
        a[6][termios.VMIN] = a[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, a)
        self.log = bytearray()
        self.request('')

    def close(self):
        os.close(self.fd)

    def request(self, cmd):
        assert re.fullmatch(r'(?:status|dbg|params|(?:memr|flr) 0x[0-9a-fA-F]+ (?:[1-9][0-9]{0,2})|)', cmd)
        os.write(self.fd, (cmd + '\r').encode())
        out = bytearray()
        end = time.monotonic() + 3
        while time.monotonic() < end:
            if select.select([self.fd], [], [], .05)[0]:
                try:
                    out.extend(os.read(self.fd, 16384))
                except BlockingIOError:
                    continue
                if out.endswith(b'> ') and (not cmd or cmd.encode() in out):
                    self.log.extend(out)
                    return out.decode(errors='replace')
        raise TimeoutError((cmd, bytes(out)))

    def read(self, addr, size, raw=False):
        result = bytearray()
        for at in range(addr, addr + size, 256):
            n = min(256, addr + size - at)
            s = self.request(f'{"flr" if raw else "memr"} 0x{at:x} {n}')
            b = bytearray()
            for line in s.splitlines():
                m = re.fullmatch(r'[0-9A-F]{6,8}:((?: [0-9A-F]{2})+)', line)
                if m:
                    b.extend(bytes.fromhex(m[1]))
            assert len(b) == n, (hex(at), n, s)
            result.extend(b)
        return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', default='/dev/cu.usbmodem21104')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--symbols', type=Path, required=True)
    ap.add_argument('--samples', action='store_true')
    args = ap.parse_args()
    assert args.out.is_dir(), 'Use an existing registered SSD QA directory'
    syms = {m[2]: int(m[1], 16) for m in re.finditer(r'^([0-9a-f]+).*?\s([A-Za-z_][A-Za-z_0-9]*)$', args.symbols.read_text(), re.M)}
    c = Console(args.port)
    try:
        before = c.request('status')
        print(before, flush=True)
        args.out.joinpath('hardware-tracks.bin').write_bytes(c.read(syms['trk'], 0x40f8))
        args.out.joinpath('hardware-song.bin').write_bytes(c.read(syms['song'], 164))
        args.out.joinpath('hardware-prf.bin').write_bytes(c.read(syms['prf'], 612))
        costs = struct.unpack('<6I', c.read(syms['mc_tk'], 24))
        print('Track render us:', [round(x / 24, 2) for x in costs], flush=True)
        for k, off in enumerate((0xa0000, 0xb4000)):
            n = 81920 if args.samples else 64
            args.out.joinpath(f'hardware-bank-{k}-raw.bin').write_bytes(c.read(off, n, True))
            args.out.joinpath(f'hardware-bank-{k}-xip.bin').write_bytes(c.read(0x02000000 + off - 0x4000, 64))
            print(f'Bank {k} read ({n} raw bytes)', flush=True)
        after = c.request('status')
        args.out.joinpath('hardware-console.txt').write_bytes(c.log)
        args.out.joinpath('hardware-render-costs.json').write_text(json.dumps({'before': before, 'after': after, 'track_ticks': costs}, indent=2))
        print(after, flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()
