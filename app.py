from pathlib import Path

import pandas as pd
import streamlit as st

from experiments import save_experiments


RESULTS_FILE = Path("results/traffic_results.csv")

st.set_page_config(
    page_title="SmartFlow AI",
    page_icon="🚦",
    layout="wide",
)

st.title("🚦 SmartFlow AI")
st.subheader("Intelligent Traffic Signal Optimization")

st.write(
    "Compare fixed-time and AI-based traffic control "
    "under normal and peak traffic scenarios."
)

st.info(
    "The dashboard uses results from the educational "
    "traffic simulation, not live road sensors."
)

if st.button("Run experiments and refresh results"):
    with st.spinner("Running traffic simulations..."):
        df = save_experiments()
        st.session_state["results"] = df

if "results" in st.session_state:
    df = st.session_state["results"]
elif RESULTS_FILE.exists():
    df = pd.read_csv(RESULTS_FILE)
else:
    st.warning(
        "No experiment results found. Click the button above "
        "or run 'python experiments.py' in the terminal."
    )
    st.stop()

scenario = st.selectbox(
    "Select traffic scenario",
    ["Normal", "Peak"],
)

filtered = df[df["scenario"] == scenario].copy()

if filtered.empty:
    st.error("No results found for the selected scenario.")
    st.stop()

summary = (
    filtered.groupby("mode")[
        ["average_wait", "average_queue", "maximum_queue",
         "completed", "emergency_average_wait"]
    ]
    .mean()
)

if "Fixed" not in summary.index or "AI" not in summary.index:
    st.error("Both controller results are required.")
    st.stop()

fixed = summary.loc["Fixed"]
ai = summary.loc["AI"]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Fixed average wait",
    f"{fixed['average_wait']:.2f} s",
)

col2.metric(
    "AI average wait",
    f"{ai['average_wait']:.2f} s",
)

if fixed["average_wait"] > 0:
    change = (
        (fixed["average_wait"] - ai["average_wait"])
        / fixed["average_wait"]
    ) * 100

    col3.metric(
        "Waiting-time reduction",
        f"{change:.1f}%",
        help="A positive value means AI waiting time is lower.",
    )
else:
    col3.metric("Waiting-time reduction", "N/A")

col4.metric(
    "AI completed vehicles",
    f"{ai['completed']:.1f}",
)

st.divider()

st.markdown("### Average waiting time")
st.bar_chart(summary[["average_wait"]])

st.markdown("### Average queue length")
st.bar_chart(summary[["average_queue"]])

st.markdown("### Completed vehicles")
st.bar_chart(summary[["completed"]])

st.markdown("### Emergency vehicle waiting time")
st.bar_chart(summary[["emergency_average_wait"]])

st.markdown("### Experiment data")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download experiment results",
    data=df.to_csv(index=False),
    file_name="traffic_results.csv",
    mime="text/csv",
)

st.caption(
    "Results are averaged across the seeds included in the experiment."
)