import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Career Tour School Dashboard", layout="wide")

RAW_COLUMNS = [
    "S. No", "SCHOOL ID", "ZONE", "NAME OF SCHOOL", "Shift", "HoS Name",
    "Contact Number", "Gender", "Date", "Poc", "Infrastructure availability",
    "Enrollment", "STATUS", "Google form submitted",
]

WORKING_VALUES = {"yes", "working", "tv", "smart board", "smart tv", "stc tv"}
NOT_WORKING_VALUES = {"no", "not working"}

DEFAULT_DATA_PATH = "data/school_list.csv"


@st.cache_data
def load_data(file):
    df = pd.read_csv(file, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    return df


def split_sections(df: pd.DataFrame):
    """Separate the real school rows from the pivot/summary rows tacked on
    at the bottom of the original sheet."""
    main = df[df["SCHOOL ID"].notna()].copy()
    tail = df[df["SCHOOL ID"].isna()].copy()
    tail = tail.dropna(how="all")
    return main, tail


def classify_infra(value) -> str:
    if pd.isna(value):
        return "Unknown"
    v = str(value).strip().lower()
    if v in WORKING_VALUES:
        return "Working"
    if v in NOT_WORKING_VALUES:
        return "Not working"
    return "Unknown"


def clean_main(main: pd.DataFrame) -> pd.DataFrame:
    main = main.copy()
    main["Enrollment_num"] = pd.to_numeric(main["Enrollment"], errors="coerce")
    main["Infra_status"] = main["Infrastructure availability"].apply(classify_infra)

    main["Visit_status"] = main["STATUS"].fillna("Pending")
    main["Visit_status"] = main["Visit_status"].replace({"Already done": "Completed"})

    main["Form_status"] = (
        main["Google form submitted"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"done": "Done", "not done": "Not done"})
        .fillna("Unknown")
    )
    return main


st.title("📋 Career Tour 2026–27 — School Visit Dashboard")

uploaded = st.sidebar.file_uploader("Upload a different CSV (optional)", type="csv")

if uploaded is not None:
    df = load_data(uploaded)
else:
    df = load_data(DEFAULT_DATA_PATH)

main, tail = split_sections(df)
main = clean_main(main)

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

zones = sorted(main["ZONE"].dropna().unique())
zone_sel = st.sidebar.multiselect("Zone", zones, default=zones)

pocs = sorted(main["Poc"].dropna().unique())
poc_sel = st.sidebar.multiselect("POC", pocs, default=pocs)

shifts = sorted(main["Shift"].dropna().unique())
shift_sel = st.sidebar.multiselect("Shift", shifts, default=shifts)

genders = sorted(main["Gender"].dropna().unique())
gender_sel = st.sidebar.multiselect("Gender", genders, default=genders)

filtered = main[
    main["ZONE"].isin(zone_sel)
    & main["Poc"].isin(poc_sel)
    & main["Shift"].isin(shift_sel)
    & main["Gender"].isin(gender_sel)
]

# ---------------- Top metrics ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Schools (filtered)", len(filtered))
c2.metric("Visits completed", int((filtered["Visit_status"] == "Completed").sum()))
c3.metric("Visits pending", int((filtered["Visit_status"] != "Completed").sum()))
c4.metric("Total enrollment", int(filtered["Enrollment_num"].sum(skipna=True)))

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Visit tracking", "Enrollment", "Flagged schools", "All schools", "Original summary (as-is)"]
)

# ---------------- Tab 1: Visit tracking ----------------
with tab1:
    st.subheader("Visit status by POC")
    status_by_poc = (
        filtered.groupby(["Poc", "Visit_status"]).size().reset_index(name="Count")
    )
    fig = px.bar(status_by_poc, x="Poc", y="Count", color="Visit_status", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Google form submission status")
    form_counts = filtered["Form_status"].value_counts().reset_index()
    form_counts.columns = ["Form status", "Count"]
    st.dataframe(form_counts, use_container_width=True, hide_index=True)

    st.subheader("Schools still pending a visit")
    pending = filtered[filtered["Visit_status"] != "Completed"]
    st.dataframe(
        pending[["NAME OF SCHOOL", "ZONE", "Poc", "HoS Name", "Contact Number", "Visit_status"]],
        use_container_width=True,
        hide_index=True,
    )

# ---------------- Tab 2: Enrollment ----------------
with tab2:
    st.subheader("Enrollment by zone")
    by_zone = filtered.groupby("ZONE")["Enrollment_num"].sum().reset_index()
    st.plotly_chart(px.bar(by_zone, x="ZONE", y="Enrollment_num"), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Enrollment by shift")
        by_shift = filtered.groupby("Shift")["Enrollment_num"].sum().reset_index()
        st.plotly_chart(px.pie(by_shift, names="Shift", values="Enrollment_num"), use_container_width=True)
    with col_b:
        st.subheader("Enrollment by gender")
        by_gender = filtered.groupby("Gender")["Enrollment_num"].sum().reset_index()
        st.plotly_chart(px.pie(by_gender, names="Gender", values="Enrollment_num"), use_container_width=True)

# ---------------- Tab 3: Flagged schools ----------------
with tab3:
    st.subheader("Schools to consider dropping")
    st.caption(
        "Based on the note in the original sheet: "
        "\u201cdrop those schools who does not have proper infrastructure and less enrollment.\u201d"
    )
    enrollment_cutoff = st.slider("Enrollment below this = 'low'", 0, 250, 60, step=5)
    include_unknown_infra = st.checkbox(
        "Also flag schools with unrecorded (blank) infrastructure status", value=False
    )

    infra_bad = filtered["Infra_status"] == "Not working"
    if include_unknown_infra:
        infra_bad = infra_bad | (filtered["Infra_status"] == "Unknown")

    flagged = filtered[infra_bad & (filtered["Enrollment_num"] < enrollment_cutoff)]
    st.write(f"**{len(flagged)} school(s) match both conditions.**")
    st.dataframe(
        flagged[
            ["NAME OF SCHOOL", "ZONE", "Shift", "Infrastructure availability",
             "Enrollment_num", "Poc", "HoS Name", "Contact Number"]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Note: 'Infrastructure availability' had inconsistent free-text entries in the original "
        "sheet (e.g. 'no', 'Yes', 'TV', 'smart board', 'not working'). Values are grouped here into "
        "Working / Not working / Unknown as a best-effort read \u2014 double-check edge cases."
    )

# ---------------- Tab 4: All schools ----------------
with tab4:
    st.subheader("All schools (filtered)")
    st.dataframe(filtered[RAW_COLUMNS], use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        filtered[RAW_COLUMNS].to_csv(index=False).encode("utf-8"),
        file_name="filtered_schools.csv",
        mime="text/csv",
    )

# ---------------- Tab 5: Original summary, untouched ----------------
with tab5:
    st.subheader("Original summary block (as it appeared in the sheet)")
    st.caption(
        "The POC visit-count rows and the shift pivot table from the bottom of your original "
        "file, shown unedited."
    )
    st.dataframe(tail, use_container_width=True, hide_index=True)
