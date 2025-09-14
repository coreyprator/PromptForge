from __future__ import annotations
import argparse, sys
from promptforge_core import VERSION as PF_VERSION
from promptforge_core.builder import build_prompt
from promptforge_core.config import load_config, config_path

def cmd_init(args):
    cfg = load_config()
    print(f"Initialized config at {config_path()}")

def cmd_make(args):
    prompt = build_prompt(args.task, scenario=args.scenario)
    print("=== SYSTEM ===")
    print(prompt["system"])
    print("\n=== USER ===")
    print(prompt["user"])

def cmd_bridge(args):
    from promptforge_bridge.server import run_server
    run_server(host=args.host, port=args.port)

def cmd_gui(args):
    from promptforge_gui.app import run_app
    run_app()

def main(argv=None):
    p = argparse.ArgumentParser("pf")
    p.add_argument("--version", action="version", version=f"%(prog)s {PF_VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init"); sp.set_defaults(func=cmd_init)
    sp = sub.add_parser("make"); sp.add_argument("task"); sp.add_argument("--scenario", default="default"); sp.set_defaults(func=cmd_make)
    sp = sub.add_parser("bridge"); sp.add_argument("--host", default="127.0.0.1"); sp.add_argument("--port", type=int, default=8765); sp.set_defaults(func=cmd_bridge)
    sp = sub.add_parser("gui"); sp.set_defaults(func=cmd_gui)

    args = p.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    sys.exit(main())
