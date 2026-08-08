import os
import polars as pl
import plotly.express as px
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Defense Viz App",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling: App background #19310c, text white
st.markdown("""
<style>
    /* Global background color and default text color */
    .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"], body {
        background-color: #19310c !important;
        color: #FFFFFF !important;
    }
    
    header, [data-testid="stHeader"] {
        background-color: #19310c !important;
    }

    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        color: #FFFFFF !important;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1.0rem;
        color: #CBD5E1 !important;
        margin-bottom: 1.5rem;
    }
    
    .pitch-container {
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        margin-top: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }
    
    .match-header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 0.2rem;
    }
    
    .match-date-subtitle {
        font-size: 0.95rem;
        color: #94A3B8 !important;
        margin-bottom: 1rem;
    }
    
    .metric-badge {
        display: inline-block;
        background-color: #234213;
        border: 1px solid rgb(164, 235, 152);
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        margin-right: 0.75rem;
        font-size: 0.9rem;
        font-weight: 600;
        color: rgb(164, 235, 152) !important;
    }
    
    .instruction-box {
        background-color: #1e1e1e;
        border-left: 4px solid rgb(164, 235, 152);
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data() -> pl.DataFrame:
    """
    Reads match data from data/data.parquet into a Polars DataFrame.
    Enriches with scores and date if not present.
    """
    data_path = "data/data.parquet"
    if not os.path.exists(data_path):
        data_path = "defense_viz_app/data/data.parquet"
        if not os.path.exists(data_path):
            st.error(f"Data file not found at {data_path}")
            return pl.DataFrame()

    df = pl.read_parquet(data_path)
    df = df.with_columns(
        hover_info=(
            pl.col("home_team")
            + " "
            + pl.col("home_team_score").cast(pl.String)
            + " - "
            + pl.col("away_team_score").cast(pl.String)
            + " "
            + pl.col("away_team")
            + "<br>"
            + pl.col("date")
        )
    )
    return df


def main():
    # Load data into Polars DataFrame
    df_polars = load_data()

    if df_polars.is_empty():
        st.warning("No data available to display.")
        return

    # Convert to pandas for Plotly Express input
    pdf = df_polars.to_pandas()
    pdf["display_goals_size"] = pdf["rma_goals"] + 1

    # Dropdown menu to switch scatter plot x-axis metric (replacing st.subheader("Scatter Plot"))
    selected_metric = st.selectbox(
        "Select Defensive Metric",
        options=[
            "Number of Pressures",
            "Horizontal Compactness",
            "Centroid Compactness",
            "Defensive Line Height"
        ],
        key="scatter_metric_selector",
        label_visibility="collapsed",
    )

    if selected_metric == "Centroid Compactness":
        x_col = "def_compact"
        x_label = "Centroid Compactness"
        plot_title = "Centroid Compactness vs Real Madrid Shots (Dot size scaled by Goals)"
    elif selected_metric == "Defensive Line Height":
        x_col = "def_median"
        x_label = "Defensive Line Height"
        plot_title = "Defensive Line Height vs Real Madrid Shots (Dot size scaled by Goals)"
    elif selected_metric == "Horizontal Compactness":
        x_col = "horiz_compact"
        x_label = "Horizontal Compactness"
        plot_title = "Horizontal Compactness vs Real Madrid Shots (Dot size scaled by Goals)"
    else:
        x_col = "num_pressures"
        x_label = "Number of Pressures"
        plot_title = "Defensive Pressures vs Real Madrid Shots (Dot size scaled by Goals)"

    # Create Plotly scatter plot
    fig = px.scatter(
        pdf,
        x=x_col,
        y="rma_shots",
        size="display_goals_size",
        size_max=32,
        custom_data=["hover_info", "match_id", "home_team", "away_team", "home_team_score", "away_team_score", "date", "rma_goals"],
        labels={
            x_col: x_label,
            "rma_shots": "Real Madrid Shots",
            "rma_goals": "Real Madrid Goals",
            "display_goals_size": "Real Madrid Goals"
        },
        title=plot_title
    )

    # Format hover tooltip to display: "{home_team} {home_team_score} - {away_team_score} {away_team}\n{date}"
    fig.update_traces(
        hovertemplate="<br>%{customdata[0]}<br><extra></extra>",
        marker=dict(
            color="rgb(164, 235, 152)",
            sizemin=8,
            sizemode="area",
            line=dict(width=1, color="#19310c")
        )
    )

    # Background color #1e1e1e and white text across plot
    xaxis_config = dict(
        title=dict(text=x_label, font=dict(color="#FFFFFF")),
        tickfont=dict(color="#FFFFFF"),
        gridcolor="#333333",
        zerolinecolor="#555555"
    )

    # For Defensive Line Height, reverse the X-axis and subtract tick values from 52.5
    if selected_metric == "Defensive Line Height":
        tickvals = [30, 32, 34, 36, 38, 40, 42]
        ticktext = [f"{52.5 - v:.1f}".rstrip('0').rstrip('.') for v in tickvals]
        xaxis_config["autorange"] = "reversed"
        xaxis_config["tickmode"] = "array"
        xaxis_config["tickvals"] = tickvals
        xaxis_config["ticktext"] = ticktext

    fig.update_layout(
        height=680,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font=dict(family="sans-serif", size=13, color="#FFFFFF"),
        title=dict(
            font=dict(color="#FFFFFF", size=16)
        ),
        xaxis=xaxis_config,
        yaxis=dict(
            title=dict(text="Real Madrid Shots", font=dict(color="#FFFFFF")),
            tickfont=dict(color="#FFFFFF"),
            gridcolor="#333333",
            zerolinecolor="#555555"
        ),
        hoverlabel=dict(
            bgcolor="#19310c",
            font_size=13,
            font_family="sans-serif",
            font_color="#FFFFFF",
            bordercolor="rgb(164, 235, 152)",
        )
    )

    # Display Scatter Plot (Top Layout)
    event_dict = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode="points",
        key="scatter_plot",
        use_container_width=True
    )

    # Determine selected match ID from click interaction
    selected_match_id = None
    selected_row = None

    if event_dict and "selection" in event_dict and "points" in event_dict["selection"]:
        points = event_dict["selection"]["points"]
        if len(points) > 0:
            pt = points[0]
            # Try getting match_id from customdata
            if "customdata" in pt and len(pt["customdata"]) > 1:
                selected_match_id = pt["customdata"][1]
            elif "point_index" in pt:
                idx = pt["point_index"]
                selected_row = df_polars[idx]
                selected_match_id = selected_row["match_id"][0]
            elif "point_number" in pt:
                idx = pt["point_number"]
                selected_row = df_polars[idx]
                selected_match_id = selected_row["match_id"][0]

    # Store in session state for persistence
    if selected_match_id is not None:
        st.session_state["selected_match_id"] = selected_match_id

    # Below scatter plot: Pitch Plot section
    st.markdown("---")

    active_match_id = st.session_state.get("selected_match_id")

    if active_match_id:
        # Find match record in Polars DataFrame
        match_data = df_polars.filter(pl.col("match_id") == int(active_match_id))

        if not match_data.is_empty():
            row = match_data.to_dicts()[0]
            home_t = row.get("home_team", "")
            away_t = row.get("away_team", "")
            home_s = row.get("home_team_score", 0)
            away_s = row.get("away_team_score", 0)
            m_date = row.get("date", "")
            pressures = row.get("num_pressures", 0)
            shots = row.get("rma_shots", 0)
            goals = row.get("rma_goals", 0)

        pitch_file = f"pitch_plots/{active_match_id}.png"
        if not os.path.exists(pitch_file):
            pitch_file = f"defense_viz_app/pitch_plots/{active_match_id}.png"

        if os.path.exists(pitch_file):
            st.image(
                pitch_file,
                caption=f"Tactical Pitch Plot for Match #{active_match_id}",
                use_container_width=True
            )
        else:
            st.warning(f"Pitch plot file not found for match {active_match_id} ({pitch_file}).")
    else:
        st.markdown(
            """
            <div class="instruction-box">
                👉 <strong>No match selected.</strong> Click on any dot in the scatter plot above to load and display its pitch plot here.
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
