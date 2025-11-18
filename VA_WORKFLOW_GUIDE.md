# VA Workflow Guide - Instagram Follower Analyzer

## Overview
This system uses **human-assisted categorization** via a Streamlit web app. A VA (Virtual Assistant) manually categorizes pages by viewing profile pictures, bios, and posts.

## Complete Workflow

### Step 1: Add Clients
**Option A: Single Client**
```bash
python main.py
# Choose option 1
# Enter client name and Instagram username
```

**Option B: Bulk Add**
```bash
python main.py
# Choose option 2
# Enter multiple usernames (comma or space separated)
```

### Step 2: Scrape Following Lists
**Option A: Single Client**
```bash
python main.py
# Choose option 3
# Enter username to scrape
```

**Option B: All Clients**
```bash
python main.py
# Choose option 4
# Confirm and set delay (recommended: 10-15 seconds)
```

**What this does:**
- Gets list of all pages each client follows
- Updates `clients_data.json` with following relationships
- Does NOT scrape profile data yet (that's step 3)

### Step 3: Pre-Scrape Profile Data ⚠️ REQUIRED
**This step is ESSENTIAL before using Streamlit!**

```bash
python scrape_profiles.py
```

**Choose:**
- **Option 1: Priority Scrape** (Recommended first)
  - Scrapes high-priority pages only (Tiers 1-3)
  - Fast: hotlist pages + pages with 2+ clients
  - Good for getting started quickly
  
- **Option 2: Scrape All** (Complete data)
  - Scrapes ALL pages that need profile data
  - Takes longer (overnight run recommended)
  - Use after priority scrape is done

**What this scrapes:**
- Profile pictures
- Bios
- Recent posts (up to 12)
- Follower counts
- Promo status (from bio/highlights)
- Website URLs
- Website promo detection (mentions, pages, forms, emails)

**Smart Features:**
- Skips already-scraped pages
- Prioritizes hotlist pages first
- Marks failed pages (retries after 1 hour)
- Long-term failed pages (5+ failures) retry after 30 days

### Step 4: Use Streamlit App for Categorization
```bash
streamlit run categorize_app.py
```

Opens in browser at `http://localhost:8501`

## Streamlit App Features

### Tab 1: Categorize Pages
**Purpose:** VA categorizes pages one at a time

**Features:**
- **Hotlist Priority**: Pages matching keywords (melanin, black, hustl, etc.) appear first
- **One Page View**: Shows profile pic, bio, follower count, recent posts
- **Caption Toggle**: Show/hide post captions
- **Auto-save**: Category saves automatically when clicking "Next"
- **Navigation**: Previous/Next buttons, or jump to specific page number
- **Filter Options**: 
  - Uncategorized Only (default)
  - All Pages
  - Specific Category

**How to Use:**
1. Select category from dropdown
2. Review page info (pic, bio, posts)
3. Click "Next ▶" to save and move forward
4. Hotlist pages show 🔥 badge

### Tab 2: Edit Page Details
**Purpose:** Update contact info, pricing, promo status

**Features:**
- Search/select any page
- Edit contact methods (multi-select)
- Set IG account used for DM
- Update promo price
- Manually set/override promo status
- View/edit website URL
- View auto-detected promo indicators

**Contact Methods:**
- Known Contact Methods (multi-select)
- Successful Contact Method (which one they replied to)
- Current Main Contact Method
- IG Account for DM (which of your accounts you use)

### Tab 3: View by Category
**Purpose:** Review categorized pages sorted by value

**Features:**
- Separate tabs for each category
- **Smart Sorting:**
  - Pages WITH price: Sorted by `concentration_per_dollar` (best ROI first)
  - Pages WITHOUT price: Sorted by `followers_per_client` (most followers per client first)
- Shows: Profile pic, stats, contact info, website, promo info
- Search/filter within each category
- Quick edit button to jump to Edit Page Details

## Data Flow

```
1. main.py (Add clients + Scrape following lists)
   ↓
2. scrape_profiles.py (Pre-scrape profile data)
   ↓
3. categorize_app.py (VA categorizes pages)
   ↓
4. main.py option 10 (Export to CSV)
```

## Key Features

### Hotlist Keywords (Priority Pages)
These pages appear first in categorization:
- hustl, afri, afro, black, melanin, blvck
- culture, kulture, brown, noir, ebony

### Promo Detection
**Automatic (during scraping):**
- Bio/highlights checked for promo keywords
- Website checked for promo mentions, pages, forms, emails
- Stored in `promo_status` and `promo_indicators`

**Manual (in Streamlit):**
- VA can override promo status
- View auto-detected indicators
- Set to "Warm", "Unknown", or "Not Open"

### Failure Handling
- **Short-term failures**: Retry after 1 hour
- **Long-term failures** (5+ consecutive): Retry after 30 days
- Prevents infinite retries on deleted/restricted accounts

### Contact Tracking
- Track which contact methods are known
- Record which method got a reply
- Track current main contact method
- For IG DM: Track which of your IG accounts you use

## Tips

1. **Start with Priority Scrape**: Gets hotlist pages quickly for immediate categorization
2. **Run Scrape All Overnight**: Complete data collection while you sleep
3. **Use Hotlist Priority**: Focus on high-value pages first
4. **Update Contact Info**: As you contact pages, update in Edit Page Details tab
5. **Export Regularly**: Use CSV export to backup/share data

## Troubleshooting

**"Profile picture not scraped yet"**
→ Run `python scrape_profiles.py` first

**"No pages showing in Streamlit"**
→ Check filter settings (should be "Uncategorized Only" by default)
→ Make sure you've run scrape_profiles.py

**"Images not loading"**
→ Instagram URLs expire. Re-run scrape_profiles.py to get fresh URLs

**"Can't find a page"**
→ Use search in Edit Page Details tab
→ Check if page was filtered out (min clients setting)


