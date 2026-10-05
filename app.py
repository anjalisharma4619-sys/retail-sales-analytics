
import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Retail Sales Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.metric-card {border:1px solid #ddd; border-radius:12px; padding:12px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Retail Sales Analytics & Forecasting")
st.caption("Initial Streamlit prototype • Dashboard • Forecasting • Business Insights")

@st.cache_data
def load_demo():
    return pd.read_csv("sample_retail_dataset.csv")

uploaded = st.file_uploader(
    "Upload your retail sales data (CSV or Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded:
    if uploaded.name.lower().endswith(".csv"):
        data = pd.read_csv(uploaded)
    else:
        data = pd.read_excel(uploaded)
else:
    data = load_demo()
    st.info("Demo dataset is loaded. Upload your own CSV/Excel file to analyze real data.")

# Flexible column matching
def find_col(cols, names):
    low = {str(c).strip().lower(): c for c in cols}
    for n in names:
        if n in low:
            return low[n]
    for c in cols:
        cl = str(c).strip().lower()
        if any(n in cl for n in names):
            return c
    return None

date_col = find_col(data.columns, ["date", "order date", "sales date"])
sales_col = find_col(data.columns, ["sales", "revenue", "amount", "total sales"])
category_col = find_col(data.columns, ["category", "product category"])
region_col = find_col(data.columns, ["region", "zone", "area"])
units_col = find_col(data.columns, ["units sold", "quantity", "units", "qty"])

if date_col is None or sales_col is None:
    st.error("Please provide at least a Date column and a Sales/Revenue column.")
    st.stop()

data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
data[sales_col] = pd.to_numeric(data[sales_col], errors="coerce")
data = data.dropna(subset=[date_col, sales_col]).copy()

if category_col:
    data[category_col] = data[category_col].fillna("Unknown").astype(str)
if region_col:
    data[region_col] = data[region_col].fillna("Unknown").astype(str)

# Sidebar filters
st.sidebar.header("🔎 Filters")
min_d, max_d = data[date_col].min().date(), data[date_col].max().date()
date_range = st.sidebar.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)
if isinstance(date_range, tuple) and len(date_range) == 2:
    data = data[(data[date_col].dt.date >= date_range[0]) & (data[date_col].dt.date <= date_range[1])]

if category_col:
    cats = sorted(data[category_col].unique())
    selected_cats = st.sidebar.multiselect("Category", cats, default=cats)
    data = data[data[category_col].isin(selected_cats)]

if region_col:
    regs = sorted(data[region_col].unique())
    selected_regs = st.sidebar.multiselect("Region", regs, default=regs)
    data = data[data[region_col].isin(selected_regs)]

if data.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# KPIs
total_sales = data[sales_col].sum()
total_rows = len(data)
avg_sales = data[sales_col].mean()
total_units = data[units_col].sum() if units_col else np.nan

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total Sales", f"₹{total_sales:,.0f}")
c2.metric("🧾 Transactions", f"{total_rows:,}")
c3.metric("📈 Avg. Sale", f"₹{avg_sales:,.0f}")
c4.metric("📦 Units Sold", f"{total_units:,.0f}" if not np.isnan(total_units) else "N/A")

st.divider()

# Daily trend
daily = data.groupby(data[date_col].dt.date, as_index=False)[sales_col].sum()
daily.columns = ["Date", "Sales"]
fig = px.line(daily, x="Date", y="Sales", markers=True, title="Daily Sales Trend")
fig.update_layout(height=420)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

if category_col:
    cat_sales = data.groupby(category_col, as_index=False)[sales_col].sum().sort_values(sales_col, ascending=False)
    fig_cat = px.bar(cat_sales, x=category_col, y=sales_col, title="Sales by Category", text_auto=".2s")
    left.plotly_chart(fig_cat, use_container_width=True)
else:
    left.info("Category column not detected.")

if region_col:
    reg_sales = data.groupby(region_col, as_index=False)[sales_col].sum().sort_values(sales_col, ascending=False)
    fig_reg = px.bar(reg_sales, x=region_col, y=sales_col, title="Sales by Region", text_auto=".2s")
    right.plotly_chart(fig_reg, use_container_width=True)
else:
    right.info("Region column not detected.")

# Forecast
st.subheader("🔮 Initial Sales Forecast")
st.caption("Prototype forecast: 7-day moving average. This is intentionally simple for the initial project stage.")

daily2 = data.groupby(data[date_col].dt.date)[sales_col].sum().reset_index()
daily2.columns = ["Date", "Sales"]
daily2["Date"] = pd.to_datetime(daily2["Date"])
daily2 = daily2.sort_values("Date")

window = min(7, max(2, len(daily2)))
forecast_days = st.slider("Forecast horizon (days)", 3, 14, 7)

if len(daily2) >= window:
    baseline = daily2["Sales"].tail(window).mean()
    future_dates = pd.date_range(daily2["Date"].max() + pd.Timedelta(days=1), periods=forecast_days)
    forecast = pd.DataFrame({"Date": future_dates, "Forecast Sales": [baseline]*forecast_days})
    hist = daily2.tail(45).rename(columns={"Sales":"Value"}).assign(Type="Actual")
    fc = forecast.rename(columns={"Forecast Sales":"Value"}).assign(Type="Forecast")
    combined = pd.concat([hist[["Date","Value","Type"]], fc[["Date","Value","Type"]]])
    fig_fc = px.line(combined, x="Date", y="Value", color="Type", markers=True,
                     title=f"Actual vs {forecast_days}-Day Forecast")
    st.plotly_chart(fig_fc, use_container_width=True)
    st.dataframe(forecast, use_container_width=True, hide_index=True)
else:
    st.warning("Not enough daily history for the prototype forecast.")

# Insights
st.subheader("💡 Business Insights & Recommendations")
insights = []
insights.append(f"Total analyzed sales are ₹{total_sales:,.0f} across {total_rows:,} records.")

if category_col:
    top_cat = data.groupby(category_col)[sales_col].sum().idxmax()
    insights.append(f"Top-performing category: **{top_cat}**.")
if region_col:
    top_reg = data.groupby(region_col)[sales_col].sum().idxmax()
    insights.append(f"Top-performing region: **{top_reg}**.")
if len(daily2) >= 14:
    recent = daily2.tail(7)["Sales"].mean()
    previous = daily2.iloc[-14:-7]["Sales"].mean()
    if previous:
        change = (recent - previous) / previous * 100
        direction = "increased" if change >= 0 else "decreased"
        insights.append(f"Average daily sales {direction} by **{abs(change):.1f}%** in the latest 7 days versus the previous 7 days.")
insights.append("Use the forecast as an initial planning signal; a later project phase can replace it with a trained ML/time-series model.")

for item in insights:
    st.markdown(f"- {item}")

with st.expander("🧹 Data Preview & Quality"):
    st.write(f"Rows after cleaning: **{len(data):,}**")
    st.write(f"Columns detected: **{len(data.columns)}**")
    st.dataframe(data.head(20), use_container_width=True, hide_index=True)

st.caption("Project prototype — implementation can later add ML forecasting, authentication, database connectivity, and deployment.")
