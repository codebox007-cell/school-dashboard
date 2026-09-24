# Career Tour 2026–27 — School Master Dashboard

A Streamlit dashboard for the full 302-school master list (all 8 zones):
an interactive map, enrollment breakdowns, tour/diagnosis status, and an
editable visit tracker.

## Visit tracking
The "Visit tracking" tab lets you set each school's Visit status
(Not visited / Scheduled / Completed), POC, visit date, and notes directly
in the dashboard. It starts pre-filled from the "Career tour already
conducting" column in your data (already-toured schools default to
Completed). Click **Save changes** after editing.

Edits are written to `visit_log.csv` on the app's own disk. **This is not
guaranteed permanent on Streamlit Community Cloud's free tier** — if the
app restarts (inactivity, redeploy, etc.), disk writes can be lost. Use the
"Download current visit log as CSV" button regularly as a backup. If this
tracking becomes important to rely on long-term, the more robust fix is
connecting the app to a Google Sheet or small database instead of local
disk — ask if you want that upgrade built.

## Files
- `app.py` — the dashboard
- `requirements.txt` — Python dependencies
- `school_master_list.csv` — cleaned copy of the "300 school list" sheet from
  your workbook. **Keep this file in the same folder as app.py, not in a
  subfolder** — that's what tripped up the last deploy.

## Run locally
```
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push these three files (all in the same top-level folder — no nesting) to
   a GitHub repo.
2. Go to share.streamlit.io, sign in with GitHub, click "Create app," pick
   this repo and `app.py`.
3. Deploy. Any future git push auto-updates the live app.

## Notes / assumptions made while cleaning
- "Career tour already conducting" contained `#N/A` for schools with no tour
  yet, and an actual site name for schools where one has already happened.
  This is turned into a simple Yes/No "Tour_status" for filtering — the
  original site names are still visible in the full data table.
- "Daignosis" (as spelled in your sheet) had inconsistent casing (`yes` /
  `Yes`) and many blanks; blanks are treated as "not done."
- Two schools have no Latitude/Longitude and are excluded from the map only
  (they still appear in every other tab and the data table).
- The sheet is titled "300 school list" but actually contains 302 rows (two
  S.No values are duplicated in the source — SCHOOL ID is unique, so that's
  used as the reliable identifier).
