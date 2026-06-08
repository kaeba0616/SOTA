"""Run the web simulator: python -m sota.web [--host H] [--port P]"""
import argparse

import uvicorn


def main():
    ap = argparse.ArgumentParser(prog="sota.web")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    uvicorn.run("sota.web.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
