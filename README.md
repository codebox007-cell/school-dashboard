# Career Tour 2026–27 — School Visit Dashboard

A Streamlit dashboard for tracking career-tour school visits: visit status by POC,
enrollment breakdowns, and a filter to flag schools worth dropping (poor
infrastructure + low enrollment), plus the original pivot/summary block from
the sheet preserved as-is.

## Files
- `app.py` — the dashboard
- `requirements.txt` — Python dependencies
- `data/school_list.csv` — a cleaned (UTF-8) copy of your uploaded sheet, used
  as the default dataset. You can also upload a different CSV from the app's
  sidebar at any time, as long as it has the same column headers.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud (free, online)
1. Create a GitHub repo and push these three items (app.py, requirements.txt,
   the data folder) to it.
2. Go to share.streamlit.io and sign in with GitHub.
3. Click "Create app," pick this repo and `app.py` as the main file, then
   Deploy.
4. Any time you push a new commit, the live app updates automatically.

## Data notes / assumptions made while cleaning
- The sheet's "Infrastructure availability" column had inconsistent free-text
  values (`no`, `Yes`, `TV`, `smart board`, `NOT working`, `STC TV`, etc.).
  The app buckets these into Working / Not working / Unknown — worth a quick
  sanity check against the source sheet if precision matters here.
- One row (Trilokpuri 22 Block) had `#N/A` in Enrollment and "Done" mistakenly
  entered in the Poc column in the original file — this is left as-is; it will
  show up as a "Poc" filter option and a blank enrollment value.
- Rows with no SCHOOL ID (the POC visit-count summary and the shift pivot
  table at the bottom of the original sheet) are treated as a separate
  "Original summary" block, not as school records.
