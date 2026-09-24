import os
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Career Tour 2026–27 — School Master Dashboard", layout="wide")

DEFAULT_DATA_PATH = "school_master_list.csv"
VISIT_LOG_PATH = "visit_log.csv"
VISIT_STATUS_OPTIONS = ["Not visited", "Scheduled", "Completed"]

RAW_COLUMNS = [
    "S. No", "SCHOOL ID", "ZONE", "NAME OF SCHOOL", "HoS Name", "Contact Number",
    "Shift", "SchoolLevel", "Gender", "Latitude", "Longitude", "Boys", "Girls",
    "Total", "Career tour already conducting", "Daignosis", "Metro station",
]


@st.cache_data
def load_data(file):
    df = pd.read_csv(file, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ZONE"] = df["ZONE"].astype(str).str.strip()

    # "Career tour already conducting" holds '#N/A' when no tour has happened yet,
    # and a school/site name when one already has.
    df["Tour_status"] = df["Career tour already conducting"].apply(
        lambda v: "Not yet conducted" if pd.isna(v) or str(v).strip() == "#N/A" else "Already conducted"
    )

    df["Diagnosis_done"] = df["Daignosis"].apply(
        lambda v: "Yes" if str(v).strip().lower() == "yes" else "No"
    )

    df["Near_metro"] = df["Metro station"].apply(lambda v: "Yes" if pd.notna(v) and str(v).strip() != "" else "No")

    for col in ["Boys", "Girls", "Total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_visit_log(df: pd.DataFrame) -> pd.DataFrame:
    """Build (or reload) the visit-tracking columns, keyed on SCHOOL ID.

    Seeds Visit_status from Tour_status the first time so already-toured
    schools start pre-marked as Completed. If a saved visit_log.csv exists
    (from earlier edits on this running app), that data wins instead.
    """
    seed = pd.DataFrame({
        "SCHOOL ID": df["SCHOOL ID"],
        "Visit_status": df["Tour_status"].map({"Already conducted": "Completed", "Not yet conducted": "Not visited"}),
        "POC": "",
        "Visit_date": "",
        "Notes": "",
    }).set_index("SCHOOL ID")

    if os.path.exists(VISIT_LOG_PATH):
        saved = pd.read_csv(VISIT_LOG_PATH, encoding="utf-8").set_index("SCHOOL ID")
        # Overwrite seed defaults with any previously saved edits; schools not
        # yet in the saved log (e.g. a refreshed master list) keep the seed.
        seed.update(saved)

    return seed.reset_index()


st.title("🏫 Career Tour 2026–27 — School Master Dashboard")
st.caption("All 302 schools across 8 zones, from the master consolidated list.")

uploaded = st.sidebar.file_uploader("Upload a different CSV (optional)", type="csv")

if uploaded is not None:
    df = load_data(uploaded)
else:
    df = load_data(DEFAULT_DATA_PATH)

df = clean(df)

visit_log = load_visit_log(df)
df = df.merge(visit_log, on="SCHOOL ID", how="left")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

zones = sorted(df["ZONE"].dropna().unique())
zone_sel = st.sidebar.multiselect("Zone", zones, default=zones)

genders = sorted(df["Gender"].dropna().unique())
gender_sel = st.sidebar.multiselect("Gender", genders, default=genders)

shifts = sorted(df["Shift"].dropna().unique())
shift_sel = st.sidebar.multiselect("Shift", shifts, default=shifts)

tour_sel = st.sidebar.multiselect(
    "Tour status", ["Not yet conducted", "Already conducted"],
    default=["Not yet conducted", "Already conducted"],
)

visit_sel = st.sidebar.multiselect("Visit status", VISIT_STATUS_OPTIONS, default=VISIT_STATUS_OPTIONS)

filtered = df[
    df["ZONE"].isin(zone_sel)
    & df["Gender"].isin(gender_sel)
    & df["Shift"].isin(shift_sel)
    & df["Tour_status"].isin(tour_sel)
    & df["Visit_status"].isin(visit_sel)
]

# ---------------- Top metrics ----------------
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Schools (filtered)", len(filtered))
c2.metric("Total enrollment", int(filtered["Total"].sum(skipna=True)))
c3.metric("Zones covered", filtered["ZONE"].nunique())
c4.metric("Visits completed", int((filtered["Visit_status"] == "Completed").sum()))
c5.metric("Visits pending", int((filtered["Visit_status"] == "Not visited").sum()))
c6.metric("Near a metro station", int((filtered["Near_metro"] == "Yes").sum()))

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Map", "Enrollment", "Tour & diagnosis status", "Visit tracking", "All schools"]
)

# ---------------- Tab 1: Map ----------------
with tab1:
    st.subheader("School locations")
    mappable = filtered.dropna(subset=["Latitude", "Longitude"])
    if len(mappable) < len(filtered):
        st.caption(f"{len(filtered) - len(mappable)} school(s) in the current filter have no coordinates and are excluded from the map.")

    color_by = st.radio("Color points by", ["ZONE", "Tour_status", "Diagnosis_done", "Near_metro"], horizontal=True)

    fig = px.scatter_mapbox(
        mappable,
        lat="Latitude",
        lon="Longitude",
        color=color_by,
        hover_name="NAME OF SCHOOL",
        hover_data=["ZONE", "Shift", "Gender", "Total", "HoS Name"],
        zoom=9,
        height=600,
    )
    fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Tab 2: Enrollment ----------------
with tab2:
    st.subheader("Enrollment by zone")
    by_zone = filtered.groupby("ZONE")["Total"].sum().reset_index().sort_values("Total", ascending=False)
    st.plotly_chart(px.bar(by_zone, x="ZONE", y="Total"), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Enrollment by gender")
        by_gender = filtered.groupby("Gender")["Total"].sum().reset_index()
        st.plotly_chart(px.pie(by_gender, names="Gender", values="Total"), use_container_width=True)
    with col_b:
        st.subheader("Enrollment by shift")
        by_shift = filtered.groupby("Shift")["Total"].sum().reset_index()
        st.plotly_chart(px.pie(by_shift, names="Shift", values="Total"), use_container_width=True)

    st.subheader("Boys vs Girls enrollment by zone")
    bg = filtered.groupby("ZONE")[["Boys", "Girls"]].sum().reset_index()
    bg_melt = bg.melt(id_vars="ZONE", value_vars=["Boys", "Girls"], var_name="Group", value_name="Count")
    st.plotly_chart(px.bar(bg_melt, x="ZONE", y="Count", color="Group", barmode="group"), use_container_width=True)

# ---------------- Tab 3: Tour & diagnosis status ----------------
with tab3:
    st.subheader("Tour status by zone")
    tour_by_zone = filtered.groupby(["ZONE", "Tour_status"]).size().reset_index(name="Count")
    st.plotly_chart(
        px.bar(tour_by_zone, x="ZONE", y="Count", color="Tour_status", barmode="group"),
        use_container_width=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Diagnosis completed?")
        diag_counts = filtered["Diagnosis_done"].value_counts().reset_index()
        diag_counts.columns = ["Diagnosis done", "Count"]
        st.dataframe(diag_counts, use_container_width=True, hide_index=True)
    with col_b:
        st.subheader("Near a metro station?")
        metro_counts = filtered["Near_metro"].value_counts().reset_index()
        metro_counts.columns = ["Near metro", "Count"]
        st.dataframe(metro_counts, use_container_width=True, hide_index=True)

    st.subheader("Schools where a tour has not yet been conducted")
    st.dataframe(
        filtered[filtered["Tour_status"] == "Not yet conducted"][
            ["NAME OF SCHOOL", "ZONE", "Shift", "Gender", "Total", "HoS Name", "Contact Number"]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ---------------- Tab 4: Visit tracking (editable) ----------------
with tab4:
    st.subheader("Track and update school visits")
    st.caption(
        "Visit status starts pre-filled from the 'Career tour already conducting' column "
        "(already-toured schools default to Completed). Edit any cell below, then click Save."
    )

    editable_cols = ["SCHOOL ID", "NAME OF SCHOOL", "ZONE", "HoS Name", "Contact Number",
                      "Visit_status", "POC", "Visit_date", "Notes"]
    editor_df = filtered[editable_cols].reset_index(drop=True)

    edited = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["SCHOOL ID", "NAME OF SCHOOL", "ZONE", "HoS Name", "Contact Number"],
        column_config={
            "Visit_status": st.column_config.SelectboxColumn("Visit status", options=VISIT_STATUS_OPTIONS),
            "Visit_date": st.column_config.TextColumn("Visit date", help="Type a date, e.g. 2026-09-30"),
        },
        key="visit_editor",
    )

    if st.button("💾 Save changes"):
        # Merge edited rows back into the full visit log (not just the filtered view)
        # so filtering never causes other schools' edits to be lost.
        full_log = load_visit_log(df).set_index("SCHOOL ID")
        edits = edited.set_index("SCHOOL ID")[["Visit_status", "POC", "Visit_date", "Notes"]]
        full_log.update(edits)
        full_log.reset_index().to_csv(VISIT_LOG_PATH, index=False, encoding="utf-8")
        st.success(f"Saved {len(edited)} row(s). Refresh the page to confirm.")

    st.caption(
        "⚠️ Note: on Streamlit Community Cloud's free tier, saved edits live on the app's own "
        "disk and aren't guaranteed to survive every restart. Download a backup regularly if "
        "this data matters."
    )
    st.download_button(
        "Download current visit log as CSV",
        load_visit_log(df).to_csv(index=False).encode("utf-8"),
        file_name="visit_log_backup.csv",
        mime="text/csv",
    )

# ---------------- Tab 5: All schools ----------------
with tab5:
    st.subheader("All schools (filtered)")
    display_cols = RAW_COLUMNS + ["Visit_status", "POC", "Visit_date", "Notes"]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        filtered[display_cols].to_csv(index=False).encode("utf-8"),
        file_name="filtered_school_master_list.csv",
        mime="text/csv",
    )
