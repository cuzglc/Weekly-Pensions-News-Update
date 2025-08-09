import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="News Dashboard", layout="wide")

st.title("News Dashboard")


def get_state(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


st.write("Upload your latest Excel/CSV of stories or use the sample data packaged with this app.")

@st.cache_data
def load_sample():
    return pd.read_csv("sample_data.csv")

def standardize_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_col(df, candidates):
    for cand in candidates:
        for col in df.columns:
            if cand in col.lower():
                return col
    return None

def detect_schema(df):
    cols = list(df.columns)
    col_date = find_col(df, ["date", "published", "updated"])
    col_title = find_col(df, ["headline", "title"])
    col_intro = find_col(df, ["intro", "introduction", "summary", "dek"])
    col_tags = find_col(df, ["tag", "topic", "topics", "category", "categories", "label"])
    col_keyinfo = find_col(df, ["key information", "key info", "details", "body", "story", "content"])
    col_relevance = find_col(df, ["relevance", "why it matters", "impact"])
    col_links = find_col(df, ["link", "links", "url", "source"])
    return {
        "date": col_date,
        "title": col_title,
        "intro": col_intro,
        "tags": col_tags,
        "key_information": col_keyinfo,
        "relevance": col_relevance,
        "links": col_links,
    }

def preprocess(df, schema):
    df = df.copy()
    # Coerce date
    dcol = schema["date"]
    if dcol:
        df[dcol] = pd.to_datetime(df[dcol], errors="coerce")
        df = df.dropna(subset=[dcol])
    # Ensure strings
    for k in ["title", "intro", "tags", "key_information", "relevance", "links"]:
        c = schema.get(k)
        if c and c in df.columns:
            df[c] = df[c].astype(str).fillna("")
    return df

# Data source
tab1, tab2 = st.tabs(["Upload file", "Use sample"])


with tab1:
    uploaded = st.file_uploader("Upload Excel (.xlsx) or CSV", type=["xlsx", "csv"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df_up = pd.read_csv(uploaded)
                st.session_state["uploaded_type"] = "csv"
                st.session_state["data"] = standardize_cols(df_up)
                st.session_state["schema"] = detect_schema(st.session_state["data"])
                st.success("CSV loaded!")
            else:
                # Excel: let user pick a sheet
                xls = pd.ExcelFile(uploaded, engine="openpyxl")
                sheets = xls.sheet_names
                pick = st.selectbox("Select worksheet", sheets, key="sheet_select")
                if pick:
                    df_up = pd.read_excel(xls, pick)
                    st.session_state["uploaded_type"] = "excel"
                    st.session_state["uploaded_sheet"] = pick
                    st.session_state["data"] = standardize_cols(df_up)
                    st.session_state["schema"] = detect_schema(st.session_state["data"])
                    st.success(f"Excel loaded (sheet: {pick})!")
        except Exception as e:
            st.error("Couldn't read that file. Common fixes:

- If it's Excel, ensure it's .xlsx (not .xls)
- Make sure the first row has column headers
- Try another sheet if using Excel
- If dates are stored as text, that's OK; the app will parse them

Error detail: " + str(e))


with tab2:
    if st.button("Load sample data"):
        df = load_sample()
        df = standardize_cols(df)
        schema = detect_schema(df)
        st.session_state["data"] = df
        st.session_state["schema"] = schema
        st.success("Sample loaded!")

if "data" not in st.session_state:
    st.info("Load data to begin.")
    st.stop()

df = st.session_state["data"]


def combine_cols(row, cols, sep="; "):
    if not cols: return ""
    vals = []
    for c in (cols if isinstance(cols, list) else [cols]):
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            vals.append(str(row[c]).strip())
    return sep.join(vals)

schema = st.session_state["schema"]

# Sidebar filters
st.sidebar.header("Filters")

dcol = schema.get("date")
tcol = schema.get("tags")  # list of tag columns
title_col = schema.get("title")
intro_col = schema.get("intro")
key_col = schema.get("key_information")  # list of key info columns
rel_col = schema.get("relevance")  # list of relevance columns
link_col = schema.get("links")  # list of link columns

if dcol:
    ser = pd.to_datetime(df[dcol], errors="coerce")
    min_date = ser.min()
    max_date = ser.max()
    if pd.isna(min_date) or pd.isna(max_date):
        st.sidebar.info("No valid dates detected in the date column. Date filter disabled.")
        start = end = None
    else:
        start, end = st.sidebar.date_input(
            "Date range", 
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
else:
    start = end = None

tag_filter = []
if tcol:
    # Split tags on comma/semicolon
    def split_tags(x):
        if pd.isna(x): return []
        s = str(x)
        for sep in [";", "|"]:
            s = s.replace(sep, ",")
        return [t.strip() for t in s.split(",") if t.strip()]
    def row_tags(row):
        return split_tags(combine_cols(row, tcol))
    all_tags = sorted({t for _, r in df.iterrows() for t in row_tags(r)})
    tag_filter = st.sidebar.multiselect("Topics / Tags", options=all_tags)

search_q = st.sidebar.text_input("Search keywords", "")

# Apply filters
fdf = df.copy()
if dcol and start and end:
    mask = (pd.to_datetime(fdf[dcol], errors="coerce").dt.date >= start) & (pd.to_datetime(fdf[dcol], errors="coerce").dt.date <= end)
    fdf = fdf[mask]

if tag_filter and tcol:
    def has_any_row(row):
        tags = [t.lower() for t in row_tags(row)]
        return any(t.lower() in tags for t in tag_filter)
    fdf = fdf[fdf.apply(has_any_row, axis=1)]

if search_q:
    q = search_q.lower()
    def cols_present(cols):
        if not cols: return []
        if isinstance(cols, list):
            return [c for c in cols if c in fdf.columns]
        return [cols] if cols in fdf.columns else []
    cols_to_search = [c for c in [title_col, intro_col] if c and c in fdf.columns] + cols_present(key_col) + cols_present(rel_col)
    def row_match(row):
        for c in cols_to_search:
            if q in str(row[c]).lower():
                return True
        return False
    fdf = fdf[fdf.apply(row_match, axis=1)]

# Sort newest first if date exists
if dcol:
    fdf = fdf.sort_values(by=dcol, ascending=False)

st.caption(f"Showing {len(fdf)} of {len(df)} stories.")

# Render cards
for i, row in fdf.iterrows():
    with st.container(border=True):
        headline = str(row.get(title_col, "")) if title_col else "(No title)"
        intro = str(row.get(intro_col, "")) if intro_col else ""
        date_str = ""
        if dcol:
            d = row[dcol]
            try:
                date_str = pd.to_datetime(d).strftime("%Y-%m-%d")
            except Exception:
                date_str = str(d)
        tags = combine_cols(row, tcol) if tcol else ""
        cols = st.columns([6,2])
        with cols[0]:
            st.subheader(headline)
            meta = " • ".join([x for x in [date_str, tags] if x])
            if meta:
                st.caption(meta)
            if intro:
                st.write(intro)
        with cols[1]:
            first_link = None
            if link_col:
                combined_links = combine_cols(row, link_col, sep=" ")  # space to split
                parts = str(combined_links).split()
                first_link = parts[0] if parts else None
            if first_link:
                # Show first link if multiple
                first_link = str(row[link_col]).split()[0]
                st.link_button("Open source", first_link)
        with st.expander("View details"):
            if key_col:
                st.markdown("**Key information**")
                st.write(combine_cols(row, key_col, sep="\n\n• "))
            if rel_col:
                st.markdown("**Relevance**")
                st.write(combine_cols(row, rel_col, sep="\n\n• "))
            if link_col:
                st.markdown("**Links**")
                st.write(combine_cols(row, link_col, sep="\n"))

st.download_button("Download filtered results (CSV)", data=fdf.to_csv(index=False).encode("utf-8"), file_name="filtered_news.csv", mime="text/csv")
