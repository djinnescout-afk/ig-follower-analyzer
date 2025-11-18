# Quick Start Guide 🚀

## Setup (5 minutes)

### 1. Install Python packages
```bash
pip install -r requirements.txt
```

### 2. Get your API tokens

**Required: Apify (for scraping)**
1. Go to https://apify.com and create a free account
2. Navigate to https://console.apify.com/account/integrations
3. Copy your API token

**Optional: OpenAI (for AI categorization)**
1. Go to https://platform.openai.com/api-keys
2. Create an API key

### 3. Set your API tokens
**Windows PowerShell:**
```powershell
$env:APIFY_TOKEN="your_token_here"
$env:OPENAI_API_KEY="your_key_here"
```

**Windows CMD:**
```cmd
set APIFY_TOKEN=your_token_here
set OPENAI_API_KEY=your_key_here
```

**Linux/Mac:**
```bash
export APIFY_TOKEN="your_token_here"
export OPENAI_API_KEY="your_key_here"
```

Or create a `config.py` file (copy from `config_example.py`)

Note: OpenAI key is only needed if you want AI categorization. The tool works without it for basic analysis.

## First Use (10 minutes)

### 1. Run the tool
```bash
python main.py
```

### 2. Add your first client
```
Select option: 1
Client name: John Smith
Instagram username: johnsmith
```

### 3. Scrape their following list
```
Select option: 2
Instagram username to scrape: johnsmith
```

⏳ This takes 1-3 minutes depending on how many accounts they follow.

### 4. Add more clients
Repeat steps 2-3 for each client (you need at least 2 clients for cross-referencing)

### 5. View the analysis
```
Select option: 4
Minimum clients following: 2
```

🎉 You'll now see which pages multiple clients follow!

### 6. (Optional) AI Categorize Pages
```
Select option: 7
Minimum clients following: 2
```

This will automatically categorize pages and find contact info. Requires OpenAI API key.

## Understanding Your Results

The tool shows you:
- **Clients Following**: How many of YOUR clients follow this page
- **Total Followers**: How big the page is
- **Concentration**: What % of their audience is your clients (higher = more targeted)
- **Followers per Client**: How "spread out" your clients are in their audience

### What to Look For
✅ **Good targets**: High client count, medium-sized pages (10k-500k followers)
❌ **Bad targets**: Low client count OR massive pages (millions of followers)

## Adding Prices (Optional but Recommended)

Once you contact pages and get their promo prices:

```
Select option: 5
Page username: fitnesscoach
Promo price ($): 250
```

Then view ROI analysis:
```
Select option: 6
```

This shows which pages give you the **best value per dollar**!

## Tips

### How Many Clients Do I Need?
- **Minimum**: 2-3 clients to start seeing patterns
- **Good**: 5-10 clients for meaningful data
- **Great**: 20+ clients for strong insights

### Cost Expectations
- Apify Instagram Following Scraper: ~$0.05-0.50 per client
- If each client follows 500 accounts: ~$0.10 per scrape
- 10 clients = ~$1.00 total

### Best Practices
1. Start with your most engaged clients (they follow accounts they actually care about)
2. Scrape during different times of day
3. Export to CSV after each batch for backup
4. Update following lists every 2-3 months (people's interests change)

## Common Issues

**"APIFY_TOKEN not set"**
- Run the export/set command in the SAME terminal window where you run `python main.py`

**"Rate limit exceeded"**
- Wait 15-30 minutes before scraping again
- Don't scrape more than 10 clients in one hour

**"Private account"**
- You can only scrape public Instagram accounts
- Ask your client to temporarily make their account public, or use an account that follows them

**Scraping takes forever**
- Normal for accounts that follow 1000+ pages
- It might take 5-10 minutes for very active users

## Next Steps

After your first analysis:
1. **Identify top 10 pages** (most clients following)
2. **Research their content** - do they align with your brand?
3. **Contact them** for promo pricing
4. **Add prices** to the tool
5. **Run ROI analysis** to find best deals
6. **Start with 1-2 test promos** on highest-value pages

## Need Help?

Check the full README.md for:
- Detailed metric explanations
- Understanding the formulas
- Advanced usage examples
- Troubleshooting guide

---

Happy analyzing! 📊✨

