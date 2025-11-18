# Quick Reference Card 📋

## Setup (One-Time)
```bash
pip install -r requirements.txt
$env:APIFY_TOKEN="your_token"
$env:OPENAI_API_KEY="your_key"
python main.py
```

## The 9 Categories

| Category | Description | Example |
|----------|-------------|---------|
| BLACK_THEME | African American targeted | @blacksuccesslive |
| MIXED_THEME | Diverse representation | @inspirationation00 |
| TEXT_ONLY | Text-based posts | @healersmindset |
| BLACK_BG_WHITE_TEXT | Black bg aesthetic | @rarementalities |
| GENERAL_WHITE_THEME | Caucasian focused | @investingmentors |
| BLACK_CELEBRITY | Black celeb accounts | @martinlawrence |
| WHITE_CELEBRITY | White celeb accounts | @steveaoki |
| STREAMER_YOUTUBER | Content creators | Gaming/streaming |
| PERSONAL_BRAND_ENTREPRENEUR | Business coaches | @justinp (competitors!) |

## CLI Quick Actions

| Option | Action | Use When |
|--------|--------|----------|
| 1 | Add client | New client joins |
| 2 | Scrape one client | Just added them |
| 3 | Scrape all clients | First time / monthly update |
| 4 | View analysis | Basic page ranking |
| **5** | **View by category** | **See categorized pages** |
| 6 | ROI analysis | Have pricing data |
| **7** | **AI Categorize (new only)** | **First time categorizing** |
| **8** | **Re-categorize all** | **Pages changed content** |
| 9 | Add price | Got promo quote |
| 10 | Export CSV | Need spreadsheet |
| 11 | Exit | Done for now |

## Promo Status Indicators

| Symbol | Status | Meaning | Action |
|--------|--------|---------|--------|
| 🟢 | Warm | Open to promos | Reach out! |
| ⚪ | Unknown | No signals | Try anyway |
| 🔴 | Not Open | Explicitly closed | Skip |

## Cost Calculator

| Pages | Low | High |
|-------|-----|------|
| 5 | $0.75 | $1.75 |
| 10 | $1.50 | $3.50 |
| 25 | $3.75 | $8.75 |
| 50 | $7.50 | $17.50 |
| 100 | $15 | $35 |

## Typical Workflow

```
1. Add clients (Option 1)
   └─> Do this when someone joins

2. Scrape following lists (Option 3)
   └─> Takes 2-5 min per client

3. View analysis (Option 4)
   └─> See which pages are popular

4. AI Categorize (Option 7)
   └─> Costs money, shows cost estimate
   └─> Extracts emails & promo status

5. View by category (Option 5)
   └─> See organized results
   └─> Focus on Warm pages

6. Reach out to Warm pages
   └─> Use the emails found

7. Add prices (Option 9)
   └─> When you get quotes

8. ROI analysis (Option 6)
   └─> Find best value pages

9. Book promotions!
   └─> Start with top 2-3
```

## Priority Pages

Target pages that are:
- ✅ Warm for promo
- ✅ Have contact email
- ✅ 3+ of your clients follow
- ✅ Concentration > 0.00005
- ✅ In relevant category

## Files to Know

| File | Purpose |
|------|---------|
| clients_data.json | Your database (backup this!) |
| ig_analysis.csv | Exported data |
| main.py | Main program |
| categorizer.py | AI logic |
| AI_CATEGORIZATION.md | Full category guide |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "APIFY_TOKEN not set" | Run `$env:APIFY_TOKEN="..."` |
| "OPENAI_API_KEY not set" | Run `$env:OPENAI_API_KEY="..."` (for option 7 only) |
| Category is wrong | Use Option 8 to re-categorize |
| No email found | Check their link in bio manually |
| Scraping fails | Account might be private |
| Cost too high | Only categorize pages with 3+ clients |

## When to Re-Run

| Task | Frequency |
|------|-----------|
| Add new clients | When they join |
| Scrape following | Monthly |
| Categorize pages | First time + every 6 months |
| Update prices | When you get new quotes |
| Export data | Weekly (for backup) |

## Best Practices

✅ **DO:**
- Start with 2-3 test pages
- Focus on Warm pages first
- Track which promos work
- Backup clients_data.json regularly

❌ **DON'T:**
- Categorize pages with <2 clients (waste of money)
- Skip the cost confirmation
- Contact pages marked "Not Open"
- Spam pages without permission

## Key Metrics Explained

**Concentration** = Your clients / Their followers
- Higher = more targeted
- Example: 5/50,000 = 0.0001 (good!)

**Value Score** = Concentration / Price  
- Higher = better deal
- Example: 0.0001 / $200 = 5e-7

**Cost per Client** = Price / Your clients
- Lower = better
- Example: $200 / 5 = $40 per client

## Quick Tips

💡 **Personal Brand Entrepreneurs = Competitors**
They have your exact audience but may not want to promote you.

💡 **Start Small**
Test 1-2 pages before committing to big campaigns.

💡 **Warm + Email = Priority**
These are your hottest leads.

💡 **Category Matters**
Don't promote on gaming/streamer pages if you coach business.

💡 **Concentration > Reach**
Better to reach 5 clients on a 10K page than 5 clients on a 1M page.

## Need Help?

1. **README.md** - Full documentation
2. **AI_CATEGORIZATION.md** - Category guide
3. **QUICKSTART.md** - 5-minute setup
4. **WORKFLOW.md** - Strategy guide

---

Save this card for quick reference! 🚀



