#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import requests


IGDB_GAMES_URL = "https://api.igdb.com/v4/games"


def build_query(game_name: str, limit: int = 5) -> str:
    """
    IGDB query language:
    - search "<text>" does fuzzy search on name.
    - fields: pick what we need for plot.
    """
    safe = game_name.replace('"', '\\"')
    return (
        f'search "{safe}"; '
        f'fields id,name,summary,storyline,first_release_date,genres.name,involved_companies.company.name; '
        f'limit {limit};'
    )


def pick_best_game(results: list, target_name: str) -> dict | None:
    """
    Heuristic pick:
    1) Exact match (case-insensitive) on name
    2) Startswith match
    3) Otherwise first result
    """
    if not results:
        return None

    t = target_name.strip().lower()

    exact = [g for g in results if (g.get("name") or "").strip().lower() == t]
    if exact:
        return exact[0]

    starts = [g for g in results if (g.get("name") or "").strip().lower().startswith(t)]
    if starts:
        return starts[0]

    return results[0]


def extract_plot_text(game_obj: dict) -> str:
    """
    Prefer storyline > summary.
    """
    storyline = (game_obj.get("storyline") or "").strip()
    summary = (game_obj.get("summary") or "").strip()

    if storyline:
        return storyline
    if summary:
        return summary
    return ""


def fetch_plot(game_name: str, client_id: str, token: str) -> tuple[str, dict]:
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    query = build_query(game_name, limit=8)
    resp = requests.post(IGDB_GAMES_URL, headers=headers, data=query, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(
            f"IGDB API failed: HTTP {resp.status_code}\n"
            f"Response: {resp.text[:500]}"
        )

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"IGDB returned non-JSON response: {resp.text[:300]}")

    best = pick_best_game(data, game_name)
    if not best:
        raise RuntimeError(f"No IGDB results found for '{game_name}'.")

    plot = extract_plot_text(best)
    if not plot:
        # If no storyline/summary, still return metadata for debugging
        raise RuntimeError(
            f"Found game '{best.get('name')}', but it has no storyline/summary in IGDB."
        )

    return plot, best


def main():
    ap = argparse.ArgumentParser(description="Fetch game plot from IGDB and save to file.")
    ap.add_argument("--game", required=True, help="Game name to search on IGDB")
    ap.add_argument("--out", required=True, help="Output text file path (e.g., projects/LOL/input_plot.txt)")
    ap.add_argument("--client-id", required=True, help="Twitch Client ID")
    ap.add_argument("--token", required=True, help="Twitch access_token")
    ap.add_argument("--save-json", action="store_true", help="Also save raw IGDB JSON next to output for debugging")
    args = ap.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plot_text, best_obj = fetch_plot(args.game, args.client_id, args.token)

    # Save plot
    out_path.write_text(plot_text.strip() + "\n", encoding="utf-8")

    # Optional debug JSON
    if args.save_json:
        jpath = out_path.parent / "igdb_game_debug.json"
        jpath.write_text(json.dumps(best_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print short log for UI
    name = best_obj.get("name", "Unknown")
    print(f"[IGDB] Selected: {name}")
    print(f"[IGDB] Plot saved to: {out_path}")

    # Print preview (short)
    preview = plot_text.strip().replace("\n", " ")
    if len(preview) > 240:
        preview = preview[:240] + "..."
    print(f"[IGDB] Preview: {preview}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[IGDB] ERROR: {e}", file=sys.stderr)
        raise