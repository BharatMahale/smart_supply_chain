import streamlit as st # type: ignore 
import pandas as pd
from math import sqrt
import pydeck as pdk # type: ignore 

VEHICLE_CAPACITY = 25

st.set_page_config(page_title="Supply Chain Optimizer", layout="wide")

st.title("🚚 Smart Supply Chain Optimizer")

st.divider()


st.markdown("""
### 🖥️ AI-Powered Supply Chain Intelligence Dashboard
Real-time disruption prediction • Route optimization • Decision support
""")


# Load data
orders = pd.read_csv("data/orders.csv")


# Sidebar
st.sidebar.header("🌍 Simulation Controls")

traffic_level = st.sidebar.selectbox("Traffic Level", ["Low", "Medium", "High"])
weather_type = st.sidebar.selectbox("Weather", ["Clear", "Fog", "Rain", "Storm"])

simulate = st.sidebar.button("🚀 Apply Scenario")


# Distance function
def distance(a, b):
    return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


# Optimization logic
def optimize_route(df):
    depot = (df.iloc[0]["lat"], df.iloc[0]["lon"])
    route = []
    current = depot
    total_distance = 0
    remaining = df.copy()

    while len(remaining) > 0:
        remaining["dist"] = remaining.apply(
            lambda x: distance(current, (x["lat"], x["lon"])), axis=1
        )

        nearest = remaining.sort_values("dist").iloc[0]
        total_distance += nearest["dist"]

        route.append(nearest)

        current = (nearest["lat"], nearest["lon"])
        remaining = remaining.drop(nearest.name)

    return pd.DataFrame(route), total_distance


# Simulate disruption
if simulate:
    orders["traffic"] = traffic_level
    orders["weather"] = weather_type
    st.warning(f"Scenario applied: Traffic={traffic_level}, Weather={weather_type}")


# Show original data
st.markdown("## 📦 Orders Overview")
st.dataframe(orders, use_container_width=True)

st.divider()


# Optimize button
if st.button("🚀 Optimize Route"):
    optimized, total_distance = optimize_route(orders)

    # ETA
    optimized["ETA (min)"] = optimized["dist"] * 2

    # Risk logic
    def risk(row):
        score = 0
        if row["priority"] == "High":
            score += 30
        elif row["priority"] == "Medium":
            score += 20
        else:
            score += 10

        if row["weight"] > 8:
            score += 20

        if row["dist"] > 0.02:
            score += 20

        # NEW: traffic impact
        if row["traffic"] == "High":
            score += 30
        elif row["traffic"] == "Medium":
            score += 20

        # NEW: weather impact
        if row["weather"] in ["Rain", "Storm"]:
            score += 25
        elif row["weather"] == "Fog":
            score += 15

        if score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        else:
            return "Low"

    optimized["Risk"] = optimized.apply(risk, axis=1)


    # Delay Prediction
    def delay_prediction(row):
        if row["Risk"] == "High":
            return "Likely Delay"
        else:
            return "On Time"

    optimized["Status"] = optimized.apply(delay_prediction, axis=1)


    # KPIs
    st.markdown("## 📊 Operational Metrics")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📦 Orders", len(optimized))
    col2.metric("📏 Distance", round(total_distance, 2))
    col3.metric("⚠️ High Risk", (optimized["Risk"] == "High").sum())

    confidence = 100 - (optimized["Risk"] == "High").sum() * 10
    col4.metric("🤖 Confidence", f"{confidence}%")

    st.divider()


    st.markdown("## 📊 Route Summary")

    st.info(f"""
    🚚 Total Distance: {round(total_distance,2)}  
    ⏱️ Total ETA: {round(optimized["ETA (min)"].sum(),2)} mins  
    ⚠️ High Risk Deliveries: {(optimized["Risk"] == "High").sum()}  
    📦 Total Load: {optimized["weight"].sum()}
    """)


    st.markdown("## 🚛 Vehicle Load Status")

    total_weight = optimized["weight"].sum()

    if total_weight > VEHICLE_CAPACITY:
        st.error(f"⚠️ Overloaded! Total Weight: {total_weight}")
    else:
        st.success(f"✅ Within Capacity. Total Weight: {total_weight}")


    # Highlight risk
    def highlight(val):
        if val == "High":
            return "background-color: red; color: white;"
        elif val == "Medium":
            return "background-color: orange;"
        else:
            return "background-color: lightgreen;"
        

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚨 Disruption Alerts")
        high_risk = optimized[optimized["Risk"] == "High"]

        if not high_risk.empty:
            for _, row in high_risk.iterrows():
                st.error(f"Order {row['order_id']} at risk")
        else:
            st.success("No major disruptions")

    with col2:
        st.markdown("### 🤖 AI Recommendations")

        if (optimized["Risk"] == "High").sum() >= 2:
            st.warning("Use alternate route or extra vehicle")
        elif (optimized["Risk"] == "Medium").sum() >= 2:
            st.info("Monitor deliveries closely")
        else:
            st.success("All routes are optimal")

    st.divider()


    st.markdown("## 🚚 Optimized Delivery Plan")
    st.dataframe(
        optimized[[
            "order_id", "customer", "priority", "traffic", "weather",
            "ETA (min)", "Risk", "Status"
        ]],
        use_container_width=True
    )

    st.divider()


    # Map
    st.markdown("## 🗺️ Route Visualization")

    route_coords = optimized[["lat", "lon"]].values.tolist()

    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=orders["lat"].mean(),
            longitude=orders["lon"].mean(),
            zoom=12,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=optimized,
                get_position='[lon, lat]',
                get_color='[0, 128, 255, 160]',
                get_radius=200,
            ),
            pdk.Layer(
                "LineLayer",
                data=[{"path": route_coords}],
                get_path="path",
                get_width=5,
                get_color='[255, 0, 0]',
            ),
        ],
    ))

    st.divider()


    # Export Section
    st.markdown("## 📥 Export & Reporting")

    csv = optimized.to_csv(index=False)

    st.download_button(
        label="📄 Download Optimized Plan",
        data=csv,
        file_name="route_plan.csv",
        mime="text/csv"
    )


    st.success("✅ Route optimized successfully!")


    st.markdown("---")
    st.markdown("### 💡 Built for Hackathon | Smart Supply Chain Optimization System")