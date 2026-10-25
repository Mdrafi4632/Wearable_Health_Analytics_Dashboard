import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

# Set MONGO_URI as an environment variable -- never hard-code it.
db = MongoClient(os.environ["MONGO_URI"])["health_data"]
DATA = Path(__file__).parent / "data"

SOURCES = {
    "daily_activity": ["peoples_data/daily_activity_1.csv", "peoples_data/daily_activity_2.csv"],
    "sleep_day": ["peoples_data/sleep_day.csv"],
    "physiologicals_rafi": ["rafi_data/physiologicals_rafi.csv"],
    "sleeps_rafi": ["rafi_data/sleeps_rafi.csv"],
    "workouts_rafi": ["rafi_data/workouts_rafi.csv"],
}

for name, files in SOURCES.items():
    df = pd.concat([pd.read_csv(DATA / f, encoding="utf-8-sig") for f in files], ignore_index=True)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
    df = df.astype(object).where(df.notna(), None)
    db[name].drop()  # re-runnable: replace instead of duplicating
    db[name].insert_many(df.to_dict(orient="records"))
    print(f"Loaded {len(df)} documents into '{name}'")
