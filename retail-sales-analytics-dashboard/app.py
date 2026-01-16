import streamlit as st
import pandas as pd
import numpy as np
import datetime

# --- 1. Page Configuration (Wide Layout and Title) ---
st.set_page_config(
    page_title="FritoLays Ralphs Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up the main title
st.title("🛒 FritoLays Ralphs Sales Dashboard")
st.markdown("A dynamic dashboard to analyze Frito-Lay product sales performance at Ralphs.")

# --- 2. Data Simulation ---
# Create mock data for demonstration
@st.cache_data
def load_mock_data():
    np.random.seed(42)
    
    # Generate dates for the last year
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    
    date_range = pd.date_range(start_date, end_date, freq='W-SAT').date
    num_records = 500

    data = {
        'Week Ending': np.random.choice(date_range, num_records),
        'Ounces': np.round(np.random.uniform(1.0, 15.0, num_records), 1),
        'Packaging': np.random.choice(['Single Bag', 'Family Size Bag', 'Multipack', 'Canister'], num_records, p=[0.4, 0.3, 0.2, 0.1]),
        'Keyword': np.random.choice(['Tortilla', 'Potato', 'Cheese', 'Pretzel', 'Baked'], num_records),
        'Flavor': np.random.choice(['Original', 'Spicy Sweet Chili', 'Cool Ranch', 'Nacho Cheese', 'Honey Mustard'], num_records),
        'Product': np.random.choice(['Doritos', 'Lay\'s', 'Cheetos', 'Tostitos', 'Ruffles'], num_records),
        'Description': [f'{p} {f} {o}oz' for p, f, o in zip(
            np.random.choice(['Doritos', 'Lay\'s', 'Cheetos', 'Tostitos', 'Ruffles'], num_records),
            np.random.choice(['Original', 'BBQ', 'Sour Cream', 'Cheddar'], num_records),
            np.random.choice([1.75, 5.0, 9.5, 12.0], num_records)
        )],
        'Sales Units': np.random.randint(500, 5000, num_records),
        'Sales Revenue': np.round(np.random.uniform(1000, 25000, num_records), 2),
    }

    df = pd.DataFrame(data)
    df['Week Ending'] = pd.to_datetime(df['Week Ending'])
    return df

df = load_mock_data()

# --- 3. Sidebar Filters ---
st.sidebar.header("Dashboard Filters")

# a. Week Ending Range (Date Slider)
min_date = df['Week Ending'].min().date()
max_date = df['Week Ending'].max().date()

date_start, date_end = st.sidebar.slider(
    '📅 Week Ending Range',
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MM/DD/YY"
)

# b. Ounces Range (Numerical Slider)
min_oz = df['Ounces'].min()
max_oz = df['Ounces'].max()

oz_start, oz_end = st.sidebar.slider(
    '⚖️ Ounces Range',
    min_value=float(min_oz),
    max_value=float(max_oz),
    value=(float(min_oz), float(max_oz)),
    step=0.1
)

# c. Packaging (Multiselect)
all_packaging = df['Packaging'].unique().tolist()
selected_packaging = st.sidebar.multiselect(
    '🛍️ Packaging',
    options=all_packaging,
    default=all_packaging
)

# d. Grouping Selector
group_by_options = ['Keyword', 'Flavor', 'Product', 'Description']
selected_grouping = st.sidebar.selectbox(
    '📊 Group Data By:',
    options=group_by_options
)

# --- 4. Data Filtering ---
df_filtered = df[
    (df['Week Ending'].dt.date >= date_start) & 
    (df['Week Ending'].dt.date <= date_end) & 
    (df['Ounces'] >= oz_start) & 
    (df['Ounces'] <= oz_end) & 
    (df['Packaging'].isin(selected_packaging))
]

# --- 5. Main Dashboard Content ---

st.subheader(f"Results Filtered by: {len(df_filtered)} Records")

if df_filtered.empty:
    st.warning("No data matches the selected filters. Please adjust the sidebar selections.")
else:
    # --- KPIs (Key Performance Indicator) ---
    total_revenue = df_filtered['Sales Revenue'].sum()
    total_units = df_filtered['Sales Units'].sum()
    avg_oz = df_filtered['Ounces'].mean()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Sales Revenue", 
            value=f"${total_revenue:,.2f}",
            delta="+" + f"{(total_revenue * 0.05):,.2f}" # Mock delta
        )

    with col2:
        st.metric(
            label="Total Units Sold", 
            value=f"{total_units:,.0f}",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Avg. Ounces Per Purchase", 
            value=f"{avg_oz:.1f} oz"
        )

    st.markdown("---")

    # --- Grouped Data Chart ---
    st.subheader(f"Revenue by {selected_grouping}")

    # Group the data based on the selected grouping dimension
    df_grouped = df_filtered.groupby(selected_grouping)['Sales Revenue'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='Sales Revenue', ascending=False)

    # Use Streamlit's native element chart for simplicity
    st.bar_chart(
        df_grouped, 
        x=selected_grouping, 
        y='Sales Revenue',
        color="#F8C000" # Frito-Lay yellow/gold look
    )

    st.markdown("---")

    # --- Raw Data Preview (Optional but helpful) ---
    st.subheader("Filtered Raw Data Sample")
    st.dataframe(df_filtered.head(10), use_container_width=True)