import os
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt
from pymongo import MongoClient

st.set_page_config(page_title="Health Analytics Dashboard", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
SOURCES = {
    "daily_activity": ["peoples_data/daily_activity_1.csv", "peoples_data/daily_activity_2.csv"],
    "sleep_day": ["peoples_data/sleep_day.csv"],
    "physiologicals_rafi": ["rafi_data/physiologicals_rafi.csv"],
    "sleeps_rafi": ["rafi_data/sleeps_rafi.csv"],
    "workouts_rafi": ["rafi_data/workouts_rafi.csv"],
}


def mongo_uri():
    try:
        return st.secrets["MONGO_URI"]
    except Exception:
        return os.getenv("MONGO_URI")


@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load_all():
    """Read from MongoDB Atlas; fall back to bundled CSVs if it is unreachable."""
    uri = mongo_uri()
    if uri:
        try:
            db = MongoClient(uri, serverSelectionTimeoutMS=5000)["health_data"]
            dfs = {c: pd.DataFrame(list(db[c].find({}, {"_id": 0}))) for c in SOURCES}
            if all(not d.empty for d in dfs.values()):
                return dfs, "MongoDB Atlas"
        except Exception:
            pass
    dfs = {
        c: pd.concat([pd.read_csv(DATA_DIR / f, encoding="utf-8-sig") for f in files], ignore_index=True)
        for c, files in SOURCES.items()
    }
    return dfs, "bundled CSV files"


dfs, data_source = load_all()
for df in dfs.values():
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

daily_activity, sleep_day = dfs["daily_activity"], dfs["sleep_day"]
physiologicals_rafi, sleeps_rafi, workouts_rafi = dfs["physiologicals_rafi"], dfs["sleeps_rafi"], dfs["workouts_rafi"]


# ---------- Style ----------
ACCENT, MUTED, LINE = "#C6F432", "#8A9099", "#1E232B"
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;800&family=Inter:wght@400;500&display=swap');
.block-container{padding-top:3.5rem;max-width:1200px}
.stMarkdown p,.stMarkdown li{font-family:'Inter',sans-serif}
.topbar{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font:600 13px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#8A9099;border-bottom:1px solid #1E232B;padding-bottom:12px}
.topbar b{color:#F2F4F7}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#C6F432;margin-right:8px}
.eyebrow{font:600 14px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.25em;color:#C6F432;text-transform:uppercase;margin:32px 0 10px}
.hero{font:800 clamp(44px,7.5vw,92px)/.92 'Barlow Condensed','Arial Narrow',sans-serif;text-transform:uppercase;color:#F2F4F7;margin:36px 0 0}
.hero span{color:#C6F432}
.lede{color:#8A9099;font:400 17px/1.6 'Inter';margin:20px 0 36px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:#1E232B;border:1px solid #1E232B;border-radius:12px;overflow:hidden}
.stat{background:#0F1217;padding:20px 22px}
.stat .v{font:800 clamp(30px,3.2vw,46px)/1 'Barlow Condensed','Arial Narrow',sans-serif;color:#F2F4F7;white-space:nowrap}.stat .u{font:500 14px 'Inter';color:#8A9099;margin-left:4px}
.stat .l{font:600 12px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#8A9099;margin-top:10px}
.sec{font:600 13px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.22em;text-transform:uppercase;color:#8A9099;margin:52px 0 14px}
.card{border:1px solid #1E232B;border-radius:12px;padding:22px;background:#0F1217;height:100%}
.card h4{font:800 24px 'Barlow Condensed','Arial Narrow',sans-serif;text-transform:uppercase;margin:0 0 6px;color:#F2F4F7;padding:0}
.card p{color:#8A9099;font:400 14px/1.6 'Inter';margin:0}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font:500 13px 'Inter';color:#C9CED6}
.flow span{border:1px solid #2A303A;border-radius:999px;padding:6px 14px}.flow i{color:#C6F432;font-style:normal}
.foot{color:#5C636E;font:400 13px 'Inter';border-top:1px solid #1E232B;padding-top:16px;margin-top:56px}
.ptitle{font:800 clamp(36px,5vw,56px)/1 'Barlow Condensed','Arial Narrow',sans-serif;text-transform:uppercase;color:#F2F4F7;margin:32px 0 0}
.ptitle span{color:#C6F432}
.cmp{font:400 13px/1.5 'Inter';color:#8A9099;margin-top:10px}.cmp b{color:#C6F432;font-weight:500}
.take{border-left:2px solid #C6F432;padding:4px 0 4px 16px;margin:0 0 14px;color:#C9CED6;font:400 15px/1.6 'Inter'}
.stTabs [role="tablist"]{justify-content:safe center}
.stTabs .react-aria-SelectionIndicator,.stTabs [data-baseweb="tab-highlight"]{background-color:#C6F432 !important}
.stTabs [aria-selected="true"] p{color:#C6F432}
.stTabs [role="tab"] p{font:600 15px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.12em;text-transform:uppercase}
</style>""", unsafe_allow_html=True)

def stat_row(items):
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="v">{v}<span class="u">{u}</span></div><div class="l">{l}</div></div>'
        for v, u, l in items) + "</div>", unsafe_allow_html=True)


def section(title, where=st):
    where.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)


def date_range(key, where=st):
    """Return the start date for the chosen range, or None for All."""
    opt = where.radio("Range", ["3M", "6M", "1Y", "All"], index=3, horizontal=True, key=key)
    return None if opt == "All" else {"3M": 91, "6M": 182, "1Y": 365}[opt]


def numeric(df, cols):
    df = df.rename(columns=cols)
    for c in cols.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df.dropna(subset=["Date"]).sort_values("Date")


def show(chart, h=280, where=st):
    where.altair_chart(
        chart.properties(height=h, background="transparent").configure_view(stroke=None)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=LINE, domainColor=LINE, tickColor=LINE,
                        labelFont="Inter", titleFont="Inter", titleFontWeight=500),
        width="stretch")


st.markdown(
    f'<div class="topbar"><div><span class="dot"></span><b>Rafi</b></div>'
    f'<div>Source: {data_source}</div></div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["Overview", "Fitbit Activity", "Fitbit Sleep Activity", "WHOOP Activity", "WHOOP Sleep Activity", "Comparisons"])


# TAB 0: Overview
with tabs[0]:
    num = lambda df, c: pd.to_numeric(df[c], errors="coerce")
    phys, slp, wk = physiologicals_rafi, sleeps_rafi, workouts_rafi
    dates = pd.to_datetime(pd.concat([phys["Date"], slp["Date"], wk["Date"]]), errors="coerce").dropna()
    years = (dates.max() - dates.min()).days / 365.25
    sleep_h = (num(slp, "Light sleep duration (min)") + num(slp, "Deep duration (min)") + num(slp, "REM duration (min)")).mean() / 60
    n_users = daily_activity["Id"].nunique()

    st.markdown(
        f"""<div class="hero">From <span>Data</span> to <span>Discovery</span></div>
        <p class="lede">{round(years)} years of personal WHOOP data and {n_users} Fitbit users, unified in MongoDB Atlas and analyzed with Python.</p>""",
        unsafe_allow_html=True,
    )

    stats = [
        (f"{num(phys, 'Heart rate variability (ms)').mean():.0f}", "ms", "Avg HRV"),
        (f"{num(phys, 'Resting heart rate (bpm)').mean():.0f}", "bpm", "Resting HR"),
        (f"{num(slp, 'Sleep performance %').mean():.0f}", "%", "Sleep performance"),
        (f"{sleep_h:.1f}", "h", "Avg sleep"),
        (f"{num(phys, 'Day Strain').mean():.1f}", "", "Day strain"),
        (f"{len(wk):,}", "", "Workouts logged"),
    ]
    st.markdown(
        '<div class="stats">' + "".join(
            f'<div class="stat"><div class="v">{v}<span class="u">{u}</span></div><div class="l">{l}</div></div>'
            for v, u, l in stats) + "</div>",
        unsafe_allow_html=True,
    )

    # Sources
    st.markdown('<div class="sec">Data sources</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="card"><h4>WHOOP &middot; Personal</h4><p>{len(phys):,} days of HRV, resting HR, strain, SpO2 and skin temp, '
                f'{len(slp):,} nights of sleep stages and {len(wk):,} workouts.</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><h4>Fitbit &middot; Public</h4><p>{n_users} anonymized users from 2016: {len(daily_activity):,} days of steps, '
                f'calories and intensity minutes, plus {len(sleep_day):,} sleep logs.</p></div>', unsafe_allow_html=True)

    # Pipeline
    st.markdown('<div class="sec">Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="flow"><span>CSV exports</span><i>&rarr;</i><span>Pandas ETL</span><i>&rarr;</i>'
                '<span>MongoDB Atlas &middot; 5 collections</span><i>&rarr;</i><span>Streamlit + Altair</span></div>',
                unsafe_allow_html=True)

    # Raw data, tucked away
    st.markdown('<div class="sec">Raw data</div>', unsafe_allow_html=True)
    with st.expander("Browse collections"):
        coll = st.selectbox("Collection", list(dfs), key="raw_coll", label_visibility="collapsed")
        st.dataframe(dfs[coll], width="stretch", hide_index=True)

    st.markdown('<div class="foot">Md Rafiul Islam Rafi &nbsp;&middot;&nbsp; Fordham University &nbsp;&middot;&nbsp; CISC 5640 NoSQL Database Systems</div>',
                unsafe_allow_html=True)





# TAB 1: Fitbit Activity
with tabs[1]:
    fa = daily_activity.copy()
    fa["Date"] = pd.to_datetime(fa["Date"], errors="coerce")
    for c in ["TotalSteps", "TotalDistance", "HighIntensityMinutes", "ModerateIntensityMinutes",
              "LowIntensityMinutes", "RestMinutes", "Calories"]:
        fa[c] = pd.to_numeric(fa[c], errors="coerce")
    fa = fa[fa["Calories"] > 0].dropna(subset=["Date"])  # 0 kcal = device not worn
    fa = fa.drop_duplicates(["Id", "Date"], keep="last").sort_values("Date")
    users = sorted(fa["Id"].unique())

    st.markdown(
        f'<div class="ptitle">Fitbit <span>Activity</span></div>'
        f'<p class="lede">{len(users)} anonymized users &middot; {fa.Date.min():%b %d} to {fa.Date.max():%b %d, %Y}. '
        f'Pick a user to see their daily movement.</p>', unsafe_allow_html=True)

    pick, _ = st.columns([1, 3])
    user = pick.selectbox("User ID", users, key="activity_user")
    u = fa[fa["Id"] == user]
    best = u.loc[u["TotalSteps"].idxmax()]

    stat_row([
        (f"{u.TotalSteps.mean():,.0f}", "", "Avg daily steps"),
        (f"{u.Calories.mean():,.0f}", "kcal", "Avg calories"),
        (f"{(u.HighIntensityMinutes + u.ModerateIntensityMinutes).mean():.0f}", "min", "Active / day"),
        (f"{(u.TotalSteps >= 10000).mean() * 100:.0f}", "%", "Days over 10k"),
        (f"{best.TotalSteps:,.0f}", "", f"Best day &middot; {best.Date:%b %d}"),
        (f"{len(u)}", "", "Days tracked"),
    ])

    # Daily steps with 10k goal
    section("Daily steps &middot; dashed line = 10k goal")
    bars = alt.Chart(u).mark_bar(color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %d", grid=False)),
        y=alt.Y("TotalSteps:Q", title=None),
        tooltip=[alt.Tooltip("Date:T", format="%a, %b %d"), alt.Tooltip("TotalSteps:Q", format=",", title="Steps")])
    goal = pd.DataFrame({"y": [10000], "t": ["10k goal"]})
    rule = alt.Chart(goal).mark_rule(color=MUTED, strokeDash=[4, 4]).encode(y="y:Q")
    show(bars + rule)

    left, right = st.columns(2, gap="large")

    # Steps vs calories
    section("Steps vs calories", left)
    scatter = alt.Chart(u).mark_circle(color=ACCENT, size=70, opacity=0.75).encode(
        x=alt.X("TotalSteps:Q", title="Steps", scale=alt.Scale(zero=False)),
        y=alt.Y("Calories:Q", title="Calories", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("Date:T", format="%b %d"), alt.Tooltip("TotalSteps:Q", format=","), "Calories:Q"])
    show(scatter, 300, left)

    # Average active minutes
    section("Average day &middot; active minutes", right)
    mins = pd.DataFrame({
        "Intensity": ["High", "Moderate", "Low"],
        "Minutes": [u.HighIntensityMinutes.mean(), u.ModerateIntensityMinutes.mean(), u.LowIntensityMinutes.mean()]})
    y = alt.Y("Intensity:N", title=None, sort=None, axis=alt.Axis(labelFontSize=13, domain=False, ticks=False))
    hbar = alt.Chart(mins).mark_bar(color=ACCENT, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=28).encode(
        x=alt.X("Minutes:Q", title=None, axis=None), y=y, tooltip=["Intensity", alt.Tooltip("Minutes:Q", format=".0f")])
    vals = alt.Chart(mins).mark_text(align="left", dx=6, color="#F2F4F7", font="Inter", fontSize=13).encode(
        x="Minutes:Q", y=y, text=alt.Text("Minutes:Q", format=".0f"))
    show(hbar + vals, 230, right)
    right.caption(f"Plus {u.RestMinutes.mean() / 60:.1f} h of rest / sedentary time per day.")





# TAB 2: Fitbit Sleep
with tabs[2]:
    fs = sleep_day.copy()
    fs["Date"] = pd.to_datetime(fs["SleepDay"], errors="coerce")
    fs["Asleep"] = pd.to_numeric(fs["TotalMinutesAsleep"], errors="coerce") / 60
    fs["InBed"] = pd.to_numeric(fs["TotalTimeInBed"], errors="coerce") / 60
    fs = fs.dropna(subset=["Date", "Asleep"]).drop_duplicates(["Id", "Date"], keep="last").sort_values("Date")
    fs["Efficiency"] = fs["Asleep"] / fs["InBed"] * 100
    fs["DayType"] = fs["Date"].dt.weekday.map(lambda d: "Weekend" if d >= 5 else "Weekday")
    users = sorted(fs["Id"].unique())

    st.markdown(
        f'<div class="ptitle">Fitbit <span>Sleep</span></div>'
        f'<p class="lede">{len(users)} users with sleep logs &middot; {fs.Date.min():%b %d} to {fs.Date.max():%b %d, %Y}. '
        f'Pick a user to see their nights.</p>', unsafe_allow_html=True)

    pick, _ = st.columns([1, 3])
    user = pick.selectbox("User ID", users, key="sleep_user")
    u = fs[fs["Id"] == user]
    best = u.loc[u["Asleep"].idxmax()]

    stat_row([
        (f"{u.Asleep.mean():.1f}", "h", "Avg sleep"),
        (f"{u.InBed.mean():.1f}", "h", "Avg time in bed"),
        (f"{u.Efficiency.mean():.0f}", "%", "Sleep efficiency"),
        (f"{(u.Asleep >= 7).mean() * 100:.0f}", "%", "Nights over 7h"),
        (f"{best.Asleep:.1f}", "h", f"Best night &middot; {best.Date:%b %d}"),
        (f"{len(u)}", "", "Nights logged"),
    ])

    # Nightly sleep vs time in bed
    section("Nightly sleep &middot; <span style='color:#C6F432'>asleep</span> vs in bed &middot; dashed line = 7h")
    x = alt.X("Date:T", title=None, axis=alt.Axis(format="%b %d", grid=False))
    tip = [alt.Tooltip("Date:T", format="%a, %b %d"), alt.Tooltip("Asleep:Q", format=".1f", title="Asleep (h)"),
           alt.Tooltip("InBed:Q", format=".1f", title="In bed (h)")]
    bed = alt.Chart(u).mark_bar(color="#4A525E", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=x, y=alt.Y("InBed:Q", title=None), tooltip=tip)
    slept = alt.Chart(u).mark_bar(color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=x, y="Asleep:Q", tooltip=tip)
    rule = alt.Chart(pd.DataFrame({"y": [7]})).mark_rule(color=MUTED, strokeDash=[4, 4]).encode(y="y:Q")
    show(bed + slept + rule)

    left, right = st.columns(2, gap="large")

    # Weekday vs weekend
    section("Weekday vs weekend &middot; avg hours", left)
    wk_df = u.groupby("DayType", as_index=False)["Asleep"].mean()
    y = alt.Y("DayType:N", title=None, sort=["Weekday", "Weekend"], axis=alt.Axis(labelFontSize=13, domain=False, ticks=False))
    hbar = alt.Chart(wk_df).mark_bar(color=ACCENT, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=32).encode(
        x=alt.X("Asleep:Q", title=None, axis=None), y=y, tooltip=["DayType", alt.Tooltip("Asleep:Q", format=".1f")])
    vals = alt.Chart(wk_df).mark_text(align="left", dx=6, color="#F2F4F7", font="Inter", fontSize=13).encode(
        x="Asleep:Q", y=y, text=alt.Text("Asleep:Q", format=".1f"))
    show(hbar + vals, 200, left)

    # Efficiency over time
    section("Sleep efficiency &middot; asleep / in bed", right)
    eff = alt.Chart(u).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %d", grid=False)),
        y=alt.Y("Efficiency:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format=".0f")))
    show(eff.mark_line(color=ACCENT, strokeWidth=2) +
         eff.mark_circle(color=ACCENT, size=50).encode(tooltip=[alt.Tooltip("Date:T", format="%b %d"), alt.Tooltip("Efficiency:Q", format=".0f", title="Efficiency %")]),
         200, right)





# TAB 3: WHOOP Activity
with tabs[3]:
    ph = numeric(physiologicals_rafi, {"Heart rate variability (ms)": "HRV", "Resting heart rate (bpm)": "RHR",
                                       "Day Strain": "Strain", "Energy burned (cal)": "Energy",
                                       "Blood oxygen %": "SpO2", "Skin temperature": "Skin"})
    wo = numeric(workouts_rafi, {"Activity Strain": "Strain", "Duration (min)": "Duration", "Energy burned (cal)": "Energy"})

    st.markdown(
        f'<div class="ptitle">WHOOP <span>Activity</span></div>'
        f'<p class="lede">{len(ph):,} days of recovery and strain plus {len(wo)} workouts &middot; '
        f'{ph.Date.min():%b %Y} to {ph.Date.max():%b %Y}.</p>', unsafe_allow_html=True)

    days = date_range("whoop_act_range")
    if days:
        start = ph.Date.max() - pd.Timedelta(days=days)
        ph, wo = ph[ph.Date >= start], wo[wo.Date >= start]

    stat_row([
        (f"{ph.HRV.mean():.0f}", "ms", "Avg HRV"),
        (f"{ph.RHR.mean():.0f}", "bpm", "Resting HR"),
        (f"{ph.Strain.mean():.1f}", "", "Day strain"),
        (f"{ph.Energy.mean():,.0f}", "kcal", "Energy / day"),
        (f"{ph.SpO2.mean():.1f}", "%", "Blood oxygen"),
        (f"{len(wo)}", "", "Workouts"),
    ])

    # HRV: daily dots + 30-day average
    ph = ph.set_index("Date")
    ph["HRV30"] = ph["HRV"].rolling("30D", min_periods=3).mean()
    ph["RHR30"] = ph["RHR"].rolling("30D", min_periods=3).mean()
    ph = ph.reset_index()

    def trend(col, avg, label, where=st, h=280):
        base = alt.Chart(ph).encode(x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %y", grid=False)))
        dots = base.mark_circle(color=ACCENT, opacity=0.25, size=22).encode(
            y=alt.Y(f"{col}:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("Date:T", format="%b %d, %Y"), alt.Tooltip(f"{col}:Q", title=label)])
        line = base.mark_line(color=ACCENT, strokeWidth=2.5).encode(y=alt.Y(f"{avg}:Q", scale=alt.Scale(zero=False)))
        show(dots + line, h, where)

    section("HRV (ms) &middot; daily dots, 30-day average line")
    trend("HRV", "HRV30", "HRV (ms)")

    left, right = st.columns(2, gap="large")
    section("Resting heart rate (bpm) &middot; 30-day average", left)
    trend("RHR", "RHR30", "RHR (bpm)", left, 240)

    section("Day strain vs energy burned", right)
    show(alt.Chart(ph).mark_circle(color=ACCENT, size=40, opacity=0.6).encode(
        x=alt.X("Strain:Q", title="Day strain"),
        y=alt.Y("Energy:Q", title="kcal", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("Date:T", format="%b %d, %Y"), "Strain:Q", alt.Tooltip("Energy:Q", format=",.0f")]), 240, right)

    # Workouts by activity
    section("Workouts &middot; avg strain by activity, top 8 by sessions")
    if wo.empty:
        st.caption("No workouts in this range.")
    else:
        g = (wo.groupby("Activity name").agg(n=("Strain", "size"), strain=("Strain", "mean"), mins=("Duration", "mean"))
               .nlargest(8, "n").reset_index())
        g["label"] = g.apply(lambda r: f"{r.strain:.1f}  \u00b7  {r.n} sessions", axis=1)
        y = alt.Y("Activity name:N", title=None, sort="-x", axis=alt.Axis(labelFontSize=13, domain=False, ticks=False))
        bars = alt.Chart(g).mark_bar(color=ACCENT, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=22).encode(
            x=alt.X("strain:Q", title=None, axis=None), y=y,
            tooltip=["Activity name", alt.Tooltip("n:Q", title="Sessions"), alt.Tooltip("strain:Q", format=".1f", title="Avg strain"),
                     alt.Tooltip("mins:Q", format=".0f", title="Avg minutes")])
        txt = alt.Chart(g).mark_text(align="left", dx=6, color="#F2F4F7", font="Inter", fontSize=12).encode(x="strain:Q", y=y, text="label:N")
        show(bars + txt, 34 * len(g) + 20)





# TAB 4: WHOOP Sleep
with tabs[4]:
    STAGE_COLORS = alt.Scale(domain=["Deep", "REM", "Light"], range=[ACCENT, "#5AC8FA", "#4A525E"])
    sl = numeric(sleeps_rafi, {"Light sleep duration (min)": "Light", "Deep duration (min)": "Deep", "REM duration (min)": "REM",
                               "Sleep need (min)": "Need", "Sleep debt (min)": "Debt", "Sleep performance %": "Perf",
                               "Sleep efficiency %": "Eff", "Sleep consistency %": "Cons"})
    sl["Total"] = sl[["Light", "Deep", "REM"]].sum(axis=1, min_count=3)

    st.markdown(
        f'<div class="ptitle">WHOOP <span>Sleep</span></div>'
        f'<p class="lede">{len(sl):,} nights of sleep stages, need and performance &middot; '
        f'{sl.Date.min():%b %Y} to {sl.Date.max():%b %Y}.</p>', unsafe_allow_html=True)

    days = date_range("whoop_sleep_range")
    if days:
        sl = sl[sl.Date >= sl.Date.max() - pd.Timedelta(days=days)]

    stat_row([
        (f"{sl.Total.mean() / 60:.1f}", "h", "Avg sleep"),
        (f"{sl.Need.mean() / 60:.1f}", "h", "Sleep need"),
        (f"{sl.Perf.mean():.0f}", "%", "Performance"),
        (f"{sl.Eff.mean():.0f}", "%", "Efficiency"),
        (f"{sl.Cons.mean():.0f}", "%", "Consistency"),
        (f"{sl.Debt.mean():.0f}", "min", "Avg sleep debt"),
    ])

    # Stages over time (nightly for 3M, weekly averages otherwise)
    nightly = days == 91
    st_df = sl.set_index("Date")[["Deep", "REM", "Light"]]
    if not nightly:
        st_df = st_df.resample("W").mean()
    st_df = (st_df.dropna() / 60).reset_index().melt("Date", var_name="Stage", value_name="Hours")
    st_df["order"] = st_df["Stage"].map({"Deep": 0, "REM": 1, "Light": 2})
    section(f"Sleep stages (h) &middot; {'nightly' if nightly else 'weekly average'} &middot; "
            "<span style='color:#C6F432'>Deep</span> / <span style='color:#5AC8FA'>REM</span> / "
            "<span style='color:#A0A7B2'>Light</span>")
    show(alt.Chart(st_df).mark_bar().encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %y", grid=False)),
        y=alt.Y("Hours:Q", title=None, stack="zero"),
        color=alt.Color("Stage:N", scale=STAGE_COLORS, legend=None),
        order="order:Q",
        tooltip=[alt.Tooltip("Date:T", format="%b %d, %Y"), "Stage:N", alt.Tooltip("Hours:Q", format=".1f")]))

    left, right = st.columns(2, gap="large")

    section("Sleep performance % &middot; monthly average", left)
    perf = sl.set_index("Date")["Perf"].resample("MS").mean().dropna().reset_index()
    show(alt.Chart(perf).mark_bar(color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %y", grid=False)),
        y=alt.Y("Perf:Q", title=None, scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("Date:T", format="%B %Y"), alt.Tooltip("Perf:Q", format=".0f", title="Performance %")]), 240, left)

    section("Average night &middot; minutes per stage", right)
    avg = pd.DataFrame({"Stage": ["Deep", "REM", "Light"], "Minutes": [sl.Deep.mean(), sl.REM.mean(), sl.Light.mean()]})
    y = alt.Y("Stage:N", title=None, sort=None, axis=alt.Axis(labelFontSize=13, domain=False, ticks=False))
    show(alt.Chart(avg).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=28).encode(
            x=alt.X("Minutes:Q", title=None, axis=None), y=y,
            color=alt.Color("Stage:N", scale=STAGE_COLORS, legend=None),
            tooltip=["Stage", alt.Tooltip("Minutes:Q", format=".0f")]) +
         alt.Chart(avg).mark_text(align="left", dx=6, color="#F2F4F7", font="Inter", fontSize=13).encode(
            x="Minutes:Q", y=y, text=alt.Text("Minutes:Q", format=".0f")), 240, right)





# TAB 5: Rafi vs the Fitbit cohort
with tabs[5]:
    RAFI, COHORT = ACCENT, "#8A9099"
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Fitbit cohort: one average per user, so every user counts equally
    fa = daily_activity.copy()
    fa["Calories"] = pd.to_numeric(fa["Calories"], errors="coerce")
    fa = fa[fa["Calories"] > 0]
    fs = sleep_day.copy()
    fs["Date"] = pd.to_datetime(fs["SleepDay"], errors="coerce")
    fs["Hours"] = pd.to_numeric(fs["TotalMinutesAsleep"], errors="coerce") / 60
    fs["Eff"] = fs["Hours"] * 60 / pd.to_numeric(fs["TotalTimeInBed"], errors="coerce") * 100
    fs = fs.dropna(subset=["Date", "Hours"])
    users = pd.DataFrame({"Calories": fa.groupby("Id")["Calories"].mean(),
                          "Hours": fs.groupby("Id")["Hours"].mean(),
                          "Eff": fs.groupby("Id")["Eff"].mean()})

    # Rafi (WHOOP)
    rp = numeric(physiologicals_rafi, {"Energy burned (cal)": "Calories"})
    rp = rp[rp["Calories"] > 0]
    rs = numeric(sleeps_rafi, {"Light sleep duration (min)": "Light", "Deep duration (min)": "Deep",
                               "REM duration (min)": "REM", "Sleep efficiency %": "Eff", "Sleep need (min)": "Need"})
    rs["Hours"] = rs[["Light", "Deep", "REM"]].sum(axis=1, min_count=3) / 60
    rs = rs.dropna(subset=["Hours"])
    rafi = {"Calories": rp["Calories"].mean(), "Hours": rs["Hours"].mean(), "Eff": rs["Eff"].mean()}

    def weekend_gain(d):
        m = d.groupby(d["Date"].dt.weekday >= 5)["Hours"].mean()
        return m.get(True, float("nan")) - m.get(False, float("nan"))

    nights = fs.groupby("Id")["Hours"]
    users["SD"] = nights.std()[nights.count() >= 5]
    users["Weekend"] = fs.groupby("Id")[["Date", "Hours"]].apply(weekend_gain)
    rafi["SD"], rafi["Weekend"] = rs["Hours"].std(), weekend_gain(rs)

    def rank(m):
        if m == "SD":
            pct = (users[m].dropna() > rafi[m]).mean() * 100
            return f"more consistent than {pct:.0f}%" if pct >= 50 else f"less consistent than {100 - pct:.0f}%"
        pct = (users[m].dropna() < rafi[m]).mean() * 100
        return f"higher than {pct:.0f}%" if pct >= 50 else f"lower than {100 - pct:.0f}%"

    st.markdown(
        f'<div class="ptitle">Rafi <span>vs</span> the Cohort</div>'
        f'<p class="lede">Two years of personal WHOOP data next to {len(users)} Fitbit users. '
        f'Different people, years and devices, so read this as context, not a contest.</p>', unsafe_allow_html=True)

    # Head-to-head cards
    seven_r, seven_c = (rs.Hours >= 7).mean() * 100, (fs.Hours >= 7).mean() * 100
    cards = [
        ("Calories / day", f"{rafi['Calories']:,.0f}", "kcal", f"Cohort avg {users.Calories.mean():,.0f} &middot; <b>{rank('Calories')} of users</b>"),
        ("Sleep / night", f"{rafi['Hours']:.1f}", "h", f"Cohort avg {users.Hours.mean():.1f} h &middot; <b>{rank('Hours')} of users</b>"),
        ("Sleep efficiency", f"{rafi['Eff']:.0f}", "%", f"Cohort avg {users.Eff.mean():.0f}% &middot; <b>{rank('Eff')} of users</b>"),
        ("Nights over 7 h", f"{seven_r:.0f}", "%", f"Cohort {seven_c:.0f}% of nights"),
    ]
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="l" style="margin:0 0 10px">{l}</div><div class="v">{v}<span class="u">{u}</span></div>'
        f'<div class="cmp">{c}</div></div>' for l, v, u, c in cards) + "</div>", unsafe_allow_html=True)

    # Key takeaways
    under5_r, under5_c = (rs.Hours < 5).mean() * 100, (fs.Hours < 5).mean() * 100
    gap = rs["Need"].mean() / 60 - rafi["Hours"]
    fa["Date"] = pd.to_datetime(fa["Date"], errors="coerce").dt.normalize()
    fa["TotalSteps"] = pd.to_numeric(fa["TotalSteps"], errors="coerce")
    link_c = fa.merge(fs.assign(Date=fs["Date"].dt.normalize()), on=["Id", "Date"])[["TotalSteps", "Hours"]].dropna()
    rstrain = numeric(physiologicals_rafi, {"Day Strain": "Strain"})[["Date", "Strain"]]
    link_r = rstrain.merge(rs[["Date", "Hours"]], on="Date").dropna()
    r_c, r_r = link_c["TotalSteps"].corr(link_c["Hours"]), link_r["Strain"].corr(link_r["Hours"])
    section("Key takeaways")
    for t in [
        f"Rafi burns <b>{rafi['Calories'] - users.Calories.mean():,.0f} kcal/day more</b> than the average Fitbit user, "
        f"but sleeps <b>{users.Hours.mean() - rafi['Hours']:.1f} h less</b> per night.",
        f"<b>{under5_r:.0f}%</b> of Rafi's nights are under 5 hours, compared with <b>{under5_c:.0f}%</b> for the cohort.",
        f"Sleep efficiency is {rank('Eff')} of users, so the gap is <b>time asleep</b>, not restless sleep.",
        f"WHOOP estimates a need of <b>{rs['Need'].mean() / 60:.1f} h</b>, about <b>{gap:.1f} h</b> more than Rafi actually sleeps.",
        f"Rafi's sleep swings by <b>&plusmn;{rafi['SD']:.1f} h</b> night to night (cohort median &plusmn;{users.SD.median():.1f} h), "
        f"<b>{rank('SD')} of users</b>.",
        f"The cohort sleeps <b>{users.Weekend.median():+.1f} h</b> extra on weekends (median); Rafi <b>{rafi['Weekend']:+.1f} h</b>.",
        f"Harder days don't mean more sleep: <b>r = {r_r:.2f}</b> for Rafi (strain vs sleep), "
        f"<b>r = {r_c:.2f}</b> for the cohort (steps vs sleep).",
    ]:
        st.markdown(f'<div class="take">{t}</div>', unsafe_allow_html=True)

    # Where Rafi ranks
    section(f"Where Rafi ranks &middot; <span style='color:{COHORT}'>each dot = one Fitbit user</span>, "
            f"<span style='color:{RAFI}'>lime = Rafi</span>")
    for m, label, fmt in [("Calories", "Calories / day", ",.0f"), ("Hours", "Sleep hours / night", ".1f"), ("Eff", "Sleep efficiency %", ".0f"),
                          ("SD", "Night-to-night variation (h)", ".1f"), ("Weekend", "Weekend extra sleep (h)", "+.1f")]:
        l, r = st.columns([1, 3])
        l.markdown(f'<div class="stat" style="background:none;padding:14px 0"><div class="l" style="margin:0">{label}</div>'
                   f'<div class="cmp" style="margin-top:6px"><b>{rank(m).capitalize()}</b></div></div>', unsafe_allow_html=True)
        cohort = users[[m]].dropna().reset_index()
        me = pd.DataFrame({m: [rafi[m]], "t": ["Rafi"]})
        x = alt.X(f"{m}:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format=fmt, grid=False))
        dots = alt.Chart(cohort).mark_circle(color=COHORT, size=90, opacity=0.5).encode(
            x=x, tooltip=[alt.Tooltip("Id:N", title="Fitbit user"), alt.Tooltip(f"{m}:Q", format=fmt)])
        mine = alt.Chart(me).mark_circle(color=RAFI, size=220, stroke="#0B0D10", strokeWidth=2).encode(
            x=x, tooltip=["t:N", alt.Tooltip(f"{m}:Q", format=fmt)])
        tag = alt.Chart(me).mark_text(color=RAFI, dy=-20, font="Inter", fontWeight=600, fontSize=13).encode(x=x, text="t:N")
        show(dots + mine + tag, 100, r)

    left, right = st.columns(2, gap="large")

    # Nights by sleep length
    section(f"Nights by sleep length &middot; <span style='color:{RAFI}'>Rafi</span> vs <span style='color:{COHORT}'>cohort</span>", left)
    bins, labels = [0, 5, 6, 7, 8, 24], ["<5 h", "5-6 h", "6-7 h", "7-8 h", "8 h+"]
    dist = pd.concat([
        pd.cut(rs.Hours, bins, labels=labels).value_counts(normalize=True).rename("Share").reset_index().assign(Who="Rafi"),
        pd.cut(fs.Hours, bins, labels=labels).value_counts(normalize=True).rename("Share").reset_index().assign(Who="Cohort")])
    dist.columns = ["Bucket", "Share", "Who"]
    who = alt.Scale(domain=["Rafi", "Cohort"], range=[RAFI, COHORT])
    show(alt.Chart(dist).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Bucket:N", title=None, sort=labels, axis=alt.Axis(labelAngle=0, grid=False)),
        xOffset=alt.XOffset("Who:N", sort=["Rafi", "Cohort"]),
        y=alt.Y("Share:Q", title=None, axis=alt.Axis(format="%")),
        color=alt.Color("Who:N", scale=who, legend=None),
        tooltip=["Who:N", "Bucket:N", alt.Tooltip("Share:Q", format=".0%", title="Share of nights")]), 260, left)

    # Sleep by day of week
    section(f"Sleep by day of week (h) &middot; <span style='color:{RAFI}'>Rafi</span> vs <span style='color:{COHORT}'>cohort</span>", right)
    dow = pd.concat([
        rs.groupby(rs.Date.dt.day_name())["Hours"].mean().rename("Hours").reset_index().assign(Who="Rafi"),
        fs.groupby(fs.Date.dt.day_name())["Hours"].mean().rename("Hours").reset_index().assign(Who="Cohort")])
    dow.columns = ["Day", "Hours", "Who"]
    dow["Day"] = dow["Day"].str[:3]
    base = alt.Chart(dow).encode(
        x=alt.X("Day:N", title=None, sort=[d[:3] for d in DAYS], axis=alt.Axis(labelAngle=0, grid=False)),
        y=alt.Y("Hours:Q", title=None, scale=alt.Scale(zero=False)),
        color=alt.Color("Who:N", scale=who, legend=None))
    show(base.mark_line(strokeWidth=2.5) +
         base.mark_circle(size=60).encode(tooltip=["Who:N", "Day:N", alt.Tooltip("Hours:Q", format=".1f")]), 260, right)

    left, right = st.columns(2, gap="large")

    # Calories by day of week
    section(f"Calories by day of week &middot; <span style='color:{RAFI}'>Rafi</span> vs <span style='color:{COHORT}'>cohort</span>", left)
    cal = pd.concat([
        rp.groupby(rp.Date.dt.day_name())["Calories"].mean().rename("Calories").reset_index().assign(Who="Rafi"),
        fa.groupby(fa.Date.dt.day_name())["Calories"].mean().rename("Calories").reset_index().assign(Who="Cohort")])
    cal.columns = ["Day", "Calories", "Who"]
    cal["Day"] = cal["Day"].str[:3]
    base = alt.Chart(cal).encode(
        x=alt.X("Day:N", title=None, sort=[d[:3] for d in DAYS], axis=alt.Axis(labelAngle=0, grid=False)),
        y=alt.Y("Calories:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format=",.0f")),
        color=alt.Color("Who:N", scale=who, legend=None))
    show(base.mark_line(strokeWidth=2.5) +
         base.mark_circle(size=60).encode(tooltip=["Who:N", "Day:N", alt.Tooltip("Calories:Q", format=",.0f")]), 260, left)

    # Rebound after a short night
    def rebound(d):
        d = d.sort_values("Date")
        nxt = d["Hours"].shift(-1)[(d["Date"].shift(-1) - d["Date"]).dt.days == 1]
        pairs = pd.DataFrame({"Hours": d["Hours"], "Next": nxt}).dropna()
        return pairs[pairs["Hours"] < 6]
    rr = rebound(rs)
    cr = pd.concat([rebound(g) for _, g in fs.groupby("Id")])
    reb = pd.DataFrame({
        "Night": ["Short night", "Next night", "Typical night"] * 2,
        "Who": ["Rafi"] * 3 + ["Cohort"] * 3,
        "Hours": [rr.Hours.mean(), rr.Next.mean(), rafi["Hours"], cr.Hours.mean(), cr.Next.mean(), fs.Hours.mean()]})
    section(f"Rebound after a night under 6 h &middot; <span style='color:{RAFI}'>Rafi</span> vs <span style='color:{COHORT}'>cohort</span>", right)
    show(alt.Chart(reb).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Night:N", title=None, sort=["Short night", "Next night", "Typical night"], axis=alt.Axis(labelAngle=0, grid=False)),
        xOffset=alt.XOffset("Who:N", sort=["Rafi", "Cohort"]),
        y=alt.Y("Hours:Q", title=None),
        color=alt.Color("Who:N", scale=who, legend=None),
        tooltip=["Who:N", "Night:N", alt.Tooltip("Hours:Q", format=".1f")]), 260, right)
    right.caption(f"Based on {len(rr)} short nights for Rafi and {len(cr)} for the cohort, followed by a logged next night.")

    # Does activity help you sleep?
    section("Does a harder day mean more sleep? &middot; same-date activity vs sleep, with trend line")
    left, right = st.columns(2, gap="large")
    for where, df_, xcol, xlab, color, r, who_ in [
        (left, link_c, "TotalSteps", "Steps", COHORT, r_c, "Cohort"),
        (right, link_r, "Strain", "Day strain", RAFI, r_r, "Rafi")]:
        where.markdown(f'<div class="cmp" style="margin:0 0 4px"><b style="color:{color}">{who_}</b> &middot; r = {r:.2f}</div>',
                       unsafe_allow_html=True)
        pts = alt.Chart(df_).mark_circle(color=color, size=30, opacity=0.5).encode(
            x=alt.X(f"{xcol}:Q", title=xlab, scale=alt.Scale(zero=False)),
            y=alt.Y("Hours:Q", title="Sleep (h)"),
            tooltip=[alt.Tooltip(f"{xcol}:Q", format=",.1f"), alt.Tooltip("Hours:Q", format=".1f")])
        fit = pts.transform_regression(xcol, "Hours").mark_line(color="#F2F4F7", strokeWidth=2, strokeDash=[5, 4])
        show(pts + fit, 260, where)

    st.markdown('<div class="foot">Fitbit: 2016 public Kaggle dataset, cohort averages weight every user equally. '
                'WHOOP: one person, Dec 2023 to Aug 2025. Sleep and calorie algorithms differ by device.</div>',
                unsafe_allow_html=True)
