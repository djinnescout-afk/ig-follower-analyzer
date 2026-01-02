# Instagram Follower Analyzer 🎯

A tool to analyze which Instagram pages your coaching clients follow, helping you identify high-value promotional opportunities.

## What It Does

1. **Tracks Your Clients**: Store your clients' Instagram usernames
2. **Scrapes Following Lists**: Uses Apify to get who each client follows
3. **Cross-References Data**: Finds pages followed by multiple clients
4. **AI-Powered Categorization**: Automatically categorizes pages by type and theme using GPT-4 Vision
5. **Contact Detection**: Extracts contact emails and detects promo readiness
6. **Calculates Value Metrics**: Determines which pages give you the best ROI
7. **Price Analysis**: Add promo prices to calculate cost-effectiveness

## Metrics Explained

### Concentration Score
`clients_following / total_followers`

This shows what portion of a page's audience is YOUR clients. Higher = better targeting.

**Example**: If 3 of your clients follow a page with 150,000 followers:
- Concentration = 3 / 150,000 = 0.00002 (or 1 client per 50,000 followers)

### Value Score (Concentration per Dollar)
`(clients_following / total_followers) / price`

This is your **best metric** - it combines reach efficiency with cost.

**Example**: Same page charges $500 for a promo:
- Value Score = 0.00002 / 500 = 4e-8 concentration per dollar
- Compare this across different pages to find best deals!

### Cost Per Client
`price / clients_following`

How much you pay to reach each of YOUR clients.

**Example**: $500 / 3 clients = $166.67 per client reached

## AI Categorization

The tool can automatically categorize Instagram pages into these types:

### Categories

1. **BLACK THEME PAGES**: African American targeted content with Black individuals prominently featured
2. **MIXED THEME PAGES**: Diverse representation with mix of ethnicities
3. **TEXT ONLY THEME PAGES**: Pure text-based posts with minimal imagery
4. **BLACK BG WHITE TEXT THEME PAGES**: Black background with white text aesthetic
5. **GENERAL/WHITE THEME PAGES**: Caucasian-focused content
6. **BLACK CELEBRITY**: Black celebrity or public figure accounts
7. **WHITE CELEBRITY**: White celebrity or public figure accounts
8. **STREAMER/YOUTUBER**: Content creators, streamers, YouTubers
9. **PERSONAL BRAND ENTREPRENEUR**: Business coaches, entrepreneurs (your competitors!)

### How It Works

The AI categorization uses:
- **GPT-4 Vision API** to analyze profile pictures and recent posts
- **Text analysis** of bios and captions for language patterns
- **Pattern recognition** for visual themes and demographics

### Contact & Promo Detection

The tool automatically:
- ✅ Extracts email addresses from profiles
- ✅ Detects promo openness (keywords like "collab", "business inquiries")
- ✅ Marks pages as "Warm" for promo if indicators found

### Cost for Categorization

Per page analyzed:
- Apify scraping: ~$0.10-0.30
- GPT-4 Vision: ~$0.01-0.02
- **Total: ~$0.15-0.35 per page**

The tool asks for confirmation before categorizing and shows cost estimates.

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Get your API tokens**:
   
   **Required: Apify (for scraping)**
   - Go to https://console.apify.com/account/integrations
   - Copy your API token
   - Set environment variable: `APIFY_TOKEN=your_token_here`
   
   **Optional: OpenAI (for AI categorization)**
   - Go to https://platform.openai.com/api-keys
   - Create an API key
   - Set environment variable: `OPENAI_API_KEY=your_key_here`
   
   **Setting Environment Variables:**
   - Windows PowerShell: `$env:APIFY_TOKEN="your_token"` and `$env:OPENAI_API_KEY="your_key"`
   - Windows CMD: `set APIFY_TOKEN=your_token` and `set OPENAI_API_KEY=your_key`
   - Linux/Mac: `export APIFY_TOKEN="your_token"` and `export OPENAI_API_KEY="your_key"`

4. **Run the tool**:
```bash
python main.py
```

## Usage Flow

### Step 1: Add Your Clients
```
Select option: 1
Client name: John Smith
Instagram username: johnsmith123
```

### Step 2: Scrape Their Following Lists
```
Select option: 2
Instagram username to scrape: johnsmith123
```

Do this for each client, or use option 3 to scrape all at once.

### Step 3: View Analysis
```
Select option: 4
Minimum clients following: 2
```

This shows pages followed by 2+ clients, sorted by popularity.

### Step 4: Add Pricing (Optional)
```
Select option: 5
Page username: marketingpage
Promo price ($): 500
```

### Step 5: AI Categorize Pages (Optional)
```
Select option: 7
Minimum clients following: 2
```

This will use GPT-4 Vision to automatically:
- Categorize pages by type (BLACK THEME, PERSONAL BRAND, etc.)
- Extract contact emails
- Detect if they're open to promotions
- Costs ~$0.15-0.35 per page analyzed

### Step 6: View Category Report
```
Select option: 5
```

See pages grouped by category with contact info and promo status!

### Step 7: View ROI Analysis
```
Select option: 6
```

See which pages give you the best value for your money!

## Understanding the Results

The tool ranks pages by **Value Score** (concentration per dollar). Here's why this matters:

### Good vs Bad Targets

**Good Target**:
- Page: @nichetarget
- Your clients following: 5
- Total followers: 50,000
- Concentration: 0.0001 (1 per 10,000)
- Price: $200
- Value Score: 5e-7 ← **GOOD**
- You're reaching 5 clients for $200 = $40 per client

**Bad Target**:
- Page: @hugemedia
- Your clients following: 8
- Total followers: 2,000,000
- Concentration: 0.000004 (1 per 250,000)
- Price: $5,000
- Value Score: 8e-10 ← **BAD**
- You're reaching 8 clients for $5,000 = $625 per client

Even though the second page reaches MORE of your clients (8 vs 5), it's way more expensive per client!

## Files Created

- `clients_data.json` - Stores all your client and page data
- `ig_analysis.csv` - Export of your analysis (option 7)

## Important Notes

### Costs
- Apify charges per API usage
- The Instagram Following Scraper typically costs $0.05-0.50 per scrape
- Check pricing at: https://apify.com/louisdeconinck/instagram-following-scraper

### Rate Limits
- Instagram has rate limits
- Don't scrape too many accounts at once
- Spread out your scraping over time

### Ethics
- Only scrape your actual clients (with their consent)
- This is for market research, not spam
- Follow Instagram's terms of service

## Recommended Formula

For the "which formula is best?" question:

**Best: Concentration per Dollar** `(clients/followers) / price`

Why? It considers:
- How targeted the audience is (clients/followers)
- How much it costs (price)
- Balances both reach and efficiency

Alternative formulas like `clients/price` don't account for audience size, so a page with 10M followers charging $100 would look better than a niche page with 10K followers charging $50, even if the niche page is more targeted to your audience.

## Troubleshooting

**"APIFY_TOKEN not set"**
- Make sure you created a `.env` file
- Or set it in your environment: `set APIFY_TOKEN=your_token` (Windows)

**"Actor not found"**
- Make sure you have Apify credits
- The actor name might have changed - check https://apify.com/store

**Scraping fails**
- Check if the Instagram username is correct
- Make sure the account is public (private accounts can't be scraped)
- You might have hit rate limits - wait a bit

## Staging Environment

This project includes a staging environment for safe testing before deploying to production.

### Quick Start

1. **Staging Branch**: Code on the `staging` branch auto-deploys to staging
2. **Data Sync**: Use `scripts/sync_prod_to_staging.py` to sync production data
3. **Workflow**: Feature → Staging → Test → Production

### Documentation

- **Full Guide**: See `docs/STAGING_ENVIRONMENT.md` for complete setup instructions
- **Git Workflow**: See `docs/GIT_WORKFLOW.md` for branch management
- **Quick Reference**: See `scripts/README_STAGING.md` for common commands

### Key Points

- Staging uses a separate Supabase project (complete isolation)
- Data sync is one-way: production → staging only
- Staging branch auto-deploys on every push
- Always test on staging before deploying to production

## Future Enhancements

- [ ] Automatic price checking (if pages have standard rates posted)
- [ ] Track engagement rates of pages
- [ ] Schedule automatic re-scraping to track changes
- [ ] Web dashboard for easier visualization
- [ ] Email alerts when high-value pages are found

## License

Free to use for your business!

