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
.stTabs [data-baseweb="tab"] p{font:600 15px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.12em;text-transform:uppercase}
</style>""", unsafe_allow_html=True)

def stat_row(items):
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="v">{v}<span class="u">{u}</span></div><div class="l">{l}</div></div>'
        for v, u, l in items) + "</div>", unsafe_allow_html=True)


def section(title, where=st):
    where.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)


def show(chart, h=280, where=st):
    where.altair_chart(
        chart.properties(height=h, background="transparent").configure_view(stroke=None)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=LINE, domainColor=LINE, tickColor=LINE,
                        labelFont="Inter", titleFont="Inter", titleFontWeight=500),
        use_container_width=True)


st.markdown(
    f'<div class="topbar"><div><span class="dot"></span><b>Rafi</b> &nbsp;/&nbsp; Health Analytics</div>'
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
        st.dataframe(dfs[coll], use_container_width=True, hide_index=True)

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
    st.markdown("<h1 style='text-align:center;'>Fitbit Sleep Insights</h1>", unsafe_allow_html=True)

    # User Selector
    user_ids = sorted(sleep_day["Id"].unique())
    selected_user = st.selectbox("Select User ID:", user_ids, key="sleep_user")

    # Filter for selected user
    user_sleep = sleep_day[sleep_day["Id"] == selected_user].copy()

    if user_sleep.empty:
        st.warning("No sleep data available for this user.")
        st.stop()

    # Convert Date column
    user_sleep["Date"] = pd.to_datetime(user_sleep["SleepDay"]).dt.date

    st.subheader(f"Sleep Data for User: {selected_user}")
    #st.dataframe(user_sleep)
    st.markdown("<br>", unsafe_allow_html=True)

    # Sleep Duration Graph
    st.subheader("Sleep Duration Over Time")
    duration_chart = (
        alt.Chart(user_sleep)
        .mark_line(color="#4BA3C3")
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("TotalMinutesAsleep:Q", title="Minutes Asleep"),
            tooltip=["Date", "TotalMinutesAsleep"]
        )
        .properties(width=800, height=350)
    )
    st.altair_chart(duration_chart, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Summary
    st.subheader("Summary of the Selected User")
    avg_sleep = user_sleep["TotalMinutesAsleep"].mean()
    total_sleep = user_sleep["TotalMinutesAsleep"].sum()

    col1, col2 = st.columns(2)
    col1.metric("Average Sleep (mins)", f"{avg_sleep:.0f}")
    col2.metric("Total Sleep (hrs)", f"{total_sleep/60:.1f}")
    st.markdown("<br>", unsafe_allow_html=True)

    best = user_sleep.loc[user_sleep["TotalMinutesAsleep"].idxmax()]
    worst = user_sleep.loc[user_sleep["TotalMinutesAsleep"].idxmin()]

    col3, col4 = st.columns(2)
    col3.metric("Best Sleep (mins)", int(best["TotalMinutesAsleep"]), help=f"Date: {best['Date']}")
    col4.metric("Worst Sleep (mins)", int(worst["TotalMinutesAsleep"]), help=f"Date: {worst['Date']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Weekday vs Weekend Sleep
    st.subheader("Weekday vs Weekend Sleep")

    # Convert date
    user_sleep["Date"] = pd.to_datetime(user_sleep["Date"])

    # Create Weekday/Weekend label instead of True/False
    user_sleep["DayType"] = user_sleep["Date"].dt.weekday.map(
        lambda x: "Weekend" if x >= 5 else "Weekday"
    )

    # Group by DayType
    grouped = user_sleep.groupby("DayType")["TotalMinutesAsleep"].mean().reset_index()

    # Bar chart
    bar_chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("DayType:N", title="Day Type"),
            y=alt.Y("TotalMinutesAsleep:Q", title="Avg Sleep (mins)"),
            color=alt.Color("DayType:N", scale=alt.Scale(
                domain=["Weekday", "Weekend"],
                range=["#4BA3C3", "#1F77B4"]  # nicer colors
            )),
            tooltip=["DayType", "TotalMinutesAsleep"]
        )
        .properties(width=600, height=400)
    )

    st.altair_chart(bar_chart, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Sleep Efficiency
    st.subheader("Sleep Efficiency")

    if "TotalTimeInBed" in user_sleep.columns:
        user_sleep["SleepEfficiency"] = (
            user_sleep["TotalMinutesAsleep"] / user_sleep["TotalTimeInBed"]
        ) * 100

        eff_chart = (
            alt.Chart(user_sleep)
            .mark_line(color="#4BA3C3")
            .encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("SleepEfficiency:Q", title="Sleep Efficiency (%)"),
                tooltip=["Date", "TotalMinutesAsleep", "TotalTimeInBed", "SleepEfficiency"]
            )
            .properties(width=900, height=400)
        )
        st.altair_chart(eff_chart, use_container_width=True)
    else:
        st.warning("The column 'TotalTimeInBed' is missing — cannot calculate sleep efficiency.")


    # Sleep Distribution
    st.subheader("Sleep Duration")

    hist = (
        alt.Chart(user_sleep)
        .mark_bar(color="#85C1E9")
        .encode(
            x=alt.X("TotalMinutesAsleep:Q", bin=alt.Bin(maxbins=12), title="Minutes Asleep"),
            y=alt.Y(
                "count()",
                title="Count of Records",
                axis=alt.Axis(format='d')
            ),
            tooltip=["count()"]
        )
        .properties(width=800, height=400)
    )
    st.altair_chart(hist, use_container_width=True)





# TAB 3: WHOOP Activity
with tabs[3]:
    st.markdown("<h1 style='text-align:center;'>Rafi's WHOOP Insights</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if "Date" in physiologicals_rafi.columns:
        physiologicals_rafi["Date"] = pd.to_datetime(physiologicals_rafi["Date"]).dt.date

    df = physiologicals_rafi.copy()

    # Whoop Recovery Summary
    st.subheader("WHOOP Recovery Summary")

    col1, col2, col3 = st.columns(3)
    # Core Metrics
    col1.metric("Avg HRV", f"{df['Heart rate variability (ms)'].mean():.1f} ms")
    col2.metric("Avg Resting HR", f"{df['Resting heart rate (bpm)'].mean():.1f} bpm")
    col3.metric("Avg Day Strain", f"{df['Day Strain'].mean():.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    # Variability metrics
    col4.metric(
        "HRV Stability",
        f"{df['Heart rate variability (ms)'].std():.1f}",
        help="Lower standard deviation = more consistent recovery"
    )

    # Min/Max HRV
    col5.metric(
        "Best HRV Day",
        f"{df['Heart rate variability (ms)'].max():.1f} ms"
    )

    # Lowest RHR day
    col6.metric(
        "Best Resting HR",
        f"{df['Resting heart rate (bpm)'].min():.1f} bpm"
    )
    st.markdown("<br>", unsafe_allow_html=True)


    col7, col8, col9 = st.columns(3)
    # Energy expenditure
    col7.metric(
        "Avg Energy Burned",
        f"{df['Energy burned (cal)'].mean():.0f} cal"
    )

    # Skin Temperature Avg
    if "Skin temperature" in df.columns:
        col8.metric(
            "Avg Skin Temp",
            f"{df['Skin temperature'].mean():.1f}°C"
        )
    else:
        col8.metric("Avg Skin Temp", "N/A")

    # Blood oxygen levels
    if "Blood oxygen %" in df.columns:
        col9.metric(
            "Avg Blood Oxygen",
            f"{df['Blood oxygen %'].mean():.1f}%"
        )
    else:
        col9.metric("Avg Blood Oxygen", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)


    # Monthly HRV Trend
    st.subheader("Average Heart Rate Variability (HRV) Trend")

    # Make a clean copy
    df = physiologicals_rafi.copy()

    # Convert and sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # Extract Year Month
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # Compute monthly average HRV
    monthly_hrv = df.groupby("Month")["Heart rate variability (ms)"].mean().reset_index()

    # Line chart
    monthly_chart = (
        alt.Chart(monthly_hrv)
        .mark_line(point=True, size=3, color="#00b4d8")
        .encode(
            x=alt.X("Month:N", title="Month"),
            y=alt.Y("Heart rate variability (ms):Q", title="Avg HRV (ms)"),
            tooltip=["Month", "Heart rate variability (ms)"]
        )
        .properties(height=350)
    )
    st.altair_chart(monthly_chart, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)


    # Monthly RHR Trend
    st.subheader("Average Resting Heart Rate (RHR) Trend")

    # Clean copy
    df = physiologicals_rafi.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # Group by month
    monthly_rhr = df.groupby("Month")["Resting heart rate (bpm)"].mean().reset_index()

    # Chart with RED dots
    monthly_rhr_chart = alt.layer(
        alt.Chart(monthly_rhr)
            .mark_line(size=3, color="#e76f51")
            .encode(
                x=alt.X("Month:N", title="Month"),
                y=alt.Y("Resting heart rate (bpm):Q", title="Avg Resting HR (bpm)"),
                tooltip=["Month", "Resting heart rate (bpm)"]
            ),

        alt.Chart(monthly_rhr)
            .mark_circle(size=80, color="#e76f51")
            .encode(
                x="Month:N",
                y="Resting heart rate (bpm):Q",
                tooltip=["Month", "Resting heart rate (bpm)"]
            )
    ).properties(height=350)

    st.altair_chart(monthly_rhr_chart, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)



    # Monthly Whoop Strain Bar Chart
    st.subheader(" Average WHOOP Strain")

    df_month = df.copy()
    df_month["Month"] = df_month["Date"].dt.to_period("M").astype(str)

    monthly_strain = (
        df_month.groupby("Month")["Day Strain"]
        .mean()
        .reset_index()
        .sort_values("Month")
    )
    base = alt.Chart(monthly_strain)

    # Bar Chart Customization
    bars = (
        base
        .mark_bar(
            fill="#0C0C0C",
            opacity=0.35,      
            stroke="#EFEEF1",    
            strokeWidth=1.2
        )
        .encode(
            x=alt.X("Month:N", title="Month", sort=None),
            y=alt.Y("Day Strain:Q", title="Avg Strain Score"),
            tooltip=["Month", "Day Strain"]
        )
    )
    labels = (
        base
        .mark_text(
            align="center",
            baseline="bottom",
            dy=-4,        
            color="white",
            fontSize=12,
            fontWeight="bold"
        )
        .encode(
            x="Month:N",
            y="Day Strain:Q",
            text=alt.Text("Day Strain:Q", format=".1f")
        )
    )
    final_chart = (bars + labels).properties(height=350)
    st.altair_chart(final_chart, use_container_width=True)


    # Day Strain vs Energy Burned
    st.subheader("Strain vs Energy Burned")

    physio = physiologicals_rafi.copy()
    physio["Date"] = pd.to_datetime(physio["Date"]).dt.date

    scatter = (
        alt.Chart(physio)
        .mark_circle(size=70, opacity=0.7, color="#F28E2B")
        .encode(
            x=alt.X("Day Strain:Q", title="Day Strain"),
            y=alt.Y("Energy burned (cal):Q", title="Energy Burned (cal)"),
            tooltip=["Date", "Day Strain", "Energy burned (cal)"]
        )
        .properties(width=800, height=400)
    )
    st.altair_chart(scatter, use_container_width=True)


    # Workout Strain vs Activity Duration
    st.subheader("Strain vs Activity")

    work = workouts_rafi.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.date

    bubble = (
        alt.Chart(work)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("Duration (min):Q", title="Workout Duration (min)"),
            y=alt.Y("Activity Strain:Q", title="Strain Score"),
            size="Energy burned (cal):Q",
            color="Activity name:N",
            tooltip=["Date", "Activity name", "Duration (min)", "Activity Strain", "Energy burned (cal)"]
        )
        .properties(width=900, height=400)
    )
    st.altair_chart(bubble, use_container_width=True)





# TAB 4: WHOOP Sleep
with tabs[4]:
    st.markdown("<h1 style='text-align:center;'>WHOOP Sleep Insights</h1>", unsafe_allow_html=True)

    df = sleeps_rafi.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # Sleep Summary Metrics
    st.subheader("Sleep Summary Metrics")

    avg_sleep = df["Sleep need (min)"].mean()
    avg_perf = df["Sleep performance %"].mean()

    best_night = df.loc[df["Sleep performance %"].idxmax()]
    worst_night = df.loc[df["Sleep performance %"].idxmin()]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Sleep Needed (hrs)", f"{avg_sleep/60:.1f}")
    col2.metric("Avg Sleep Performance", f"{avg_perf:.0f}%")
    col3.metric("Best Night", f"{best_night['Sleep performance %']}%", help=str(best_night["Date"].date()))
    col4.metric("Worst Night", f"{worst_night['Sleep performance %']}%", help=str(worst_night["Date"].date()))

    st.markdown("<br>", unsafe_allow_html=True)


    # Sleep Duration Bar Chart
    st.subheader("Sleep Duration")

    df_sleep = sleeps_rafi.copy()
    df_sleep["Date"] = pd.to_datetime(df_sleep["Date"])

    # Compute total sleep duration
    df_sleep["SleepDuration"] = (
        df_sleep["Light sleep duration (min)"] +
        df_sleep["Deep duration (min)"] +
        df_sleep["REM duration (min)"]
    )

    # 6 month grouping 
    # H1 = Jan–Jun
    # H2 = Jul–Dec
    df_sleep["HalfYear"] = (
        df_sleep["Date"].dt.year.astype(str) + " H" + (((df_sleep["Date"].dt.month - 1) // 6) + 1).astype(str)
    )

    # Compute averages
    halfyear_sleep = (
        df_sleep.groupby("HalfYear")["SleepDuration"]
        .mean()
        .reset_index()
        .sort_values("HalfYear")
    )

    # Bar Chart
    bar_chart = (
        alt.Chart(halfyear_sleep)
        .mark_bar(
            opacity=0.7,
            color="#4BA3C3"
        )
        .encode(
            x=alt.X("HalfYear:N", title="6 Month Period", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("SleepDuration:Q", title="Avg Sleep Duration (min)"),
            tooltip=["HalfYear", "SleepDuration"]
        )
    )
    labels = (
        alt.Chart(halfyear_sleep)
        .mark_text(
            dy=-6,
            color="white",
            fontSize=12,
            fontWeight="bold"
        )
        .encode(
            x="HalfYear:N",
            y="SleepDuration:Q",
            text=alt.Text("SleepDuration:Q", format=".0f")
        )
    )
    st.altair_chart((bar_chart + labels).properties(height=350), use_container_width=True)
 

    # Sleep Performance Bar Chart
    st.subheader("Sleep Performance")

    df = sleeps_rafi.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # 6 month groups
    df["SixMonth"] = (df["Date"].dt.year * 12 + df["Date"].dt.month - (df["Date"].dt.year * 12 + df["Date"].dt.month).min()) // 6

    # Create readable labels
    start_dates = df.groupby("SixMonth")["Date"].min()
    end_dates = df.groupby("SixMonth")["Date"].max()

    labels = [
        f"{start_dates[i].strftime('%Y-%m')} to {end_dates[i].strftime('%Y-%m')}"
        for i in range(len(start_dates))
    ]

    df["SegmentLabel"] = df["SixMonth"].map({i: labels[i] for i in range(len(labels))})

    # Compute averages
    six_month_perf = (
        df.groupby("SegmentLabel")["Sleep performance %"]
        .mean()
        .reset_index()
    )

    bars = (
        alt.Chart(six_month_perf)
        .mark_bar(size=100, color="#e76f51", opacity=0.9)
        .encode(
            x=alt.X("SegmentLabel:N", title="6 Month Period", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Sleep performance %:Q", title="Avg Sleep Performance (%)"),
            tooltip=["SegmentLabel", "Sleep performance %"]
        )
        .properties(height=350)
    )
    labels = (
        alt.Chart(six_month_perf)
        .mark_text(
            dy=-10,
            color="white",
            fontSize=14,
            fontWeight="bold"
        )
        .encode(
            x="SegmentLabel:N",
            y="Sleep performance %:Q",
            text=alt.Text("Sleep performance %:Q", format=".1f")
        )
    )
    st.altair_chart(bars + labels, use_container_width=True)

    # Sleep Duration Distribution
    st.subheader("Distribution of Sleep Duration")
    df["SleepDuration"] = df["Light sleep duration (min)"] + df["Deep duration (min)"] + df["REM duration (min)"]
    sleep_hist = (
        alt.Chart(df)
        .mark_bar(color="#4BA3C3")
        .encode(
            x=alt.X("SleepDuration:Q", bin=alt.Bin(maxbins=12), title="Sleep Duration (min)"),
            y=alt.Y("count()", title="Count of Nights", axis=alt.Axis(format="d")),
            tooltip=["count()"]
        )
        .properties(height=350)
    )
    st.altair_chart(sleep_hist, use_container_width=True)





# TAB 5: Comparisons between WHOOP vs Fitbit
with tabs[5]:
    st.header("WHOOP vs Fitbit Comparison Metrics")

    # Make aligned dataframes using index
    fit = daily_activity.copy().reset_index(drop=True)
    whoop = physiologicals_rafi.copy().reset_index(drop=True)

    # Make lengths equal
    min_len = min(len(fit), len(whoop))
    fit = fit.head(min_len)
    whoop = whoop.head(min_len)

    # Create merged comparison table
    merged = pd.DataFrame({
        "Fitbit Calories": fit["Calories"],
        "WHOOP Energy Burn": whoop["Energy burned (cal)"],
        "Fitbit Steps": fit["TotalSteps"],
        "WHOOP Day Strain": whoop["Day Strain"],
    })

    # Prepare Fitbit data
    fitbit_avg = (
        daily_activity.groupby("Date")["Calories"]
        .mean()
        .reset_index()
    )
    fitbit_avg["Date"] = pd.to_datetime(fitbit_avg["Date"])

    # Prepare WHOOP data
    whoop_energy = physiologicals_rafi.copy()
    whoop_energy["Date"] = pd.to_datetime(whoop_energy["Date"])

    whoop_energy = whoop_energy[["Date", "Energy burned (cal)"]].rename(
        columns={"Energy burned (cal)": "WHOOP Energy"}
    )

    # Merge them by nearest dates
    merged_energy = pd.merge_asof(
        fitbit_avg.sort_values("Date"),
        whoop_energy.sort_values("Date"),
        on="Date",
        direction="nearest"
    )

    # Average Daily Calories Burned Comparison
    st.subheader("Average Daily Calories Burned")

    fitbit_avg_cal = daily_activity["Calories"].mean()
    whoop_avg_energy = physiologicals_rafi["Energy burned (cal)"].mean()

    compare_df = pd.DataFrame({
        "Source": ["Fitbit Users", "Rafi WHOOP"],
        "Energy": [fitbit_avg_cal, whoop_avg_energy]
    })

    bar = (
        alt.Chart(compare_df)
        .mark_bar(size=120, opacity=0.8)
        .encode(
            x=alt.X("Source:N", title="Data Source", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Energy:Q", title="Average Daily Energy (Calories)"),
            color=alt.Color("Source:N", scale=alt.Scale(range=["#4BA3C3", "#F28E2B"])),
            tooltip=["Source", "Energy"]
        )
    )
    labels = (
        alt.Chart(compare_df)
        .mark_text(dy=-10, color="white", fontSize=14, fontWeight="bold")
        .encode(
            x="Source:N",
            y="Energy:Q",
            text=alt.Text("Energy:Q", format=".0f")
        )
    )
    st.altair_chart(bar + labels, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)


    # Sleep Quality Duration Comparison
    st.subheader("Sleep Quality Duration")

    # Fitbit sleep average
    fitbit_avg_sleep = sleep_day["TotalMinutesAsleep"].mean()

    # WHOOP sleep average
    whoop_sleep = sleeps_rafi.copy()
    whoop_sleep["TotalSleepMinutes"] = (
        whoop_sleep["Light sleep duration (min)"] +
        whoop_sleep["Deep duration (min)"] +
        whoop_sleep["REM duration (min)"]
    )
    whoop_avg_sleep = whoop_sleep["TotalSleepMinutes"].mean()

    # Create comparison dataframe
    compare_sleep_df = pd.DataFrame({
        "Source": ["Fitbit Users", "Rafi WHOOP"],
        "SleepMinutes": [fitbit_avg_sleep, whoop_avg_sleep]
    })

    bar = (
        alt.Chart(compare_sleep_df)
        .mark_bar(size=120, opacity=0.8)
        .encode(
            x=alt.X("Source:N", title="Data Source", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("SleepMinutes:Q", title="Average Sleep Duration (min)"),
            color=alt.Color("Source:N", scale=alt.Scale(range=["#4BA3C3", "#F28E2B"])),
            tooltip=["Source", "SleepMinutes"]
        )
    )
    labels = (
        alt.Chart(compare_sleep_df)
        .mark_text(dy=-10, color="white", fontSize=14, fontWeight="bold")
        .encode(
            x="Source:N",
            y="SleepMinutes:Q",
            text=alt.Text("SleepMinutes:Q", format=".0f")
        )
    )
    st.altair_chart((bar + labels).properties(height=350), use_container_width=True)


    # Sleep Quality Comparison
    st.subheader("Sleep Quality Comparison")

    # Fitbit Sleep Performance
    fitbit_sleep = sleep_day.copy()
    fitbit_sleep["Efficiency"] = (fitbit_sleep["TotalMinutesAsleep"] / fitbit_sleep["TotalTimeInBed"]) * 100
    avg_fitbit_efficiency = fitbit_sleep["Efficiency"].mean()

    # WHOOP Sleep Performance
    whoop_sleep = sleeps_rafi.copy()
    avg_whoop_performance = whoop_sleep["Sleep performance %"].mean()

    # Create comparison dataframe
    compare_sleep = pd.DataFrame({
        "Source": ["Fitbit User", "WHOOP"],
        "Value": [avg_fitbit_efficiency, avg_whoop_performance]
    })

    bars = (
        alt.Chart(compare_sleep)
        .mark_bar(size=120, opacity=0.85)
        .encode(
            x=alt.X("Source:N", title="Data Source", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Value:Q", title="Average Sleep Quality (%)"),
            color=alt.Color("Source:N", scale=alt.Scale(range=["#4BA3C3", "#F28E2B"])),
            tooltip=["Source", "Value"]
        )
    )
    labels = (
        alt.Chart(compare_sleep)
        .mark_text(
            dy=-10,
            color="white",
            fontSize=14,
            fontWeight="bold"
        )
        .encode(
            x="Source:N",
            y="Value:Q",
            text=alt.Text("Value:Q", format=".1f")
        )
    )
    st.altair_chart(bars + labels, use_container_width=True)