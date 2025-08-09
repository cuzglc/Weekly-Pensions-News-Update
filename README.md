# News Dashboard (Streamlit)

This is a lightweight dashboard to **upload, filter, search, and share** news stories with colleagues.

### What it does
- Upload your Excel or CSV of stories (or use the bundled `sample_data.csv`).
- Filter by **date range** and **topics/tags**.
- **Keyword search** across headline, introduction, key information, and relevance.
- Compact cards show **headline, date, tags, and introduction**, with an expander for **key info, relevance, and links**.
- Download the **filtered results** as CSV.

### Expected columns
The app auto-detects columns by name. It looks for:
- Date: contains one of `date`, `published`, `updated`
- Title: `headline`, `title`
- Introduction: `intro`, `introduction`, `summary`, `dek`
- Tags: `tag`, `topic`, `topics`, `category`, `categories`, `label`
- Key information: `key information`, `key info`, `details`, `body`, `story`, `content`
- Relevance: `relevance`, `why it matters`, `impact`
- Links: `link`, `links`, `url`, `source`

### Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy (no servers needed)
**Option A — Streamlit Community Cloud (free):**
1. Create a new GitHub repository and add these files.
2. Go to Streamlit Cloud and connect your repo.
3. Set the app entry-point to `app.py`.
4. Click **Deploy** and share the URL with colleagues.

**Option B — Hugging Face Spaces:**
1. Create a new Space (select **Streamlit** template).
2. Upload these files to the Space.
3. Hit **Run**; share the Space URL.

**Optional refinements**
- Enable authenticated access (Streamlit Cloud supports Google/GitHub auth).
- Add a “shared state” data store (e.g., Google Sheet, Airtable, or a CSV in the repo).
- Add stable URLs with query parameters for saved filters (requires a small enhancement).

---

This package includes a `sample_data.csv` exported from your provided Excel (`1. Role and Goal

You are an in` sheet) so you can see the structure immediately.
