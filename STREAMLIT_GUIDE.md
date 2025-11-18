# Streamlit Categorization App Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Pre-Scrape Profile Data
Before using the Streamlit app, you need to scrape profile data (pictures, bios, posts) for all pages:

```bash
python scrape_profiles.py
```

This will:
- Find all pages that don't have profile data yet
- Scrape profile pictures, bios, and recent posts
- Save everything to `clients_data.json`
- Show progress and save every 10 pages

**Note:** This may take a while depending on how many pages you have. The script includes delays to avoid rate limits.

### 3. Run the Streamlit App
```bash
streamlit run categorize_app.py
```

This will open the app in your browser (usually at `http://localhost:8501`)

## Features

### Tab 1: Categorize Pages
- **One page at a time** view for easy categorization
- **Hotlist Priority**: Pages matching keywords (melanin, black, afro, etc.) appear first
- **Navigation**: Previous/Next buttons, or jump to specific page
- **Auto-save**: Category selection saves automatically when you click "Next"
- **Display**: Profile picture, bio, follower count, recent posts (with caption toggle)

**Filter Options:**
- Uncategorized Only (default)
- All Pages
- Specific Category

### Tab 2: Edit Page Details
- Search/select any page
- Edit contact information:
  - **Known Contact Methods**: Multi-select (IG DM, Email, Phone, WhatsApp, Telegram, Other)
  - **Successful Contact Method**: Which method they replied to
  - **Current Main Contact Method**: Primary method you're using now
- Edit **Promo Price**
- Save changes with one click

### Tab 3: View by Category
- Separate tabs for each category
- **Sorting**:
  - Pages with price: Sorted by `concentration_per_dollar` (best value first)
  - Pages without price: Sorted by `followers_per_client` (most followers per client first)
- Each page shows:
  - Profile picture
  - Stats (followers, clients following, concentration)
  - Contact information
  - Link to Instagram
- Search/filter within each category

## Hotlist Keywords

Pages matching these keywords in username or full_name get prioritized:
- melanin, black, afro, african, afro-american
- blacksuccess, blackbillionaire, blackwealth, blackbusiness
- blackmoney, blackentrepreneur, blackowned, blackexcellence
- melaninmagic, melaninpoppin, melaninrich, melaninmob

You can edit these in `categorize_app.py` (HOTLIST_KEYWORDS list).

## Workflow

1. **Initial Setup**: Run `scrape_profiles.py` to get all profile data
2. **Categorization**: Use "Categorize Pages" tab to go through uncategorized pages
   - Hotlist pages appear first automatically
   - Select category from dropdown
   - Click "Next" to save and move forward
3. **Contact Management**: Use "Edit Page Details" tab to update contact info and pricing
4. **Review**: Use "View by Category" tabs to see all categorized pages sorted by value

## Tips

- **Re-scrape**: If profile data is outdated, run `scrape_profiles.py` again (it only scrapes missing data)
- **Batch Updates**: You can update multiple pages quickly using the "Edit Page Details" tab
- **Search**: Use the search box in "View by Category" to quickly find specific pages
- **Priority Pages**: Look for the 🔥 badge on hotlist pages in the categorization view

## Troubleshooting

**"Profile picture not scraped yet"**
- Run `python scrape_profiles.py` first

**Images not loading**
- Instagram image URLs expire. Re-run `scrape_profiles.py` to get fresh URLs

**App not starting**
- Make sure Streamlit is installed: `pip install streamlit`
- Check that `clients_data.json` exists

**No pages showing**
- Check your filter settings in "Categorize Pages" tab
- Make sure you have pages in your database (run `main.py` to add clients first)




