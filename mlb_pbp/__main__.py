import argparse
import sys
from datetime import date
from pathlib import Path

from .archive import archive, verify
from .client import Client, feed_url
from .formatter import render


def main():
    parser = argparse.ArgumentParser(prog='mlb-pbp')
    commands = parser.add_subparsers(dest='cmd', required=True)
    g = commands.add_parser('game')
    g.add_argument('id', type=int)
    g.add_argument('--format', choices=['raw', 'text', 'events'], default='text')
    g.add_argument('--output', type=Path)
    a = commands.add_parser('archive')
    a.add_argument('--start', type=date.fromisoformat, default=date(2014,1,1))
    a.add_argument('--end', type=date.fromisoformat, default=date.today())
    a.add_argument('--output', type=Path, default=Path('archive'))
    a.add_argument('--formats', default='text,raw,events')
    a.add_argument('--workers', type=int, default=2)
    a.add_argument('--request-delay', type=float, default=0.2)
    a.add_argument('--refresh', action='store_true')
    a.add_argument('--raw-uncompressed', action='store_true')
    commands.add_parser('verify').add_argument('root', type=Path)
    args = parser.parse_args()
    if args.cmd == 'archive':
        args.formats = args.formats.split(',')
        if args.start > args.end or args.start.year < 2014 or args.workers < 1 or args.request_delay < 0 or set(args.formats)-{'raw','text','events'}:
            parser.error('Invalid range, worker count, delay or formats')
        archive(args)
    elif args.cmd == 'verify':
        verify(args.root)
    else:
        content = render(args.format, *Client().get(feed_url(args.id), args.id))
        if args.output:
            args.output.write_bytes(content)
        else:
            sys.stdout.buffer.write(content)


if __name__ == '__main__':
    main()
