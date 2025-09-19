"""
NAZIM GP - 2025 F1 race predictor (prototype)

What this script does:
- Loads the 2025 season JSON at the exact path you provided by default.
- Handles two formats used in your DB:
    * Standard rounds (keys: p1, p2, p3, qualifying, race, start, pitStops, fastestLaps, standings, constructors)
    * Special rounds (Belgium round 13, Miami round 6, China round 2) that use: practice, sprintQualifying, sprint, qualifying, race
- Extracts driver-level features from a chosen round and simple season-level features (from standings/constructors when available).
- Produces a simple rule-based scoring to output a predicted podium (top-K drivers) for the selected round.

Notes / next steps:
- This is a lightweight, dependency-free prototype (only uses stdlib). Replace scoring with a ML model later (scikit-learn / XGBoost) and persist training data.
- The script attempts to be robust to small differences in JSON keys; if your DB uses very different key names, we may need to adapt the parsers.

Usage:
    python NAZIM_GP.py --db "C:\\Users\\Joseph N Nimyel\\OneDrive\\Documents\\Mimo Projects\\F1\\DataBase\\F1-Seasons-2025.json" --round 5 --topk 3

"""

import argparse
import json
import math
import statistics
from collections import defaultdict


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_rounds_container(data):
    """Try to find the list of rounds/races in multiple possible layouts."""
    # common keys
    for key in ("races", "Races", "rounds", "Rounds", "data", "season", "events"):
        if isinstance(data, dict) and key in data and isinstance(data[key], list):
            return data[key]
    # maybe the file itself is the list
    if isinstance(data, list):
        return data
    # fallback: try values that are lists
    for v in data.values() if isinstance(data, dict) else []:
        if isinstance(v, list):
            return v
    raise ValueError("Could not find rounds list in the JSON file. Please inspect file structure.")


def round_number_of(r):
    # try common fields
    for field in ('round', 'Round', 'raceNumber', 'roundNumber'):
        if isinstance(r, dict) and field in r:
            try:
                return int(r[field])
            except Exception:
                pass
    # maybe 'name' contains e.g. 'Round 5' or 'Belgium'
    return None


def get_list_safe(d, key):
    if not isinstance(d, dict):
        return []
    v = d.get(key)
    if isinstance(v, list):
        return v
    # sometimes nested under 'results' or 'result'
    if isinstance(v, dict):
        for alt in ("results", "result", "items"):
            if alt in v and isinstance(v[alt], list):
                return v[alt]
    return []


def extract_driver_id(result_item):
    # attempts to return a stable driver key (e.g. 'name' or driverId)
    if not isinstance(result_item, dict):
        return str(result_item)
    for k in ('driverId', 'driver_id', 'Driver', 'driver', 'name'):
        if k in result_item:
            v = result_item[k]
            if isinstance(v, dict):
                # e.g. {'givenName': 'Max', 'familyName': 'Verstappen'}
                given = v.get('givenName') or v.get('first') or ''
                fam = v.get('familyName') or v.get('last') or ''
                name = (given + ' ' + fam).strip()
                if name:
                    return name
            elif isinstance(v, str):
                return v
    # sometimes the driver is nested under 'Driver' -> 'familyName'
    if 'Driver' in result_item and isinstance(result_item['Driver'], dict):
        drv = result_item['Driver']
        given = drv.get('givenName') or drv.get('first') or ''
        fam = drv.get('familyName') or drv.get('last') or ''
        name = (given + ' ' + fam).strip()
        if name:
            return name
    # fallback: try 'constructor' or 'team'
    if 'constructor' in result_item:
        return str(result_item['constructor'])
    return json.dumps(result_item, sort_keys=True)


def safe_int(v, default=None):
    try:
        return int(v)
    except Exception:
        return default


def build_driver_features_for_round(round_entry, season_standings_map=None):
    """Return a dict driver -> features for the given round entry."""
    features = defaultdict(lambda: {
        'qual_pos': None,
        'start_pos': None,
        'practice_pos_list': [],
        'race_pos': None,
        'sprint_pos': None,
        'fastest_lap_rank': None,
        'pitstops': 0,
        'season_standing': None,
    })

    # 1) Practices: either p1/p2/p3 or practice list
    for p_key in ('p1', 'p2', 'p3'):
        for item in get_list_safe(round_entry, p_key):
            driver = extract_driver_id(item)
            grid = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
            if grid is not None:
                features[driver]['practice_pos_list'].append(grid)
    # alternate combined practice format
    for item in get_list_safe(round_entry, 'practice'):
        driver = extract_driver_id(item)
        grid = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
        if grid is not None:
            features[driver]['practice_pos_list'].append(grid)

    # 2) qualifying (and sprintQualifying)
    for q_key in ('qualifying', 'sprintQualifying'):
        for item in get_list_safe(round_entry, q_key):
            driver = extract_driver_id(item)
            pos = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
            if pos is not None:
                # prefer real qualifying over sprintQualifying when both exist
                if q_key == 'qualifying' or features[driver]['qual_pos'] is None:
                    features[driver]['qual_pos'] = pos

    # 3) race results
    for item in get_list_safe(round_entry, 'race'):
        driver = extract_driver_id(item)
        pos = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
        start = safe_int(item.get('grid') or item.get('start') or (item.get('startingPosition') if isinstance(item.get('startingPosition'), int) else None))
        if pos is not None:
            features[driver]['race_pos'] = pos
        if start is not None:
            features[driver]['start_pos'] = start

    # 4) sprint results
    for item in get_list_safe(round_entry, 'sprint'):
        driver = extract_driver_id(item)
        pos = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
        start = safe_int(item.get('start') or item.get('grid') or item.get('startingPosition'))
        if pos is not None:
            features[driver]['sprint_pos'] = pos
        if start is not None and features[driver]['start_pos'] is None:
            features[driver]['start_pos'] = start

    # 5) fastest laps
    # sometimes fastestLaps is a list of items with driver info and 'rank' or 'position'
    for item in get_list_safe(round_entry, 'fastestLaps'):
        driver = extract_driver_id(item)
        rank = safe_int(item.get('rank') or item.get('position') or item.get('pos'))
        if rank is not None:
            features[driver]['fastest_lap_rank'] = rank

    # 6) pitStops: count stops per driver
    # pitStops may be a dict with 'stops' list per driver or flat list
    ps_entries = get_list_safe(round_entry, 'pitStops')
    if ps_entries:
        # if flat list of stops where each stop has 'driver'
        for stop in ps_entries:
            driver = extract_driver_id(stop.get('driver') if isinstance(stop, dict) and 'driver' in stop else stop)
            if driver:
                features[driver]['pitstops'] += 1
    # sometimes pitStops is dict: driverId -> list
    if isinstance(round_entry.get('pitStops'), dict):
        for k, v in round_entry['pitStops'].items():
            driver = k
            if isinstance(v, list):
                features[driver]['pitstops'] += len(v)

    # 7) standings / constructors (season level info)
    if season_standings_map:
        for drv, entry in season_standings_map.items():
            features[drv]['season_standing'] = entry

    # compute aggregated practice position avg
    for drv, f in list(features.items()):
        if f['practice_pos_list']:
            try:
                f['practice_pos'] = statistics.mean(f['practice_pos_list'])
            except Exception:
                f['practice_pos'] = None
        else:
            f['practice_pos'] = None

    return features


def build_season_standings_map(rounds_list):
    """Try to build a map driver -> season standing position from any round that contains 'standings'.
    We prefer the latest standings found.
    """
    last = None
    for r in rounds_list:
        s = get_list_safe(r, 'standings')
        if s:
            last = s
    # convert from standings list to a map
    result = {}
    if last:
        for item in last:
            driver = extract_driver_id(item)
            pos = safe_int(item.get('position') or item.get('pos') or item.get('rank'))
            if pos is not None:
                result[driver] = pos
    return result


def score_drivers(features_map):
    """Simple heuristic scoring function. Higher score -> more likely podium.
    Customize weights to your taste or replace by ML model later.

    We use these features (if present):
      - qual_pos (lower is better)
      - practice_pos (lower better)
      - season_standing (lower better)
      - fastest_lap_rank (lower better)
      - sprint_pos (lower better)
      - start_pos (lower better)
      - pitstops (fewer is better)

    Missing values are handled conservatively.
    """
    scored = []
    for drv, f in features_map.items():
        # base score
        score = 0.0
        weights = {
            'qual_pos': 0.35,
            'season_standing': 0.25,
            'practice_pos': 0.15,
            'sprint_pos': 0.08,
            'start_pos': 0.08,
            'fastest_lap_rank': 0.05,
            'pitstops': -0.02,
        }
        # lower pos -> better -> convert to contribution = 1/pos
        def contrib(val, w):
            if val is None:
                return 0.0
            try:
                v = float(val)
                if v <= 0:
                    return 0.0
                return w * (1.0 / v)
            except Exception:
                return 0.0

        score += contrib(f.get('qual_pos'), weights['qual_pos'])
        score += contrib(f.get('season_standing'), weights['season_standing'])
        score += contrib(f.get('practice_pos'), weights['practice_pos'])
        score += contrib(f.get('sprint_pos'), weights['sprint_pos'])
        score += contrib(f.get('start_pos'), weights['start_pos'])
        score += contrib(f.get('fastest_lap_rank'), weights['fastest_lap_rank'])
        # pitstops penalty: more stops worse
        ps = f.get('pitstops')
        if ps is not None:
            try:
                score += weights['pitstops'] * float(ps)
            except Exception:
                pass

        scored.append((drv, score, f))
    # sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def predict_podium_for_round(round_entry, rounds_list=None, topk=3):
    season_map = build_season_standings_map(rounds_list) if rounds_list is not None else {}
    features = build_driver_features_for_round(round_entry, season_map)
    scored = score_drivers(features)
    return scored[:topk]


def pick_round_by_number(rounds_list, round_num):
    # prefer round entries whose round() matches; otherwise fallback to index
    for r in rounds_list:
        rn = round_number_of(r)
        if rn is not None and rn == round_num:
            return r
    # if not found, try index (round_num-1)
    idx = round_num - 1
    if 0 <= idx < len(rounds_list):
        return rounds_list[idx]
    raise ValueError(f"Round {round_num} not found in the 2025 JSON (tried by 'round' field and by index).")


def main():
    parser = argparse.ArgumentParser(description='NAZIM GP - 2025 lightweight predictor')
    parser.add_argument('--db', type=str, required=False,
                        default=r"C:\Users\Joseph N Nimyel\OneDrive\Documents\Mimo Projects\F1\DataBase\F1-Seasons-2025.json",
                        help='Path to your 2025 season JSON file')
    parser.add_argument('--round', type=int, default=None, help='Round number to predict (1-based). Default: latest available')
    parser.add_argument('--topk', type=int, default=3, help='How many top predictions to show')
    args = parser.parse_args()

    data = load_json(args.db)
    rounds = find_rounds_container(data)
    if not rounds:
        print('No rounds found in the JSON file.')
        return

    # Determine the target round
    if args.round is None:
        # pick last available round
        target_round = rounds[-1]
    else:
        target_round = pick_round_by_number(rounds, args.round)

    # Predict
    preds = predict_podium_for_round(target_round, rounds_list=rounds, topk=args.topk)

    print('\nNAZIM GP - Predicted Top {} for round {}\n'.format(args.topk, (round_number_of(target_round) or 'unknown')))
    for i, (drv, score, feats) in enumerate(preds, start=1):
        print(f"{i}. {drv}  (score={score:.4f})")
        # show some features for debugging
        show = {
            'qual_pos': feats.get('qual_pos'),
            'start_pos': feats.get('start_pos'),
            'practice_mean': feats.get('practice_pos'),
            'season_standing': feats.get('season_standing'),
            'sprint_pos': feats.get('sprint_pos'),
            'pitstops': feats.get('pitstops')
        }
        print('   features:', show)


if __name__ == '__main__':
    main()
