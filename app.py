import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import re

def is_valid_mobile(mobile):
    return bool(re.fullmatch(r'[6-9]\d{9}', mobile))

# ---------- Setup ----------
st.set_page_config(page_title="Customer Loyalty Dashboard", layout="wide")
st.markdown("""
    <style>
    .card {
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        font-weight: 600;
    }
    .Main-card {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #eaefc8, #ffffff); 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        font-weight: 600;
    }
    .gradient-card {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #d4edda, #f8d7da); /* red to green gradient */
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        font-weight: 600;
    }
    .big-number {
        font-size: 32px;
        color: #0f62fe;
        margin-top: 10px;
    }
    .label {
        color: #6c757d;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<h1 style='color:#ffa500; text-align:center; font-size:70px; font-weight:800;'>🛒 Rajmandir Hypermarket - Customer Analysis</h1>""", unsafe_allow_html=True)


# ---------- File Upload ----------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="file_uploader", accept_multiple_files=False)

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    if st.button("⚙️ Process File"):
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            st.session_state["data"] = df
            st.success("✅ Processed successfully.")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
else:
    st.warning("Please upload an Excel file to continue.")
    st.stop()

# ---------- Preprocessing ----------
if "data" in st.session_state:
    df = st.session_state["data"]
else:
    st.stop()
df = df[~df['Name'].str.lower().str.startswith(('loose', 'display'), na=False)]
df['Invoice No.'] = df['Invoice No.'].astype(str)
df['Mobile No.'] = df['Mobile No.'].astype(str)
df['Code'] = df['Code'].astype(str)
df['Name'] = df['Name'].astype(str)
df['Date'] = pd.to_datetime(df['Date'])
df['Qty'] = df['Qty'].astype(float)
df['Net Value'] = df['Net Value'].astype(float)
df['Company'] = df['Company'].astype(str)
df['Brand'] = df['Brand'].astype(str)
df['category'] = df['category'].astype(str)
df['sub_category'] = df['sub_category'].astype(str)
df['class'] = df['class'].astype(str)
df['Counter No.'] = df['Counter No.'].astype(float)
df['vouhcer_type'] = df['vouhcer_type'].astype(str)
df['Days_Between'] = df.groupby('Mobile No.')['Date'].diff().dt.days.fillna(1)
df['Avg_Days_Between'] = (df.groupby('Mobile No.')['Days_Between'].transform(lambda x: x[x > 0].mean() if any(x > 0) else 0))
df['Visit_Count'] = df.groupby('Mobile No.')['Invoice No.'].transform('nunique')
df['First_Visit'] = df.groupby('Mobile No.')['Date'].transform('min')
df['Last_Visit'] = df.groupby('Mobile No.')['Date'].transform('max')
df['Not_Visited_Since_Days'] = (pd.to_datetime('today') - df['Last_Visit']).dt.days
df['Avg_Invoice_Value'] = df.groupby('Mobile No.')['Net Value'].transform('sum') / df.groupby('Mobile No.')['Invoice No.'].transform('nunique')

# ---------- Classification ----------
df['Customer_Type'] = np.select(
    [
        df['Not_Visited_Since_Days'] > 180,
        df['Not_Visited_Since_Days'] > 90,
        df['Not_Visited_Since_Days'] > 45
    ],
    ['Dead', 'Going to Dead', 'At Risk'],
    default='Active'
)
df['fake_number'] = (
    ((df['Avg_Days_Between'].round(0) == 0) & (df['Visit_Count'] > 10)) |
    (~df['Mobile No.'].apply(is_valid_mobile))
)
df['customer_loyalty_type'] = np.select(
    [   
        (df['Visit_Count']>=3) & (df['Avg_Days_Between'].between(22, 36)) & (df['Avg_Invoice_Value']>=10000),
        (df['Visit_Count']>=3) & (df['Avg_Days_Between'].between(22, 36)) & (df['Avg_Invoice_Value']>=5000),
        (df['Visit_Count']>=3) & (df['Avg_Days_Between'].between(22, 36)) & (df['Avg_Invoice_Value']>=1000),
        (df['Visit_Count'].between(1,2) & (df['Avg_Invoice_Value']>=15000))
    ],
    ['Premium','Loyal','Regular','Bulk Buyer'],
    default='Normal'
)


# Visit group for bar chart
bins = [0, 2, 5, 9, float('inf')]
labels = ['1-2 visits', '3-5 visits', '6-9 visits', '10+ visits']
df['Visit_Group'] = pd.cut(df['Visit_Count'], bins=bins, labels=labels, right=True)

# ---------- KPI Section ----------
# ---------- KPI Metrics ----------
unique_customers = df.drop_duplicates(subset='Mobile No.')
total_customers = unique_customers['Mobile No.'].nunique()
fake_count = unique_customers['fake_number'].sum()
repeat_count = unique_customers[unique_customers['Visit_Count'] > 1]['Mobile No.'].nunique()
non_repeat_count = total_customers - repeat_count
repeat_ratio = (repeat_count / total_customers) * 100 if total_customers else 0
non_repeat_ratio = 100 - repeat_ratio
this_month = pd.to_datetime('today').month
this_year = pd.to_datetime('today').year
new_customers = unique_customers[
    (unique_customers['First_Visit'].dt.month == this_month) &
    (unique_customers['First_Visit'].dt.year == this_year)
]['Mobile No.'].nunique()

# ---------- KPI Cards ----------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class='Main-card'>
        <div class='label'>Total Customers</div>
        <div class='big-number'>{total_customers:,}</div>
    </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class='card'>
        <div class='label'>Fake Numbers</div>
        <div class='big-number' style='color:#fa5252;'>{fake_count:,}</div>
    </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class='gradient-card'>
        <div class='label'>Repeat | Not Repeat</div>
        <div class='big-number'>
            <span style='color: #28a745; font-weight: regular;'> {repeat_ratio:.0f}%</span> |
            <span style='color: #dc3545; font-weight: regular;'> {non_repeat_ratio:.0f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class='card'>
        <div class='label'>New Customers (This Month)</div>
        <div class='big-number'>{new_customers}</div>
    </div>
    """, unsafe_allow_html=True)
    
# ---------- Pie Chart (Corrected) ----------
st.subheader(f"📈 Customer Type Distribution ")

# Ensure one row per customer for correct count
unique_customers = df.drop_duplicates(subset='Mobile No.')[['Mobile No.', 'Customer_Type']]
pie_data = unique_customers['Customer_Type'].value_counts().reset_index()
pie_data.columns = ['Customer_Type', 'Count']

fig_pie = px.pie(
    pie_data,
    names='Customer_Type',
    values='Count',
    title="Customer Type Segmentation",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
fig_pie.update_traces(
    hoverinfo="label+percent+value",
    textinfo="label+percent",
    pull=[0.05]*len(pie_data),
    marker=dict(line=dict(color="#000000", width=1))
)
st.plotly_chart(fig_pie, use_container_width=True)

st.caption("""
🛈 **Customer Type Definitions:**
- **Active**: Recently visited
- **At Risk**: Haven’t visited in 45–90 days
- **Going to Dead**: 91–180 days since visit
- **Dead**: No visit in 180+ days
""")

# ---------- Bar Chart (Corrected) ----------
st.subheader("📊 Visit Frequency Breakdown")

# Count by unique customers
customer_df = df.drop_duplicates(subset='Mobile No.')[['Mobile No.', 'Visit_Count']].copy()
customer_df['Visit_Group'] = pd.cut(customer_df['Visit_Count'], bins=bins, labels=labels, right=True)
bar_data = customer_df['Visit_Group'].value_counts().sort_index().reset_index()
bar_data.columns = ['Visit Group', 'Count']

fig_bar = px.bar(
    bar_data,
    x='Visit Group',
    y='Count',
    color='Visit Group',
    title="Customer Visit Frequency Groups",
    text='Count',
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_bar.update_traces(textposition='outside')
fig_bar.update_layout(
    xaxis_title="Visit Range",
    yaxis_title="Number of Unique Customers",
    showlegend=False
)
st.plotly_chart(fig_bar, use_container_width=True)
st.caption("🛈 This bar chart shows how frequently customers revisit. Each group counts unique customers.")

# ---------- Sidebar Navigation ----------
# ---------- Filter Navigation ----------
Number_type = st.radio(
    "Numbers Types",
    ["Real Numbers", "Fake Numbers"],
    horizontal=True
)
st.caption("🛈 Fake numbers are those which doesn't begin with 6-9 or more then 10 visit in a day")

Loyality_type = st.radio(
    "Loyality type",
    ["All","Premium","Loyal","Regular","Bulk Buyer","Normal"],
    horizontal=True
)

menu = st.radio(
    "Customer Type",
    ["All", "Active", "At Risk", "Going to Dead", "Dead"],
    horizontal=True
)
# ---------- Filter Based on Tab ----------
df['vouhcer_type'] = df['vouhcer_type'].str.lower()
group_cols = [
    'Mobile No.', 'First_Visit', 'Last_Visit', 'Avg_Days_Between',
    'Visit_Count', 'Not_Visited_Since_Days', 'Avg_Invoice_Value',
    'Customer_Type', 'fake_number', 'customer_loyalty_type'
]
bill_df = df[df['vouhcer_type'] == 'bill']
return_df = df[df['vouhcer_type'] == 'return']
bill_counts = bill_df.groupby('Mobile No.')['Invoice No.'].nunique().reset_index(name='Bill_Invoice_Count')
return_counts = return_df.groupby('Mobile No.')['Invoice No.'].nunique().reset_index(name='Return_Invoice_Count')
numbers_data = pd.merge(bill_counts, return_counts, on='Mobile No.', how='outer').fillna(0)
filterdf = pd.merge(df, numbers_data, on='Mobile No.', how='left')
filterdf['Bill_Invoice_Count'] = filterdf['Bill_Invoice_Count'].astype(int)
filterdf['Return_Invoice_Count'] = filterdf['Return_Invoice_Count'].astype(int)
output_data = filterdf.groupby(group_cols).agg({
    'Bill_Invoice_Count': 'max',
    'Return_Invoice_Count': 'max'
}).reset_index()

# ---------- Filter Based on Tab ----------
if Number_type == "Real Numbers":
    data = output_data[~output_data['fake_number']]
else:
    data = output_data[output_data['fake_number']]


if Loyality_type == "All":
    data = data
else:
    data = data[data['customer_loyalty_type'] == Loyality_type]

data = data if menu == "All" else data[data['Customer_Type'] == menu]
# ---------- Data Table ----------
st.subheader(f"📄 Customer Table - {Number_type} of {Loyality_type} type customer's who at{menu}")
st.dataframe(data, use_container_width=True)

# ---------- Export Options ----------
col1, col2 = st.columns(2)

with col1:
    csv = data.to_csv(index=False).encode()
    st.download_button("📥 Download CSV", data=csv, file_name=f"{menu}_customers.csv", mime='text/csv')

with col2:
    st.markdown("**Tip:** Use filters to explore exported data.")

st.success("✅ Dashboard Loaded Successfully")

# force rebuild
