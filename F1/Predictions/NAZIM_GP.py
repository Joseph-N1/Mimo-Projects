"""
NAZIM GP - 2025 F1 race predictor with ML training & evaluation

Features added in this version:
- Full dataset extractor from your 2025 JSON (robust to a few structure variants).
- Feature engineering (qualifying position, start, practice mean, fastest lap rank, pitstops, season driver points, constructor points, track length, safety cars, weather encoding).
- Two ML models:
    * RandomForestRegressor -> predicts finishing position (lower is better)
    * RandomForestClassifier -> predicts whether a driver finishes on the podium (top-3)
- Train / evaluate pipeline with train/test split and cross-validation reporting.
- Save trained models to disk with joblib.

Usage examples:
  # Train models and save to models/ folder
  python NAZIM_GP.py --db "C:\\Users\\Joseph N Nimyel\\OneDrive\\Documents\\Mimo Projects\\F1\\DataBase\\F1-Seasons-2025.json" --train --model-dir ./models --test-size 0.2

  # Run prediction for a specific round using saved models
  python NAZIM_GP.py --db "..." --round 16 --predict --model-dir ./models --topk 3

Requirements (install into your virtualenv):
  pip install pandas numpy scikit-learn joblib

Notes:
- This script expects driver names to be consistent across sections (qualifying, practice, race). If they differ (e.g. "Max Verstappen" vs "Verstappen, Max"), you should normalize names centrally.
- The modelling here is a reasonable starting point — feature set and models can be improved with more advanced engineering and cross-validation strategies.

"""

import argparse
import json
import os
import math
import statistics
from collections import defaultdict
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
    """Parse times like '1:20.901' into seconds (float)."""
    if not t or not isinstance(t, str):
        return None
    try:
        if ':' in t:
            m, s = t.split(':')
            return float(m) * 60.0 + float(s)
        return float(t)
    except Exception:
        return None


def get_rounds_list(data: Any) -> List[Dict[str, Any]]:
    """Find rounds stored either as a list or as dict keyed by round name.
    Returns a list of round dicts. If the source is a dict keyed by names (e.g. 'italy': {...})
    we copy each entry and add a '_key' field with the original key.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # common containers
        for key in ("races", "Races", "rounds", "Rounds", "data", "season", "events"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # else assume each key is a round
        rounds = []
        for k, v in data.items():
            if isinstance(v, dict):
                copy = dict(v)
                copy['_key'] = k
                rounds.append(copy)
        if rounds:
            return rounds
    raise ValueError('Could not parse rounds container in JSON file')


def find_driver_entry(lst: List[Dict[str, Any]], driver_name: str, aliases: List[str]=None):
    if not isinstance(lst, list):
        return None
    for item in lst:
        # possible keys: 'driver', 'Driver', 'name', 'driverName', 'pos', 'position'
        for key in ('driver', 'Driver', 'name', 'driverName'):
            if key in item and isinstance(item[key], str):
                if item[key].strip().lower() == driver_name.strip().lower():
                    return item
        # sometimes driver is under nested dict
        if 'Driver' in item and isinstance(item['Driver'], dict):
            drv = item['Driver']
            name = (drv.get('givenName') or '') + ' ' + (drv.get('familyName') or '')
            if name.strip().lower() == driver_name.strip().lower():
                return item
    # try aliases if provided
    if aliases:
        for a in aliases:
            res = find_driver_entry(lst, a)
            if res:
                return res
    return None

# ----------------------------- Dataset builder -----------------------------

def build_driver_features_for_round_df(round_entry: Dict[str, Any], season_driver_points_map: Dict[str, float], constructors_map: Dict[str, float]):
    """Return DataFrame rows (list of dicts) for every driver present in the race results of the round."""
    rows = []
    # Y our JSON sample nests results under 'results' then 'race' and 'qualifying' etc.
    results_block = round_entry.get('results') or round_entry

    race_list = results_block.get('race') or []
    if not isinstance(race_list, list):
        race_list = []

    # gather qualifying/practice/pitstops/fastest
    qualifying_list = results_block.get('qualifying') or []
    practice_p1 = results_block.get('p1') or []
    practice_p2 = results_block.get('p2') or []
    practice_p3 = results_block.get('p3') or []
    # some rounds use 'practice' combined
    if 'practice' in round_entry and isinstance(round_entry['practice'], dict):
        # merging p1/p2/p3 if present
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
    weather = round_entry.get('weather') or ''

    for r in race_list:
        driver = r.get('driver') or r.get('Driver') or r.get('driverName') or r.get('name')
        if isinstance(driver, dict):
            driver = (driver.get('givenName','') + ' ' + driver.get('familyName','')).strip()
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

        # qualifying position for this driver
        q = find_driver_entry(qualifying_list, driver)
        row['qual_pos'] = q.get('pos') if q and q.get('pos') is not None else (q.get('position') if q and q.get('position') is not None else None)

        # practice mean from all practice sessions available
        practice_positions = []
        for p_list in (practice_p1, practice_p2, practice_p3):
            ent = find_driver_entry(p_list, driver)
            if ent:
                # sometimes practice lists don't have explicit 'pos' but have 'time'; we can approximate by ordering index
                pos = ent.get('pos') or ent.get('position')
                if pos is None and 'time' in ent:
                    # we won't compute pos here; instead store time in seconds
                    t = parse_time_to_seconds(ent.get('time'))
                    if t is not None:
                        practice_positions.append(t)
                elif pos is not None:
                    practice_positions.append(pos)
        if practice_positions:
            # if measured in times (seconds) lower is better; we'll take mean
            row['practice_mean'] = float(statistics.mean(practice_positions))
        else:
            row['practice_mean'] = None

        # fastest lap rank or lap time
        fl = find_driver_entry(fastest_list, driver)
        if fl:
            row['fastest_lap_time'] = parse_time_to_seconds(fl.get('lapTime') or fl.get('time') or fl.get('lap_time'))
            # store rank if present
            row['fastest_lap_rank'] = fl.get('rank') or fl.get('position')
        else:
            row['fastest_lap_time'] = None
            row['fastest_lap_rank'] = None

        # pitstops count
        pit_entry = None
        if isinstance(pitstops, list):
            for p in pitstops:
                # p may be {driver: 'name', stops: n}
                dname = p.get('driver') or p.get('Driver') or p.get('driverName')
                if isinstance(dname, dict):
                    dname = (dname.get('givenName','') + ' ' + dname.get('familyName','')).strip()
                if dname and dname.strip().lower() == driver.strip().lower():
                    pit_entry = p
                    break
        elif isinstance(pitstops, dict):
            # driver -> list
            if driver in pitstops:
                pit_entry = {'stops': len(pitstops[driver])}
        row['pitstops'] = pit_entry.get('stops') if pit_entry else 0

        # season points for driver
        row['season_points'] = season_driver_points_map.get(driver, None)
        # constructor points (team-level)
        row['constructor_points'] = constructors_map.get(row['team'], None)

        rows.append(row)
    return rows


def build_dataset_from_json(path: str) -> pd.DataFrame:
    data = load_json(path)
    rounds = get_rounds_list(data)

    # build season-level maps (drivers points, constructors points) from any 'standings' found
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
                if isinstance(name, dict):
                    name = (name.get('givenName','') + ' ' + name.get('familyName','')).strip()
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

    # iterate and build rows
    all_rows = []
    for r in rounds:
        rows = build_driver_features_for_round_df(r, season_driver_points, constructors_points)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)

    # Basic cleaning: convert types
    # convert boolean/strings etc.
    # If fastest_lap_time is in seconds or practice_mean in seconds, it's fine. For positions ensure numeric
    for col in ('target_pos', 'start_pos', 'qual_pos', 'pitstops', 'season_points', 'constructor_points', 'laps', 'fastest_lap_rank'):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# ----------------------------- Modelling -----------------------------

def train_and_evaluate(df: pd.DataFrame, model_dir: str, test_size: float = 0.2, random_state: int = 42):
    os.makedirs(model_dir, exist_ok=True)

    # Filter only rows with a target (some DNS/DNF may have null pos)
    df = df[df['target_pos'].notnull()].copy()
    # Feature columns
    numeric_feats = ['qual_pos', 'start_pos', 'practice_mean', 'fastest_lap_time', 'fastest_lap_rank', 'pitstops', 'season_points', 'constructor_points', 'track_length', 'safety_cars', 'laps']
    categorical_feats = ['weather', 'team', 'event_name']

    # target regression: finishing position
    df['target_pos'] = pd.to_numeric(df['target_pos'], errors='coerce')
    # target classification: podium or not
    df['target_podium'] = (df['target_pos'] <= 3).astype(int)

    X = df[numeric_feats + categorical_feats]
    y_reg = df['target_pos']
    y_clf = df['target_podium']

    # train/test split where we stratify by event_name for classifier balancing
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=test_size, random_state=random_state, stratify=X['event_name'] if 'event_name' in X else None)

    # Preprocessing pipelines
    numeric_transform = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
    categorical_transform = Pipeline(steps=[('imputer', SimpleImputer(strategy='constant', fill_value='missing')), ('onehot', OneHotEncoder(handle_unknown='ignore'))])

    preproc = ColumnTransformer(transformers=[
        ('num', numeric_transform, numeric_feats),
        ('cat', categorical_transform, categorical_feats)
    ])

    # Models
    regressor = Pipeline(steps=[('preproc', preproc), ('model', RandomForestRegressor(n_estimators=200, random_state=random_state))])
    classifier = Pipeline(steps=[('preproc', preproc), ('model', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=random_state))])

    # Fit models
    print('Training regressor...')
    regressor.fit(X_train, y_reg_train)
    print('Training classifier...')
    classifier.fit(X_train, y_clf_train)

    # Evaluate regressor
    y_reg_pred = regressor.predict(X_test)
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    rmse = math.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    print(f'Regressor MAE: {mae:.4f}, RMSE: {rmse:.4f}')

    # Evaluate classifier
    y_clf_pred = classifier.predict(X_test)
    acc = accuracy_score(y_clf_test, y_clf_pred)
    prec = precision_score(y_clf_test, y_clf_pred, zero_division=0)
    rec = recall_score(y_clf_test, y_clf_pred, zero_division=0)
    f1 = f1_score(y_clf_test, y_clf_pred, zero_division=0)
    print(f'Classifier accuracy: {acc:.4f}, precision: {prec:.4f}, recall: {rec:.4f}, f1: {f1:.4f}')

    # Cross-validated estimates (optional, smaller folds due to dataset size)
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

    # Save models
    reg_path = os.path.join(model_dir, 'nazim_regressor.joblib')
    clf_path = os.path.join(model_dir, 'nazim_classifier.joblib')
    joblib.dump(regressor, reg_path)
    joblib.dump(classifier, clf_path)
    print(f'Saved regressor to: {reg_path}')
    print(f'Saved classifier to: {clf_path}')

    # Return trained objects and test metrics for possible programmatic use
    metrics = {
        'regression': {'mae': mae, 'rmse': rmse},
        'classification': {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}
    }
    return regressor, classifier, metrics

# ----------------------------- Prediction utilities -----------------------------

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
    numeric_feats = ['qual_pos', 'start_pos', 'practice_mean', 'fastest_lap_time', 'fastest_lap_rank', 'pitstops', 'season_points', 'constructor_points', 'track_length', 'safety_cars', 'laps']
    categorical_feats = ['weather', 'team', 'event_name']
    features = df[numeric_feats + categorical_feats]
    # some drivers may have missing features; the pipeline handles this

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

    # rank by predicted position (lower predicted pos -> better)
    df_sorted = df.sort_values(by='pred_pos')
    # return topk drivers
    return df_sorted.head(topk)[['driver', 'team', 'pred_pos', 'pred_podium_prob']].to_dict(orient='records')

# ----------------------------- CLI -----------------------------

def main():
    parser = argparse.ArgumentParser(description='NAZIM GP - 2025 predictor and trainer')
    parser.add_argument('--db', type=str, required=False, default="C:\\Users\\Joseph N Nimyel\\OneDrive\\Documents\\Mimo Projects\\F1\\DataBase\\F1-Seasons-2025.json")
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
        # prepare season-level maps again to pass into predictor
        data = load_json(args.db)
        rounds = get_rounds_list(data)
        season_driver_points = {}
        constructors_points = {}
        for r in rounds:
            s = r.get('standings') or (r.get('results') and r['results'].get('standings'))
            if s and isinstance(s, dict):
                for d in s.get('drivers', []) if isinstance(s.get('drivers', []), list) else []:
                    name = d.get('driver') or d.get('Driver') or d.get('name')
                    if isinstance(name, dict):
                        name = (name.get('givenName','') + ' ' + name.get('familyName','')).strip()
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

        # pick round entry
        if args.round is None:
            target_round = rounds[-1]
        else:
            # try to find by 'round' field
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
