import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import json
from urllib.request import urlopen
from bokeh.models import GeoJSONDataSource, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from bokeh.palettes import Viridis256
from bokeh.embed import components
import streamlit.components.v1 as components_html
from bokeh.resources import CDN

# ================= CONFIG =================
st.set_page_config(page_title="PhonePe Dashboard", layout="wide")

# ================= UI =================
st.markdown("""
<style>
body { background-color: #0E1117; }
h1, h2, h3 { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.title("📊 PhonePe Transaction Insights Dashboard")

# ================= DB =================
import streamlit as st
from sqlalchemy import create_engine

db_user = st.secrets["db_user"]
db_password = st.secrets["db_password"]
db_host = st.secrets["db_host"]
db_name = st.secrets["db_name"]

engine = create_engine(
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:3306/{db_name}"
)

@st.cache_data
def run_query(query):
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def style_chart(fig):
    fig.update_layout(
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="white")
    )
    return fig

@st.cache_data
def load_geojson():
    import json
    from urllib.request import urlopen

    with urlopen("https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson") as response:
        return json.load(response)

def create_india_map(df):

    import json
    from urllib.request import urlopen
    from bokeh.models import GeoJSONDataSource, HoverTool, LinearColorMapper
    from bokeh.plotting import figure
    from bokeh.palettes import Viridis256

    # Load GeoJSON
    geojson = load_geojson()

    # 🔥 Normalize YOUR data
    df["State"] = df["State"].str.lower().str.strip()

    data_dict = dict(zip(df["State"], df["total"]))

    # 🔥 Normalize GEOJSON + match
    for feature in geojson["features"]:
        geo_state = feature["properties"]["NAME_1"].lower().strip()

        feature["properties"]["value"] = data_dict.get(geo_state, 0)

    geo_source = GeoJSONDataSource(geojson=json.dumps(geojson))

    # Color fix
    low = df["total"].min()
    high = df["total"].max()
    if low == high:
        high = low + 1

    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=low,
        high=high
    )
    p = figure(
        title="India Transaction Map",
        height=700,
        width=1100,
        tools="pan,wheel_zoom,reset,hover",
        toolbar_location="below"
    )

    p.xaxis.visible = False
    p.yaxis.visible = False
    p.outline_line_color = None
    
    p.grid.grid_line_color = None

    p.patches(
        'xs',
        'ys',
        source=geo_source,
        fill_color={'field': 'value', 'transform': color_mapper},
        line_color='white',
        line_width=0.5,
        fill_alpha=0.9
    )

    hover = p.select_one(HoverTool)
    hover.tooltips = [
        ("State", "@NAME_1"),
        ("Transactions", "@value")
    ]

    return p

@st.cache_data
def get_map_data(filter_query):
    return run_query(f"""
    SELECT State, SUM(Transaction_amount) AS total
    FROM Aggregated_transaction {filter_query}
    GROUP BY State
    """)

# ================= SIDEBAR =================
page = st.sidebar.selectbox("Select Page", [
    "Home",
    "Transaction Dynamics",
    "Device Dominance",
    "Market Expansion",
    "User Engagement",
    "District Analysis",
    "Insurance Analysis",
    "User Registration Analysis",
])

mode = st.sidebar.radio("Mode", ["Total", "Time Period"])

filter_query = ""

if mode == "Time Period":

    # 🔹 Get available years dynamically
    years_df = run_query("""
    SELECT DISTINCT Year 
    FROM Aggregated_transaction 
    ORDER BY Year
    """)

    years = years_df["Year"].dropna().astype(int).tolist() if not years_df.empty else []

    year = st.sidebar.selectbox("Year", years)

    # 🔹 Get quarters based on selected year
    q_df = run_query(f"""
    SELECT DISTINCT Quarter 
    FROM Aggregated_transaction 
    WHERE Year = {year}
    ORDER BY Quarter
    """)

    quarters = q_df["Quarter"].dropna().astype(int).tolist() if not q_df.empty else []

    quarter = st.sidebar.selectbox("Quarter", quarters)

    filter_query = f"WHERE Year={year} AND Quarter={quarter}"

# ================= HOME =================
if page == "Home":

    st.subheader("📌 Overview Dashboard")

    col1, col2, col3 = st.columns(3)

    if mode == "Time Period":
        query = f"""
        SELECT 
            (SELECT SUM(Transaction_amount) FROM Aggregated_transaction WHERE Year={year} AND Quarter={quarter}) AS txn,
            (SELECT SUM(Registered_users) FROM Map_user WHERE Year={year} AND Quarter={quarter}) AS users,
            (SELECT SUM(App_opens) FROM Map_user WHERE Year={year} AND Quarter={quarter}) AS opens
        """
    else:
        query = """
        SELECT 
            (SELECT SUM(Transaction_amount) FROM Aggregated_transaction) AS txn,
            (SELECT SUM(Registered_users) FROM Map_user) AS users,
            (SELECT SUM(App_opens) FROM Map_user) AS opens
        """

    kpi_df = run_query(query)

    total_txn = kpi_df.iloc[0]["txn"] if not kpi_df.empty else 0
    total_users = kpi_df.iloc[0]["users"] if not kpi_df.empty else 0
    total_opens = kpi_df.iloc[0]["opens"] if not kpi_df.empty else 0

    col1.metric("💰 Total Transactions", f"{int(total_txn):,}")
    col2.metric("👥 Total Users", f"{int(total_users):,}")
    col3.metric("📱 App Opens", f"{int(total_opens):,}")
    
    
    map_df = get_map_data(filter_query)
    map_df["State"] = map_df["State"].str.replace("-", " ")
    map_df["State"] = map_df["State"].str.title()

                # 🔥 COMPLETE MAPPING FIX
    map_df["State"] = map_df["State"].replace({
                "Andaman & Nicobar Islands": "Andaman and Nicobar",
                "Dadra & Nagar Haveli & Daman & Diu": "Dadra and Nagar Haveli",
                "Jammu & Kashmir": "Jammu and Kashmir",
                "Delhi": "NCT Of Delhi"
                })
    
        # ================= MAP =================
    st.subheader("🗺️ State-wise Transaction Map")

    if not map_df.empty:
        india_map = create_india_map(map_df)
        from bokeh.embed import file_html
        from bokeh.resources import CDN

        html = file_html(india_map, CDN, "India Map")
        components_html.html(html, height=750)
        
    else:
        st.warning("No data available for map")

    st.subheader("📈 Overall Transaction Trend")

    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(Transaction_amount) AS total
        FROM Aggregated_transaction
        GROUP BY Year, Quarter ORDER BY Year, Quarter
        """)
        st.plotly_chart(style_chart(px.line(trend, x="period", y="total")))
    else:
        st.info(f"Showing data for {year} Q{quarter}")

    
    

# ================= TRANSACTION =================
elif page == "Transaction Dynamics":

    st.subheader("📊 Transaction Analysis")

    df = run_query(f"""
    SELECT State, SUM(Transaction_amount) AS total
    FROM Aggregated_transaction {filter_query}
    GROUP BY State ORDER BY total DESC
    """)
    
 
    # 1️⃣ Bar (Ranking)
    st.plotly_chart(style_chart(
        px.bar(df.head(10), x="State", y="total", title="Top States by Transactions")
    ))

    # 2️⃣ Pie (Distribution)
    top5 = df.head(5)
    others = df.iloc[5:]["total"].sum()
    pie_df = pd.concat([top5, pd.DataFrame([{"State": "Others", "total": others}])])

    st.plotly_chart(style_chart(
        px.pie(pie_df, names="State", values="total", title="Contribution Share")
    ))
    

    # 3️⃣ Scatter (Comparison)
    st.plotly_chart(style_chart(
        px.scatter(df.head(15), x="State", y="total", size="total",
                   title="State Comparison")
    ))

    # 4️⃣ Trend (ONLY for total mode)
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(Transaction_amount) AS total
        FROM Aggregated_transaction
        GROUP BY Year, Quarter ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(trend, x="period", y="total", title="Transaction Trend")
        ))
        
            
    else:
        st.info("Trend disabled for selected time period")
        


    # 5️⃣ Heatmap (Advanced)
    heat = run_query("""
    SELECT State, CONCAT(Year,'-Q',Quarter) AS period,
           SUM(Transaction_amount) AS total
    FROM Aggregated_transaction
    GROUP BY State, Year, Quarter
    """)

    pivot = heat.pivot(index="State", columns="period", values="total")

    st.plotly_chart(style_chart(
        px.imshow(pivot, aspect="auto", title="State vs Time Heatmap")
    ))
    
    

# ================= DEVICE =================
elif page == "Device Dominance":

    st.subheader("📱 Device (Brand) Analysis")

    # ================= DATA =================
    df = run_query(f"""
    SELECT Brand, SUM(User_count) AS total
    FROM Aggregated_user {filter_query}
    GROUP BY Brand
    ORDER BY total DESC
    """)

    # ================= 1️⃣ BAR (Top Brands) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.head(10),
            x="Brand",
            y="total",
            title="Top 10 Mobile Brands by Users"
        )
    ))

    # ================= 2️⃣ PIE (Market Share) =================
    top5 = df.head(5)
    others = df.iloc[5:]["total"].sum()

    pie_df = pd.concat([
        top5,
        pd.DataFrame([{"Brand": "Others", "total": others}])
    ])

    st.plotly_chart(style_chart(
        px.pie(
            pie_df,
            names="Brand",
            values="total",
            title="Market Share Distribution"
        )
    ))

    # ================= 3️⃣ TREEMAP (Hierarchy View) =================
    st.plotly_chart(style_chart(
        px.treemap(
            df,
            path=["Brand"],
            values="total",
            title="Brand Dominance (Treemap)"
        )
    ))

    # ================= 4️⃣ SCATTER (Comparison) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df.head(15),
            x="Brand",
            y="total",
            size="total",
            title="Brand Comparison (Size = Users)"
        )
    ))

    # ================= 5️⃣ TREND (Growth Over Time) =================
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(User_count) AS total
        FROM Aggregated_user
        GROUP BY Year, Quarter
        ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(
                trend,
                x="period",
                y="total",
                title="Overall User Growth Trend"
            )
        ))
    else:
        st.info("Trend disabled for selected time period")

# ================= MARKET =================
elif page == "Market Expansion":

    st.subheader("📈 Market Expansion Analysis")

    # ================= DATA =================
    df = run_query("""
    SELECT State, Year, SUM(Transaction_amount) AS total
    FROM Aggregated_transaction
    GROUP BY State, Year
    ORDER BY State, Year
    """)

    # Growth calculation
    df["growth"] = df.groupby("State")["total"].pct_change()

    # ================= 1️⃣ BAR (Market Size) =================
    latest_year = df["Year"].max()
    latest_df = df[df["Year"] == latest_year]

    st.plotly_chart(style_chart(
        px.bar(
            latest_df.sort_values("total", ascending=False).head(10),
            x="State",
            y="total",
            title=f"Top States by Market Size ({latest_year})"
        )
    ))

    # ================= 2️⃣ LINE (Growth Trend) =================
    st.plotly_chart(style_chart(
        px.line(
            df,
            x="Year",
            y="total",
            color="State",
            title="Market Growth Trend by State"
        )
    ))

    # ================= 3️⃣ SCATTER (Growth vs Size) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df,
            x="growth",
            y="total",
            size="total",
            color="State",
            title="Growth vs Market Size"
        )
    ))

    # ================= 4️⃣ BOX (Growth Distribution) =================
    st.plotly_chart(style_chart(
        px.box(
            df,
            x="State",
            y="growth",
            title="Growth Distribution Across States"
        )
    ))

    # ================= 5️⃣ VIOLIN (Growth Spread) =================
    st.plotly_chart(style_chart(
        px.violin(
            df,
            x="State",
            y="growth",
            title="Growth Spread (Density View)"
        )
    ))

# ================= USER =================
elif page == "User Engagement":

    st.subheader("👥 User Engagement Analysis")

    # ================= DATA =================
    df = run_query(f"""
    SELECT State,
           SUM(Registered_users) AS users,
           SUM(App_opens) AS opens
    FROM Map_user {filter_query}
    GROUP BY State
    """)

    # Engagement Ratio
    df["engagement"] = df["opens"] / df["users"].replace(0, 1)

    # ================= 1️⃣ BAR (Total Users) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.sort_values("users", ascending=False).head(10),
            x="State",
            y="users",
            title="Top States by Registered Users"
        )
    ))

    # ================= 2️⃣ BAR (Engagement Rate) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.sort_values("engagement", ascending=False).head(10),
            x="State",
            y="engagement",
            title="Top States by Engagement Rate"
        )
    ))

    # ================= 3️⃣ SCATTER (Users vs Opens) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df,
            x="users",
            y="opens",
            size="opens",
            color="State",
            title="Users vs App Opens (Activity Level)"
        )
    ))

    # ================= 4️⃣ PIE (User Share) =================
    top5 = df.sort_values("users", ascending=False).head(5)
    others = df.iloc[5:]["users"].sum()

    pie_df = pd.concat([
        top5,
        pd.DataFrame([{"State": "Others", "users": others}])
    ])

    st.plotly_chart(style_chart(
        px.pie(
            pie_df,
            names="State",
            values="users",
            title="User Distribution Share"
        )
    ))

    # ================= 5️⃣ TREND (App Opens Over Time) =================
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(App_opens) AS opens
        FROM Map_user
        GROUP BY Year, Quarter
        ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(
                trend,
                x="period",
                y="opens",
                title="App Opens Trend (User Activity)"
            )
        ))
    else:
        st.info("Trend disabled for selected time period")

# ================= DISTRICT =================
# ================= DISTRICT =================
elif page == "District Analysis":

    st.subheader("🏙️ District-Level Transaction Analysis")

    # ================= DATA =================
    df = run_query(f"""
    SELECT District, SUM(Transaction_amount) AS total
    FROM Map_transaction {filter_query}
    GROUP BY District
    ORDER BY total DESC
    """)

    # ================= 1️⃣ BAR (Top Districts) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.head(10),
            x="District",
            y="total",
            title="Top 10 Districts by Transactions"
        )
    ))

    # ================= 2️⃣ PIE (Contribution Share) =================
    top5 = df.head(5)
    others = df.iloc[5:]["total"].sum()

    pie_df = pd.concat([
        top5,
        pd.DataFrame([{"District": "Others", "total": others}])
    ])

    st.plotly_chart(style_chart(
        px.pie(
            pie_df,
            names="District",
            values="total",
            title="Transaction Share Distribution"
        )
    ))

    # ================= 3️⃣ SCATTER (Comparison) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df.head(15),
            x="District",
            y="total",
            size="total",
            title="District Comparison (Size = Transactions)"
        )
    ))

    # ================= 4️⃣ TREND (Time Analysis) =================
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(Transaction_amount) AS total
        FROM Map_transaction
        GROUP BY Year, Quarter
        ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(
                trend,
                x="period",
                y="total",
                title="District Transactions Trend Over Time"
            )
        ))
    else:
        st.info("Trend disabled for selected time period")

    # ================= 5️⃣ HEATMAP (District vs Time) =================
    heat = run_query("""
    SELECT District,
           CONCAT(Year,'-Q',Quarter) AS period,
           SUM(Transaction_amount) AS total
    FROM Map_transaction
    GROUP BY District, Year, Quarter
    """)

    pivot = heat.pivot(index="District", columns="period", values="total")

    st.plotly_chart(style_chart(
        px.imshow(
            pivot,
            aspect="auto",
            title="District vs Time Heatmap"
        )
    ))

# ================= INSURANCE =================
elif page == "Insurance Analysis":

    st.subheader("🛡️ Insurance Adoption Analysis")

    # ================= DATA =================
    df = run_query(f"""
    SELECT State, SUM(Insurance_amount) AS total
    FROM Aggregated_insurance {filter_query}
    GROUP BY State
    ORDER BY total DESC
    """)

    # ================= 1️⃣ BAR (Top States) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.head(10),
            x="State",
            y="total",
            title="Top 10 States by Insurance Amount"
        )
    ))

    # ================= 2️⃣ PIE (Adoption Share) =================
    top5 = df.head(5)
    others = df.iloc[5:]["total"].sum()

    pie_df = pd.concat([
        top5,
        pd.DataFrame([{"State": "Others", "total": others}])
    ])

    st.plotly_chart(style_chart(
        px.pie(
            pie_df,
            names="State",
            values="total",
            title="Insurance Adoption Share"
        )
    ))

    # ================= 3️⃣ SCATTER (Comparison) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df,
            x="State",
            y="total",
            size="total",
            title="State-wise Insurance Comparison"
        )
    ))

    # ================= 4️⃣ TREND (Growth Over Time) =================
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(Insurance_amount) AS total
        FROM Aggregated_insurance
        GROUP BY Year, Quarter
        ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(
                trend,
                x="period",
                y="total",
                title="Insurance Growth Trend"
            )
        ))
    else:
        st.info("Trend disabled for selected time period")

    # ================= 5️⃣ HEATMAP (Adoption Pattern) =================
    heat = run_query("""
    SELECT State,
           CONCAT(Year,'-Q',Quarter) AS period,
           SUM(Insurance_amount) AS total
    FROM Aggregated_insurance
    GROUP BY State, Year, Quarter
    """)

    pivot = heat.pivot(index="State", columns="period", values="total")

    st.plotly_chart(style_chart(
        px.imshow(
            pivot,
            aspect="auto",
            title="Insurance Adoption Heatmap"
        )
    ))

# ================= USER REGISTRATION =================
elif page == "User Registration Analysis":

    st.subheader("🧑‍💻 User Registration Analysis")

    # ================= DATA =================
    df = run_query(f"""
    SELECT State, SUM(Registered_users) AS total
    FROM Map_user {filter_query}
    GROUP BY State
    ORDER BY total DESC
    """)

    # ================= 1️⃣ BAR (Top States) =================
    st.plotly_chart(style_chart(
        px.bar(
            df.head(10),
            x="State",
            y="total",
            title="Top 10 States by Registered Users"
        )
    ))

    # ================= 2️⃣ PIE (User Share) =================
    top5 = df.head(5)
    others = df.iloc[5:]["total"].sum()

    pie_df = pd.concat([
        top5,
        pd.DataFrame([{"State": "Others", "total": others}])
    ])

    st.plotly_chart(style_chart(
        px.pie(
            pie_df,
            names="State",
            values="total",
            title="User Registration Share"
        )
    ))

    # ================= 3️⃣ SCATTER (Comparison) =================
    st.plotly_chart(style_chart(
        px.scatter(
            df.head(15),
            x="State",
            y="total",
            size="total",
            title="State-wise Registration Comparison"
        )
    ))

    # ================= 4️⃣ TREND (Growth Over Time) =================
    if mode == "Total":
        trend = run_query("""
        SELECT CONCAT(Year,'-Q',Quarter) AS period,
               SUM(Registered_users) AS total
        FROM Map_user
        GROUP BY Year, Quarter
        ORDER BY Year, Quarter
        """)

        st.plotly_chart(style_chart(
            px.line(
                trend,
                x="period",
                y="total",
                title="User Registration Growth Trend"
            )
        ))
    else:
        st.info("Trend disabled for selected time period")

    # ================= 5️⃣ HEATMAP (State vs Time) =================
    heat = run_query("""
    SELECT State,
           CONCAT(Year,'-Q',Quarter) AS period,
           SUM(Registered_users) AS total
    FROM Map_user
    GROUP BY State, Year, Quarter
    """)

    pivot = heat.pivot(index="State", columns="period", values="total")

    st.plotly_chart(style_chart(
        px.imshow(
            pivot,
            aspect="auto",
            title="User Registration Heatmap"
        )
    ))
