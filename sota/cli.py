from sota.model.pool import ItemPool
from sota.solve.ga import solve
from sota.render.summary import build_summary
from sota.render.grid_image import render_layout
from sota.recognize.pool_from_labels import pool_from_labels


def _validate(keys, valid, label):
    bad = [k for k in keys if k not in valid]
    if bad:
        raise ValueError(f"unknown {label}: {bad}")


def run(*, tablets, artifacts, combo, slots, seed, out, gamedata, root,
        generations=60, pop_size=40):
    _validate(tablets, gamedata.tablets, "tablet key")
    _validate(artifacts, gamedata.artifacts, "artifact key")
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")
    pool = ItemPool(tablets=list(tablets), artifacts=list(artifacts))
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)
    if out is not None:
        render_layout(result.layout, combo, gamedata, root).save(out)
    return summary


def run_from_screenshot(*, screenshot, combo, slots, seed, out, gamedata, root,
                        recognize_fn, min_conf=0.5, generations=60, pop_size=40):
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")
    labels = recognize_fn(screenshot)
    pool, low = pool_from_labels(labels, gamedata, min_conf=min_conf)
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)
    if out is not None:
        render_layout(result.layout, combo, gamedata, root).save(out)
    return summary, low


import argparse, pathlib, sys
from sota.model.gamedata import load_game_data
from sota.render.summary import format_summary


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sota", description="Sephiria combo-build optimizer")
    ap.add_argument("--combo", help="target combo key (e.g. yinggalbul)")
    ap.add_argument("--tablets", default="", help="comma-separated tablet keys")
    ap.add_argument("--artifacts", default="", help="comma-separated artifact keys")
    ap.add_argument("--slots", type=int, default=34, help="inventory slot count")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--generations", type=int, default=60)
    ap.add_argument("--pop-size", type=int, default=40)
    ap.add_argument("--out", default="build.png", help="output image path")
    ap.add_argument("--list-combos", action="store_true", help="list combo keys and exit")
    args = ap.parse_args(argv)

    gd = load_game_data()
    if args.list_combos:
        for k, c in gd.combos.items():
            print(f"{k:18s} {c['label']}")
        return 0
    if not args.combo:
        ap.error("--combo is required (or use --list-combos)")

    def split(s):
        return [x.strip() for x in s.split(",") if x.strip()]

    root = pathlib.Path(__file__).resolve().parents[1]
    try:
        summary = run(tablets=split(args.tablets), artifacts=split(args.artifacts),
                      combo=args.combo, slots=args.slots, seed=args.seed, out=args.out,
                      gamedata=gd, root=root,
                      generations=args.generations, pop_size=args.pop_size)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(format_summary(summary))
    print(f"\nimage written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
