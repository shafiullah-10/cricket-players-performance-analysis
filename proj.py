import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Cricket Performance Analysis",
    page_icon="🏏",
    layout="wide"
)
#Load data
df = pd.read_csv("cricket_players_stats_combined.csv")
df.columns = df.columns.str.strip()
original = len(df)

# Clean names
df["Name"] = (
    df["Name"].astype(str)
    .str.replace("$", "", regex=False)
    .str.replace("*", "", regex=False)
    .str.replace("#", "", regex=False)
    .str.strip()
)

# Remove duplicates
df = df.drop_duplicates()
duplicates = original - len(df)
df = df.dropna(how="all")

# Convert numeric columns
nums = [
    "Mat", "Runs", "HS", "Avg", "50", "100",
    "Balls", "Wkt", "Ave", "5WI", "Ca", "St"
]

for c in nums:
    df[c] = pd.to_numeric(
        df[c].astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0],
        errors="coerce"
    ).fillna(0)

# Valid player names
valid = pd.to_numeric(
    df["Name"], errors="coerce"
).isna()

players = df[valid].copy()

#Title
st.title("🏏 Cricket Players Performance Analysis")
st.write(
    "Analyze cricket players, teams, batting, bowling "
    "and fielding performance."
)

#Sidebar
st.sidebar.header("🔎 Filters")

team = st.sidebar.multiselect(
    "Team",
    sorted(df["Team"].dropna().unique()),
    default=sorted(df["Team"].dropna().unique())
)

fmt = st.sidebar.multiselect(
    "Format",
    sorted(df["Format"].dropna().unique()),
    default=sorted(df["Format"].dropna().unique())
)

gender = st.sidebar.multiselect(
    "Gender",
    sorted(df["Gender"].dropna().unique()),
    default=sorted(df["Gender"].dropna().unique())
)

minimum = st.sidebar.slider(
    "Minimum Matches",
    1, 100, 10
)

#Filter
data = df[
    df["Team"].isin(team) &
    df["Format"].isin(fmt) &
    df["Gender"].isin(gender)
].copy()

pdata = players[
    players["Team"].isin(team) &
    players["Format"].isin(fmt) &
    players["Gender"].isin(gender)
].copy()

if data.empty:
    st.warning("No data matches your filters.")
    st.stop()

#KPI
st.subheader("📌 Key Performance Indicators")

matches = data["Mat"].sum()
runs = data["Runs"].sum()

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Players", f"{pdata['Name'].nunique():,}")
k2.metric("Matches", f"{matches:,.0f}")
k3.metric("Runs", f"{runs:,.0f}")
k4.metric("Wickets", f"{data['Wkt'].sum():,.0f}")
k5.metric(
    "Runs / Match",
    f"{runs / matches:.2f}" if matches else "0"
)

st.divider()

#Team runs
st.subheader("🏆 Total Runs by Team")

team_runs = (
    data.groupby("Team")["Runs"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(team_runs)


#Pie chart
st.subheader("🥧 Runs Distribution by Format")

format_runs = data.groupby("Format")["Runs"].sum()

fig, ax = plt.subplots(figsize=(4, 3))
ax.pie(
    format_runs.values,
    labels=format_runs.index,
    autopct="%1.1f%%",
    startangle=90
)
ax.set_title("Percentage of Total Runs by Format")
st.pyplot(fig, use_container_width=False)
plt.close(fig)

#Wrickets
st.subheader("🎯 Wickets by Format")

format_wickets = (
    data.groupby("Format")["Wkt"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(format_wickets)

#PLAYER EFFICIENCY 

st.divider()
st.subheader("📊 Player Performance & Efficiency")

eff = (
    pdata[pdata["Mat"] >= minimum]
    .groupby(["Name", "Team"])
    .agg(
        Matches=("Mat", "sum"),
        Runs=("Runs", "sum"),
        Wickets=("Wkt", "sum")
    )
    .reset_index()
)

eff["Runs Per Match"] = (
    eff["Runs"] / eff["Matches"].replace(0, 1)
)

c1, c2 = st.columns(2)

with c1:
    st.write("⭐ Most Efficient Run Scorers")
    st.dataframe(
        eff.sort_values(
            "Runs Per Match", ascending=False
        ).head(10).round(2),
        use_container_width=True,
        hide_index=True
    )

with c2:
    st.write("⚠️ High Matches but Low Runs")
    st.dataframe(
        eff.sort_values(
            "Runs Per Match"
        ).head(10).round(2),
        use_container_width=True,
        hide_index=True
    )

#Line chart
st.divider()
st.subheader("📈 Runs per Match by Match Experience")

pdata["Match Group"] = pd.cut(
    pdata["Mat"],
    [0, 10, 25, 50, 100, 200, 500, float("inf")],
    labels=[
        "1-10", "11-25", "26-50", "51-100",
        "101-200", "201-500", "500+"
    ]
)

line = (
    pdata.groupby("Match Group", observed=True)
    .agg(Runs=("Runs", "sum"), Matches=("Mat", "sum"))
)

line["Runs Per Match"] = (
    line["Runs"] / line["Matches"].replace(0, 1)
)

st.line_chart(line["Runs Per Match"])

#Scatter chart
st.subheader("📊 Matches vs Total Runs")

scatter = (
    pdata.groupby(["Name", "Team"])
    .agg(
        Matches=("Mat", "sum"),
        Runs=("Runs", "sum")
    )
    .reset_index()
)

st.scatter_chart(
    scatter,
    x="Matches",
    y="Runs"
)

st.caption(
    "Players with many matches but relatively fewer runs "
    "can be identified from this chart."
)

#TOP PLAYERS 
st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("🏆 Top 10 Run Scorers")
    st.dataframe(
        pdata.groupby(["Name", "Team"])["Runs"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(),
        use_container_width=True,
        hide_index=True
    )

with c2:
    st.subheader("🎯 Top 10 Wicket Takers")
    st.dataframe(
        pdata.groupby(["Name", "Team"])["Wkt"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(),
        use_container_width=True,
        hide_index=True
    )

#PLAYER PROFILE

st.divider()
st.subheader("👤 Player Profile")

plist = sorted(pdata["Name"].unique())

selected = st.selectbox(
    "Select Player",
    plist
)

p = pdata[pdata["Name"] == selected]

pm = p["Mat"].sum()
pr = p["Runs"].sum()

a, b, c, d, e = st.columns(5)

a.metric("Matches", f"{pm:,.0f}")
b.metric("Runs", f"{pr:,.0f}")
c.metric(
    "Runs / Match",
    f"{pr / pm:.2f}" if pm else "0"
)
d.metric("Wickets", f"{p['Wkt'].sum():,.0f}")
e.metric("Catches", f"{p['Ca'].sum():,.0f}")

st.dataframe(
    p,
    use_container_width=True,
    hide_index=True
)

#PLAYER COMPARISON
st.divider()
st.subheader("⚔️ Player Comparison")

plist = sorted(pdata["Name"].unique())

if len(plist) >= 2:

    x, y = st.columns(2)

    with x:
        player1 = st.selectbox(
            "Player 1",
            plist,
            key="p1"
        )

    with y:
        player2 = st.selectbox(
            "Player 2",
            plist,
            index=1,
            key="p2"
        )

    p1 = pdata[pdata["Name"] == player1]
    p2 = pdata[pdata["Name"] == player2]

    m1, m2 = p1["Mat"].sum(), p2["Mat"].sum()
    r1, r2 = p1["Runs"].sum(), p2["Runs"].sum()

    comparison = pd.DataFrame({
        "Statistic": [
            "Matches",
            "Runs",
            "Runs Per Match",
            "Highest Score",
            "Batting Average",
            "50s",
            "100s",
            "Wickets",
            "Bowling Average",
            "5 Wicket Hauls",
            "Catches"
        ],
        player1: [
            m1, r1,
            r1 / m1 if m1 else 0,
            p1["HS"].max(),
            p1["Avg"].max(),
            p1["50"].sum(),
            p1["100"].sum(),
            p1["Wkt"].sum(),
            p1["Ave"].max(),
            p1["5WI"].sum(),
            p1["Ca"].sum()
        ],
        player2: [
            m2, r2,
            r2 / m2 if m2 else 0,
            p2["HS"].max(),
            p2["Avg"].max(),
            p2["50"].sum(),
            p2["100"].sum(),
            p2["Wkt"].sum(),
            p2["Ave"].max(),
            p2["5WI"].sum(),
            p2["Ca"].sum()
        ]
    })

    st.write(f"### {player1} 🆚 {player2}")

    st.dataframe(
        comparison.round(2),
        use_container_width=True,
        hide_index=True
    )

#TEAM ANALYSIS

st.divider()
st.subheader("🏟️ Team Analysis")

selected_team = st.selectbox(
    "Select Team",
    sorted(data["Team"].unique())
)

td = data[data["Team"] == selected_team]

a, b, c, d = st.columns(4)

a.metric("Players", td["Name"].nunique())
b.metric("Runs", f"{td['Runs'].sum():,.0f}")
c.metric("Wickets", f"{td['Wkt'].sum():,.0f}")
d.metric("Catches", f"{td['Ca'].sum():,.0f}")

#DATA QUALITY 
st.divider()
st.subheader("🧹 Dataset Quality")

invalid = pd.to_numeric(
    df["Name"],
    errors="coerce"
).notna().sum()

a, b, c, d = st.columns(4)

a.metric("Original Records", f"{original:,}")
b.metric("Clean Records", f"{len(df):,}")
c.metric("Duplicates Removed", f"{duplicates:,}")
d.metric("Invalid Name Records", f"{invalid:,}")

# DOWNLOAD 
st.subheader("⬇️ Download Filtered Dataset")

csv = data.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download CSV",
    csv,
    "cricket_filtered_dataset.csv",
    "text/csv"
)

# DATA TABLE 
st.subheader("📋 Cleaned & Filtered Dataset")

st.write(f"Showing {len(data):,} records.")

st.dataframe(
    data,
    use_container_width=True,
    hide_index=True
)

#FOOTER 

st.divider()

st.caption(
    "Cricket Players Performance Analytics | "
    "Python + Pandas + Streamlit"
)