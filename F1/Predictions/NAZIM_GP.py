"""
NAZIM GP - 2025 F1 race predictor with ML training & evaluation (cleaned)
- Adds pit lap time features, weather normalization, driver name normalization,
  and support for sprint/sprintQualifying. Includes training, evaluation,
  model saving and round prediction.
Requirements: pandas, numpy, scikit-learn, joblib
"""

import argparse
import json
import os
import math
import statistics  # Added missing import
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score, precision_score, recall_score, f1_score
import joblib

# ----------------------------- Helpers -----------------------------

def load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_time_to_seconds(t: str):
    """Convert time string (e.g., '1:20.901') into total seconds as float."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    if not isinstance(t, str):
        return None
    try:
        if ':' in t:
            parts = t.split(':')
            if len(parts) == 2:
                m, s = parts
                return float(m) * 60.0 + float(s)
            # fallback join
            total = 0.0
            for i, part in enumerate(reversed(parts)):
                total += float(part) * (60 ** i)
            return total
        return float(t)
    except Exception:
        return None

def normalize_weather(w: str) -> str:
    """Normalize various weather descriptions into 'dry', 'wet', or 'mixed'."""
    if not w:
        return "mixed"
    w = str(w).lower()
    if any(k in w for k in ["dry", "sun", "clear"]):
        return "dry"
    if any(k in w for k in ["wet", "rain", "showers"]):
        return "wet"
    return "mixed"

def normalize_driver_name(name: str) -> str:
    """Normalize driver name strings to a consistent 'Firstname Lastname' form."""
    if not name:
        return None
    # If name is a dict with givenName/familyName
    if isinstance(name, dict):
        given = name.get('givenName') or name.get('first') or ''
        family = name.get('familyName') or name.get('last') or ''
        full = f"{given} {family}".strip()
        return ' '.join([p.capitalize() for p in full.split()]) if full else None
    # Replace commas and extra spaces, then capitalize parts
    s = str(name).strip()
    # handle "Last, First" -> "First Last"
    if ',' in s:
        parts = [p.strip() for p in s.split(',') if p.strip()]
        if len(parts) >= 2:
            s = parts[1] + ' ' + parts[0]
        else:
            s = parts[0]
    parts = [p for p in s.split() if p]
    return ' '.join([p.capitalize() for p in parts]) if parts else None

def get_rounds_list(data: Any) -> List[Dict[str, Any]]:
    """Return list of round dicts from various possible JSON structures."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # common keys that contain lists
        for key in ("races", "Races", "rounds", "Rounds", "data", "season", "events"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # otherwise treat top-level keys as rounds
        rounds = []
        for k, v in data.items():
            if isinstance(v, dict):
                copy = dict(v)
                copy['_key'] = k
                rounds.append(copy)
        if rounds:
            return rounds
    raise ValueError('Could not parse rounds container in JSON file')

# ----------------------------- Feature builder -----------------------------

def build_driver_features_for_round_df(round_entry: Dict[str, Any], season_driver_points_map: Dict[str, float], constructors_map: Dict[str, float]):
    """Extract per-driver features for a round (supports sprint formats).
    Returns list of dict rows.
    """
    rows = []
    results_block = round_entry.get('results') or round_entry

    # Race and sprint results (if any)
    race_list = results_block.get('race') or []
    sprint_list = results_block.get('sprint') or []
    if not isinstance(race_list, list):
        race_list = []
    if not isinstance(sprint_list, list):
        sprint_list = []
    combined_results = race_list + sprint_list

    qualifying_list = results_block.get('qualifying') or []
    sprint_qual_list = results_block.get('sprintQualifying') or []

    # Practice sessions
    practice_p1 = results_block.get('p1') or []
    practice_p2 = results_block.get('p2') or []
    practice_p3 = results_block.get('p3') or []
    if 'practice' in round_entry and isinstance(round_entry['practice'], dict):
        # flatten practice.{p1,p2,p3} if present
        practice_combined = []
        for k in ('p1', 'p2', 'p3'):
            practice_combined.extend(round_entry['practice'].get(k, []))
        if practice_combined:
            practice_p1 = practice_combined

    fastest_list = round_entry.get('fastestLaps') or results_block.get('fastestLaps') or []
    pitstops = round_entry.get('pitStops') or results_block.get('pitStops') or []

    # metadata
    track_length = round_entry.get('trackLength') or round_entry.get('track_length')
    try:
        track_length = float(track_length) if track_length is not None else None
    except Exception:
        track_length = None
    safety_cars = round_entry.get('safetyCars') or 0
    weather = normalize_weather(round_entry.get('weather'))

    # Build rows for every driver appearing in combined_results
    for r in combined_results:
        # driver extraction (support dict or string)
        driver = r.get('driver') or r.get('Driver') or r.get('driverName') or r.get('name')
        if isinstance(driver, dict):
            driver = normalize_driver_name(driver)
        else:
            driver = normalize_driver_name(driver)
        if not driver:
            continue

        row = {
            'round': round_entry.get('round') or round_entry.get('_key'),
            'event_name': round_entry.get('name') or round_entry.get('_key'),
            'driver': driver,
            'team': r.get('team') or r.get('constructor') or r.get('teamName'),
            'target_pos': r.get('pos') or r.get('position') or r.get('rank'),
            'start_pos': r.get('start') or r.get('grid') or r.get('startingPosition'),
            'laps': r.get('laps') or None,
            'status': r.get('status') or None,
            'points': r.get('points') or 0,
            'track_length': track_length,
            'safety_cars': safety_cars,
            'weather': weather
        }

        # Qualifying position (match normalized names)
        q = None
        for qent in qualifying_list:
            qname = qent.get('driver') or qent.get('Driver') or qent.get('name')
            if normalize_driver_name(qname) == driver:
                q = qent
                break
        if q:
            row['qual_pos'] = q.get('pos') or q.get('position')

        # Sprint qualifying
        sq = None
        for sqent in sprint_qual_list:
            sqname = sqent.get('driver') or sqent.get('Driver') or sqent.get('name')
            if normalize_driver_name(sqname) == driver:
                sq = sqent
                break
        if sq:
            row['sprint_qual_pos'] = sq.get('pos') or sq.get('position')

        # Practice mean (times in seconds preferred)
        practice_positions = []
        for p_list in (practice_p1, practice_p2, practice_p3):
            for pent in p_list:
                pname = pent.get('driver') or pent.get('Driver') or pent.get('name')
                if normalize_driver_name(pname) == driver:
                    t = parse_time_to_seconds(pent.get('time'))
                    if t is not None:
                        practice_positions.append(t)
                    elif pent.get('pos') is not None:
                        try:
                            practice_positions.append(float(pent.get('pos')))
                        except Exception:
                            pass
        row['practice_mean'] = float(statistics.mean(practice_positions)) if practice_positions else None

        # Fastest lap time/rank for the round
        fl = None
        for fent in fastest_list:
            fname = fent.get('driver') or fent.get('Driver') or fent.get('name')
            if normalize_driver_name(fname) == driver:
                fl = fent
                break
        if fl:
            row['fastest_lap_time'] = parse_time_to_seconds(fl.get('lapTime') or fl.get('time'))
            row['fastest_lap_rank'] = fl.get('rank') or fl.get('position')

        # Pit stops: count and per-stop times (if available)
        pit_entry = None
        if isinstance(pitstops, list):
            for pent in pitstops:
                pname = pent.get('driver') or pent.get('Driver') or pent.get('name')
                if normalize_driver_name(pname) == driver:
                    pit_entry = pent
                    break
        elif isinstance(pitstops, dict):
            # dict keyed by driver name -> list of stops
            for key, val in pitstops.items():
                if normalize_driver_name(key) == driver:
                    pit_entry = {'stops': len(val), 'stopsDetail': val}
                    break
        if pit_entry:
            stops_detail = pit_entry.get('stopsDetail') or []
            times = []
            for d in stops_detail:
                t = d.get('time')
                tsec = None
                if isinstance(t, (int, float)):
                    tsec = float(t)
                else:
                    try:
                        tsec = float(t)
                    except Exception:
                        tsec = None
                if tsec is not None:
                    times.append(tsec)
            row['pitstops'] = pit_entry.get('stops') or len(stops_detail)
            if times:
                row['pit_avg_time'] = float(np.mean(times))
                row['pit_min_time'] = float(np.min(times))
                row['pit_total_time'] = float(np.sum(times))
            else:
                row['pit_avg_time'] = row['pit_min_time'] = row['pit_total_time'] = None
        else:
            row['pitstops'] = 0
            row['pit_avg_time'] = row['pit_min_time'] = row['pit_total_time'] = None

        # Season / constructor points maps (may be None)
        row['season_points'] = season_driver_points_map.get(driver, None)
        row['constructor_points'] = constructors_map.get(row.get('team'), None)  # Fixed: use row.get('team')

        rows.append(row)
    return rows

def build_dataset_from_json(path: str) -> pd.DataFrame:
    """Load JSON and build a cleaned DataFrame with engineered features."""
    data = load_json(path)
    rounds = get_rounds_list(data)

    # Build season-level maps from first available standings encountered
    season_driver_points = {}
    constructors_points = {}
    for r in rounds:
        s = None
        if isinstance(r.get('standings'), dict):
            s = r['standings']
        elif isinstance(r.get('results'), dict) and isinstance(r['results'].get('standings'), dict):
            s = r['results']['standings']
        if s and isinstance(s.get('drivers'), list):
            for d in s['drivers']:
                name = d.get('driver') or d.get('Driver') or d.get('name')
                name = normalize_driver_name(name)
                points = d.get('points') or d.get('pts')
                if name and points is not None:
                    try:
                        season_driver_points[name] = float(points)
                    except Exception:
                        pass
        if s and isinstance(s.get('constructors'), list):
            for c in s['constructors']:
                team = c.get('team') or c.get('name') or c.get('fullTeam')
                pts = c.get('points')
                if team and pts is not None:
                    try:
                        constructors_points[team] = float(pts)
                    except Exception:
                        pass

    # iterate rounds and build rows
    all_rows = []
    for r in rounds:
        rows = build_driver_features_for_round_df(r, season_driver_points, constructors_points)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    # coerce numeric columns
    numeric_cols = ['target_pos', 'start_pos', 'qual_pos', 'pitstops', 'season_points', 'constructor_points', 'laps', 'fastest_lap_rank', 'pit_avg_time', 'pit_min_time', 'pit_total_time']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# ----------------------------- Modelling -----------------------------

def train_and_evaluate(df: pd.DataFrame, model_dir: str, test_size: float = 0.2, random_state: int = 42):
    """Train regressor and classifier; evaluate and save models."""
    os.makedirs(model_dir, exist_ok=True)

    # keep only rows with defined target position
    df = df[df['target_pos'].notnull()].copy()

    # features (include new pit time features)
    numeric_feats = ['qual_pos', 'start_pos', 'practice_mean', 'fastest_lap_time', 'fastest_lap_rank', 'pitstops', 'pit_avg_time', 'pit_min_time', 'pit_total_time', 'season_points', 'constructor_points', 'track_length', 'safety_cars', 'laps']
    categorical_feats = ['weather', 'team', 'event_name']

    # targets
    df['target_pos'] = pd.to_numeric(df['target_pos'], errors='coerce')
    df['target_podium'] = (df['target_pos'] <= 3).astype(int)

    X = df[numeric_feats + categorical_feats]
    y_reg = df['target_pos']
    y_clf = df['target_podium']

    # train/test split
    stratify_col = df['event_name'] if 'event_name' in df else None
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=test_size, random_state=random_state, stratify=stratify_col)

    # preprocessing
    numeric_transform = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
    categorical_transform = Pipeline(steps=[('imputer', SimpleImputer(strategy='constant', fill_value='missing')), ('onehot', OneHotEncoder(handle_unknown='ignore'))])
    preproc = ColumnTransformer(transformers=[('num', numeric_transform, numeric_feats), ('cat', categorical_transform, categorical_feats)])

    # pipelines
    regressor = Pipeline(steps=[('preproc', preproc), ('model', RandomForestRegressor(n_estimators=200, random_state=random_state))])
    classifier = Pipeline(steps=[('preproc', preproc), ('model', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=random_state))])

    # fit
    print('Training regressor...')
    regressor.fit(X_train, y_reg_train)
    print('Training classifier...')
    classifier.fit(X_train, y_clf_train)

    # evaluate regressor
    y_reg_pred = regressor.predict(X_test)
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    rmse = math.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    print(f'Regressor MAE: {mae:.4f}, RMSE: {rmse:.4f}')

    # evaluate classifier
    y_clf_pred = classifier.predict(X_test)
    acc = accuracy_score(y_clf_test, y_clf_pred)
    prec = precision_score(y_clf_test, y_clf_pred, zero_division=0)
    rec = recall_score(y_clf_test, y_clf_pred, zero_division=0)
    f1 = f1_score(y_clf_test, y_clf_pred, zero_division=0)
    print(f'Classifier accuracy: {acc:.4f}, precision: {prec:.4f}, recall: {rec:.4f}, f1: {f1:.4f}')

    # cross-validation (best-effort)
    try:
        cv_scores = cross_val_score(regressor, X, y_reg, scoring='neg_mean_absolute_error', cv=5)
        print('Regressor CV MAE (5-fold):', -cv_scores.mean())
    except Exception:
        print('Skipping regressor cross-validation (possibly small dataset / error)')
    try:
        cv_scores_clf = cross_val_score(classifier, X, y_clf, scoring='accuracy', cv=5)
        print('Classifier CV accuracy (5-fold):', cv_scores_clf.mean())
    except Exception:
        print('Skipping classifier cross-validation (possibly small dataset / error)')

    # save models
    reg_path = os.path.join(model_dir, 'nazim_regressor.joblib')
    clf_path = os.path.join(model_dir, 'nazim_classifier.joblib')
    joblib.dump(regressor, reg_path)
    joblib.dump(classifier, clf_path)
    print(f'Saved regressor to: {reg_path}')
    print(f'Saved classifier to: {clf_path}')

    metrics = {'regression': {'mae': mae, 'rmse': rmse}, 'classification': {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}}
    return regressor, classifier, metrics

# ----------------------------- Prediction -----------------------------

def load_models(model_dir: str):
    reg_path = os.path.join(model_dir, 'nazim_regressor.joblib')
    clf_path = os.path.join(model_dir, 'nazim_classifier.joblib')
    if not os.path.exists(reg_path) or not os.path.exists(clf_path):
        raise FileNotFoundError('Model files not found in model_dir. Train models first using --train')
    reg = joblib.load(reg_path)
    clf = joblib.load(clf_path)
    return reg, clf

def predict_for_round(round_entry: Dict[str, Any], regressor, classifier, season_driver_points_map: Dict[str, float], constructors_map: Dict[str, float], topk: int = 3):
    rows = build_driver_features_for_round_df(round_entry, season_driver_points_map, constructors_map)
    df = pd.DataFrame(rows)
    if df.empty:
        return []
    
    # Define expected features
    numeric_feats = ['qual_pos', 'start_pos', 'practice_mean', 'fastest_lap_time', 'fastest_lap_rank', 'pitstops', 'pit_avg_time', 'pit_min_time', 'pit_total_time', 'season_points', 'constructor_points', 'track_length', 'safety_cars', 'laps']
    categorical_feats = ['weather', 'team', 'event_name']
    all_feats = numeric_feats + categorical_feats
    
    # Ensure all expected columns exist
    for feat in all_feats:
        if feat not in df.columns:
            if feat in numeric_feats:
                df[feat] = np.nan
            else:
                df[feat] = 'missing'
    
    features = df[all_feats]

    pred_pos = regressor.predict(features)
    pred_podium_prob = None
    try:
        if hasattr(classifier, 'predict_proba'):
            pred_podium_prob = classifier.predict_proba(features)[:, 1]
        else:
            pred_podium_prob = classifier.predict(features)
    except Exception:
        pred_podium_prob = None

    df['pred_pos'] = pred_pos
    df['pred_podium_prob'] = pred_podium_prob
    df_sorted = df.sort_values(by='pred_pos')
    return df_sorted.head(topk)[['driver', 'team', 'pred_pos', 'pred_podium_prob']].to_dict(orient='records')

# ----------------------------- CLI -----------------------------

def main():
    parser = argparse.ArgumentParser(description='NAZIM GP - 2025 predictor and trainer')
    parser.add_argument('--db', type=str, required=False, default=r"C:\Users\Joseph N Nimyel\OneDrive\Documents\Mimo Projects\F1\DataBase\F1-Seasons-2025.json")
    parser.add_argument('--train', action='store_true', help='Build dataset, train models and save them')
    parser.add_argument('--model-dir', type=str, default='./models', help='Where to save / load models')
    parser.add_argument('--test-size', type=float, default=0.2, help='Train/test split for evaluation')
    parser.add_argument('--predict', action='store_true', help='Load models and predict for a round')
    parser.add_argument('--round', type=int, default=None, help='Round number to use for prediction (1-based). Default: latest available')
    parser.add_argument('--topk', type=int, default=3, help='How many top predictions to return')
    args = parser.parse_args()

    print('Loading dataset from:', args.db)
    df = build_dataset_from_json(args.db)
    print('Built dataset with rows:', len(df))

    if args.train:
        print('Training models...')
        reg, clf, metrics = train_and_evaluate(df, args.model_dir, test_size=args.test_size)
        print('Training completed. Metrics:', metrics)

    if args.predict:
        data = load_json(args.db)
        rounds = get_rounds_list(data)
        season_driver_points = {}
        constructors_points = {}
        for r in rounds:
            s = r.get('standings') or (r.get('results') and r['results'].get('standings'))
            if s and isinstance(s, dict):
                for d in s.get('drivers', []) if isinstance(s.get('drivers', []), list) else []:
                    name = d.get('driver') or d.get('Driver') or d.get('name')
                    name = normalize_driver_name(name)
                    pts = d.get('points')
                    if name and pts is not None:
                        try:
                            season_driver_points[name] = float(pts)
                        except Exception:
                            pass
                for c in s.get('constructors', []) if isinstance(s.get('constructors', []), list) else []:
                    team = c.get('team') or c.get('name') or c.get('fullTeam')
                    pts = c.get('points')
                    if team and pts is not None:
                        try:
                            constructors_points[team] = float(pts)
                        except Exception:
                            pass

        # pick round
        if args.round is None:
            target_round = rounds[-1]
        else:
            found = None
            for r in rounds:
                if r.get('round') == args.round or r.get('Round') == args.round:
                    found = r
                    break
            if not found:
                idx = args.round - 1
                if 0 <= idx < len(rounds):
                    found = rounds[idx]
            if not found:
                raise ValueError('Round not found in JSON')
            target_round = found

        reg, clf = load_models(args.model_dir)
        preds = predict_for_round(target_round, reg, clf, season_driver_points, constructors_points, topk=args.topk)
        print(f"Top {args.topk} predictions for round {target_round.get('round') or target_round.get('_key') or 'unknown'}:")
        for i, p in enumerate(preds, 1):
            print(f"{i}. {p['driver']} ({p.get('team')}) - predicted_pos={p['pred_pos']:.2f}, podium_prob={p.get('pred_podium_prob')}")

if __name__ == '__main__':
    main()