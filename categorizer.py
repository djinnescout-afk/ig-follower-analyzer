"""
AI-Powered Instagram Page Categorization Module
Uses GPT-4 Vision API and Apify to automatically categorize Instagram pages
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from apify_client import ApifyClient
from openai import OpenAI


# Category definitions
CATEGORIES = {
    "BLACK_THEME": "African American targeted content with Black individuals prominently featured",
    "MIXED_THEME": "Diverse representation with mix of ethnicities in content",
    "TEXT_ONLY": "Pure text-based posts with minimal or no imagery of people",
    "BLACK_BG_WHITE_TEXT": "Black background with white text aesthetic",
    "GENERAL_WHITE_THEME": "Caucasian-focused content with white individuals predominantly featured",
    "BLACK_CELEBRITY": "Black celebrity or public figure personal account",
    "WHITE_CELEBRITY": "White celebrity or public figure personal account",
    "STREAMER_YOUTUBER": "Content creator, streamer, or YouTuber",
    "PERSONAL_BRAND_ENTREPRENEUR": "Business coach, entrepreneur, or self-improvement content creator"
}


class InstagramCategorizer:
    def __init__(self, apify_token: str, openai_api_key: str):
        """Initialize with API tokens"""
        self.apify_client = ApifyClient(apify_token)
        self.openai_client = OpenAI(api_key=openai_api_key)
        
    def scrape_page_content(self, username: str) -> Dict:
        """
        Scrape Instagram page content including profile, posts, and highlights
        Returns: Dict with profile_pic, bio, posts (images + captions), highlights
        """
        print(f"  📥 Scraping profile data for @{username}...")
        
        try:
            # Use Apify Instagram Profile Scraper
            run_input = {
                "usernames": [username],
                "resultsLimit": 12,  # Get 12 recent posts
            }
            
            run = self.apify_client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            
            # Check run status - if it failed, return None
            run_status = run.get("status", "").upper()
            if run_status not in ["SUCCEEDED", "RUNNING"]:
                print(f"  ⚠️  Apify run failed with status: {run_status}")
                return None
            
            # Fetch results
            items = list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                print(f"  ⚠️  No data found for @{username}")
                return None
            
            profile_data = items[0]
            
            # Validate that we got actual profile data (not just an error response)
            # Check for key fields that should always be present in a valid profile
            profile_pic_url = profile_data.get("profilePicUrl", "")
            username_from_data = profile_data.get("username", "").lower().strip()
            expected_username = username.lower().strip()
            
            # A valid profile should have either:
            # 1. A profile picture URL, OR
            # 2. A matching username (case-insensitive)
            # If neither exists, this is likely an error/empty response
            has_profile_pic = bool(profile_pic_url and profile_pic_url.strip())
            username_matches = username_from_data == expected_username
            
            if not has_profile_pic and not username_matches:
                print(f"  ⚠️  Invalid profile data returned for @{username} (no profile pic and username mismatch)")
                return None
            
            # Download profile picture as base64 to prevent URL expiration
            profile_pic_base64 = None
            profile_pic_mime = None
            if profile_pic_url:
                try:
                    import base64
                    pic_response = requests.get(profile_pic_url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    pic_response.raise_for_status()
                    
                    profile_pic_base64 = base64.b64encode(pic_response.content).decode('utf-8')
                    content_type = pic_response.headers.get('content-type', 'image/jpeg')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        profile_pic_mime = 'image/jpeg'
                    elif 'png' in content_type:
                        profile_pic_mime = 'image/png'
                    elif 'webp' in content_type:
                        profile_pic_mime = 'image/webp'
                    else:
                        profile_pic_mime = 'image/jpeg'
                except Exception as e:
                    print(f"  ⚠️  Failed to download profile pic: {str(e)[:80]}")
            
            # Extract relevant information
            result = {
                "username": username,
                "full_name": profile_data.get("fullName", ""),
                "bio": profile_data.get("biography", ""),
                "profile_pic_url": profile_pic_url,  # Keep for reference
                "profile_pic_base64": profile_pic_base64,  # Base64 encoded
                "profile_pic_mime_type": profile_pic_mime,  # MIME type
                "follower_count": profile_data.get("followersCount", 0),
                "is_verified": profile_data.get("verified", False),
                "is_business": profile_data.get("isBusinessAccount", False),
                "business_email": profile_data.get("businessEmail"),
                "business_phone": profile_data.get("businessPhoneNumber"),
                "external_url": profile_data.get("externalUrl"),
                "posts": [],
                "highlights": profile_data.get("highlightsData", []),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Extract posts with images and captions
            # Download and store images as base64 to prevent URL expiration
            import base64
            latest_posts = profile_data.get("latestPosts", [])[:12]
            for post in latest_posts:
                post_data = {
                    "caption": post.get("caption", ""),
                    "image_url": None,  # Keep original URL for reference
                    "image_base64": None,  # Base64 encoded image data
                    "image_mime_type": None,  # MIME type (image/jpeg, image/png, etc.)
                    "type": post.get("type", "")
                }
                
                # Get image URL
                image_url = None
                if post.get("displayUrl"):
                    image_url = post.get("displayUrl")
                elif post.get("images"):
                    image_url = post["images"][0] if post["images"] else None
                
                if image_url:
                    post_data["image_url"] = image_url
                    
                    # Download and convert to base64
                    try:
                        img_response = requests.get(image_url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        img_response.raise_for_status()
                        
                        # Convert to base64
                        image_data = base64.b64encode(img_response.content).decode('utf-8')
                        
                        # Determine MIME type
                        content_type = img_response.headers.get('content-type', 'image/jpeg')
                        if 'jpeg' in content_type or 'jpg' in content_type:
                            mime_type = 'image/jpeg'
                        elif 'png' in content_type:
                            mime_type = 'image/png'
                        elif 'webp' in content_type:
                            mime_type = 'image/webp'
                        else:
                            mime_type = 'image/jpeg'  # Default
                        
                        post_data["image_base64"] = image_data
                        post_data["image_mime_type"] = mime_type
                    except Exception as e:
                        print(f"  ⚠️  Failed to download post image: {str(e)[:80]}")
                        # Continue without base64 - will try to use URL as fallback
                    
                    result["posts"].append(post_data)
            
            # Detect promo openness from bio and highlights
            bio = result.get("bio", "")
            highlights = result.get("highlights", [])
            promo_status, promo_indicators = self.detect_promo_openness(bio, highlights)
            result["promo_status"] = promo_status
            result["promo_indicators"] = promo_indicators
            
            # Extract website URL from bio text and external_url
            website_url = result.get("external_url", "")  # Instagram's "link in bio"
            
            # Also check bio text for URLs
            url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*'
            bio_urls = re.findall(url_pattern, bio)
            
            # Prefer external_url (Instagram's official link), but use bio URL if external_url is empty
            if not website_url and bio_urls:
                # Clean up the first URL found in bio
                website_url = bio_urls[0]
                if not website_url.startswith(('http://', 'https://')):
                    website_url = 'https://' + website_url
            
            result["website_url"] = website_url if website_url else None
            
            # Check website for promo mentions if URL exists
            website_promo_info = None
            if website_url:
                website_promo_info = self.check_website_for_promo(website_url)
                if website_promo_info:
                    result["website_promo_info"] = website_promo_info
            
            if promo_status == "Warm":
                print(f"  🟢 Promo Status: WARM ({len(promo_indicators)} indicators)")
            else:
                print(f"  ⚪ Promo Status: {promo_status}")
            
            if website_url:
                print(f"  🔗 Website: {website_url}")
                if website_promo_info:
                    if website_promo_info.get("has_promo_mention"):
                        print(f"  ✅ Website mentions promo!")
                    if website_promo_info.get("has_promo_page"):
                        print(f"  ✅ Website has promo/buy page!")
                    if website_promo_info.get("has_contact_email"):
                        print(f"  ✅ Website has contact email for promo!")
                    if website_promo_info.get("has_contact_form"):
                        print(f"  ✅ Website has contact form!")
            
            print(f"  ✅ Scraped {len(result['posts'])} posts for @{username}")
            return result
            
        except Exception as e:
            print(f"  ❌ Error scraping @{username}: {str(e)}")
            return None
    
    def extract_contact_email(self, bio: str, business_email: Optional[str] = None) -> Optional[str]:
        """Extract email address from bio or business email field"""
        # If business email is provided by API, use it
        if business_email:
            return business_email
        
        # Otherwise, search bio with regex
        if not bio:
            return None
        
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, bio)
        
        if matches:
            return matches[0]  # Return first email found
        
        return None
    
    def check_website_for_promo(self, website_url: str) -> Optional[Dict]:
        """
        Check website for promo mentions, promo/buy pages, and contact emails
        Returns: Dict with has_promo_mention, has_promo_page, has_contact_email, and details
        """
        try:
            # Fetch website content with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(website_url, timeout=10, headers=headers, allow_redirects=True)
            response.raise_for_status()
            
            html_content = response.text.lower()
            
            # Promo-related keywords to search for
            promo_keywords = [
                "promo", "promotion", "advertise", "advertising", "sponsor", "sponsorship",
                "collab", "collaboration", "partnership", "brand deal", "brand deals",
                "business inquiry", "business inquiries", "work with us", "work with me",
                "contact for", "email for", "dm for", "reach out", "book", "booking"
            ]
            
            # Check for promo mentions in text
            has_promo_mention = any(keyword in html_content for keyword in promo_keywords)
            
            # Look for promo/buy page links
            promo_page_keywords = ["promo", "advertise", "sponsor", "collab", "partnership", "book", "buy", "pricing", "rates"]
            has_promo_page = False
            promo_page_urls = []
            
            # Check for contact forms
            has_contact_form = False
            contact_form_info = []
            
            # Try to parse HTML with BeautifulSoup if available, otherwise use regex
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '').lower()
                    link_text = link.get_text().lower()
                    
                    # Check if link URL or text contains promo keywords
                    if any(keyword in href or keyword in link_text for keyword in promo_page_keywords):
                        has_promo_page = True
                        full_url = href
                        if not full_url.startswith(('http://', 'https://')):
                            # Make it absolute URL
                            from urllib.parse import urljoin
                            full_url = urljoin(website_url, href)
                        promo_page_urls.append(full_url)
                
                # Find contact forms
                forms = soup.find_all('form')
                contact_form_keywords = ["contact", "inquiry", "inquiries", "message", "reach", "get in touch", "reach out"]
                
                for form in forms:
                    form_html = str(form).lower()
                    form_id = form.get('id', '').lower()
                    form_class = ' '.join(form.get('class', [])).lower()
                    form_action = form.get('action', '').lower()
                    
                    # Check if form is related to contact/promo
                    is_contact_form = (
                        any(keyword in form_html for keyword in contact_form_keywords) or
                        any(keyword in form_id for keyword in contact_form_keywords) or
                        any(keyword in form_class for keyword in contact_form_keywords) or
                        any(keyword in form_action for keyword in contact_form_keywords) or
                        any(keyword in form_html for keyword in promo_keywords)
                    )
                    
                    if is_contact_form:
                        has_contact_form = True
                        # Try to find form action URL
                        form_action_url = form.get('action', '')
                        if form_action_url:
                            if not form_action_url.startswith(('http://', 'https://')):
                                from urllib.parse import urljoin
                                form_action_url = urljoin(website_url, form_action_url)
                            contact_form_info.append({
                                "url": form_action_url,
                                "has_email_field": 'type="email"' in form_html or 'name="email"' in form_html or 'id="email"' in form_html,
                                "has_message_field": 'textarea' in form_html or 'name="message"' in form_html or 'id="message"' in form_html
                            })
                        else:
                            contact_form_info.append({
                                "url": website_url,  # Form on same page
                                "has_email_field": 'type="email"' in form_html or 'name="email"' in form_html or 'id="email"' in form_html,
                                "has_message_field": 'textarea' in form_html or 'name="message"' in form_html or 'id="message"' in form_html
                            })
                
                # Extract email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, html_content)
                
                # Check if email is mentioned near promo keywords
                has_contact_email = False
                contact_emails = []
                for email in set(emails):  # Remove duplicates
                    # Check if email appears near promo keywords (within 200 chars)
                    email_pos = html_content.find(email.lower())
                    if email_pos != -1:
                        context = html_content[max(0, email_pos-200):email_pos+200]
                        if any(keyword in context for keyword in promo_keywords):
                            has_contact_email = True
                            contact_emails.append(email)
                
            except ImportError:
                # Fallback to regex if BeautifulSoup not available
                # Look for links in HTML
                link_pattern = r'href=["\']([^"\']+)["\']'
                links = re.findall(link_pattern, html_content)
                
                for href in links:
                    if any(keyword in href.lower() for keyword in promo_page_keywords):
                        has_promo_page = True
                        full_url = href
                        if not full_url.startswith(('http://', 'https://')):
                            from urllib.parse import urljoin
                            full_url = urljoin(website_url, href)
                        promo_page_urls.append(full_url)
                
                # Check for contact forms using regex
                contact_form_keywords = ["contact", "inquiry", "inquiries", "message", "reach", "get in touch", "reach out"]
                form_pattern = r'<form[^>]*>.*?</form>'
                forms = re.findall(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
                
                for form_html in forms:
                    form_lower = form_html.lower()
                    is_contact_form = (
                        any(keyword in form_lower for keyword in contact_form_keywords) or
                        any(keyword in form_lower for keyword in promo_keywords)
                    )
                    
                    if is_contact_form:
                        has_contact_form = True
                        # Extract form action
                        action_match = re.search(r'action=["\']([^"\']+)["\']', form_html, re.IGNORECASE)
                        form_action_url = action_match.group(1) if action_match else website_url
                        
                        if form_action_url and not form_action_url.startswith(('http://', 'https://')):
                            from urllib.parse import urljoin
                            form_action_url = urljoin(website_url, form_action_url)
                        
                        contact_form_info.append({
                            "url": form_action_url,
                            "has_email_field": bool(re.search(r'type=["\']email["\']|name=["\']email["\']|id=["\']email["\']', form_html, re.IGNORECASE)),
                            "has_message_field": bool(re.search(r'<textarea|name=["\']message["\']|id=["\']message["\']', form_html, re.IGNORECASE))
                        })
                
                # Extract emails
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, html_content, re.IGNORECASE)
                
                has_contact_email = False
                contact_emails = []
                for email in set(emails):
                    email_lower = email.lower()
                    email_pos = html_content.find(email_lower)
                    if email_pos != -1:
                        context = html_content[max(0, email_pos-200):email_pos+200]
                        if any(keyword in context for keyword in promo_keywords):
                            has_contact_email = True
                            contact_emails.append(email)
            
            # Return results
            result = {
                "has_promo_mention": has_promo_mention,
                "has_promo_page": has_promo_page,
                "has_contact_email": has_contact_email,
                "has_contact_form": has_contact_form,
                "promo_page_urls": promo_page_urls[:5] if promo_page_urls else [],  # Limit to 5
                "contact_emails": contact_emails[:3] if contact_emails else [],  # Limit to 3
                "contact_forms": contact_form_info[:3] if contact_form_info else []  # Limit to 3
            }
            
            return result if (has_promo_mention or has_promo_page or has_contact_email or has_contact_form) else None
            
        except Exception as e:
            # Silently fail - don't break scraping if website check fails
            print(f"  ⚠️  Could not check website: {str(e)[:80]}")
            return None
    
    def detect_promo_openness(self, bio: str, highlights: List[Dict]) -> Tuple[str, List[str]]:
        """
        Detect if page is open to promotions
        Returns: (promo_status, indicators_list)
        """
        indicators = []
        
        if not bio:
            bio = ""
        
        bio_lower = bio.lower()
        
        # Check bio for promo keywords
        promo_keywords = [
            "business inquiries", "business inquiry", "collab", "collaboration",
            "partnerships", "sponsorship", "sponsor", "advertising", "promo",
            "dm for business", "dm for collab", "work with me", "brand deals",
            "email for business", "contact for business", "booking", "management"
        ]
        
        for keyword in promo_keywords:
            if keyword in bio_lower:
                indicators.append(f"Bio mentions: '{keyword}'")
        
        # Check highlights for promo-related titles
        if highlights:
            promo_highlight_titles = [
                "promo", "collab", "work", "business", "partnerships", "ads",
                "sponsored", "advertising", "deals", "brand", "contact"
            ]
            
            for highlight in highlights:
                title = highlight.get("title", "").lower()
                for promo_title in promo_highlight_titles:
                    if promo_title in title:
                        indicators.append(f"Highlight: '{highlight.get('title')}'")
                        break
        
        # Determine status
        if len(indicators) >= 2:
            status = "Warm"
        elif len(indicators) == 1:
            status = "Warm"
        else:
            status = "Unknown"
        
        return status, indicators
    
    def analyze_with_vision(self, profile_data: Dict) -> Tuple[str, float, str]:
        """
        Analyze profile and posts with GPT-4 Vision
        Returns: (category, confidence, reasoning)
        """
        print(f"  🤖 Analyzing with GPT-4 Vision...")
        
        # Prepare image URLs (profile pic + up to 9 posts)
        image_urls = []
        
        if profile_data["profile_pic_url"]:
            image_urls.append(profile_data["profile_pic_url"])
        
        for post in profile_data["posts"][:9]:
            if post["image_url"]:
                image_urls.append(post["image_url"])
        
        if not image_urls:
            print(f"  ⚠️  No images available for analysis")
            return "TEXT_ONLY", 0.5, "No images available"
        
        # Collect captions for text analysis
        captions = [post["caption"] for post in profile_data["posts"] if post["caption"]]
        caption_text = "\n\n".join(captions[:5])  # First 5 captions
        
        # Build the prompt
        prompt = self._build_vision_prompt(
            username=profile_data["username"],
            full_name=profile_data["full_name"],
            bio=profile_data["bio"],
            captions=caption_text,
            num_images=len(image_urls)
        )
        
        # Prepare messages with images
        # Download images and convert to base64 (Instagram URLs expire quickly)
        content = [{"type": "text", "text": prompt}]
        
        import base64
        import requests
        from io import BytesIO
        
        images_added = 0
        for url in image_urls[:10]:  # Limit to 10 images max
            try:
                # Download image
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Convert to base64
                image_data = base64.b64encode(response.content).decode('utf-8')
                
                # Determine image format
                content_type = response.headers.get('content-type', 'image/jpeg')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    mime_type = 'image/jpeg'
                elif 'png' in content_type:
                    mime_type = 'image/png'
                elif 'webp' in content_type:
                    mime_type = 'image/webp'
                else:
                    mime_type = 'image/jpeg'  # Default
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}",
                        "detail": "low"  # Use low detail to save costs
                    }
                })
                images_added += 1
            except Exception as e:
                print(f"  ⚠️  Failed to download image {images_added + 1}: {str(e)[:80]}")
                continue  # Skip this image and continue with others
        
        if images_added == 0:
            print(f"  ❌ WARNING: No images could be downloaded! This will likely cause categorization to fail.")
        else:
            print(f"  📸 Successfully prepared {images_added} image(s) for analysis")
        
        try:
            if images_added == 0:
                print(f"  ⚠️  No images available - categorization may be less accurate")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest vision model
                messages=[{"role": "user", "content": content}],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent categorization
            )
            
            result_text = response.choices[0].message.content
            print(f"  🔍 Raw API response: {result_text[:200]}...")  # Debug: show first 200 chars
            
            # Parse JSON response
            result = self._parse_vision_response(result_text)
            
            if result['category'] == "UNKNOWN":
                print(f"  ⚠️  WARNING: Category parsed as UNKNOWN. Raw response was: {result_text[:300]}")
            
            print(f"  ✅ Category: {result['category']} ({result['confidence']*100:.0f}% confidence)")
            return result["category"], result["confidence"], result["reasoning"]
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Vision API error: {error_msg}")
            if "rate limit" in error_msg.lower():
                print(f"  ⏳ Rate limited - please wait before retrying")
            elif "invalid" in error_msg.lower() or "400" in error_msg:
                print(f"  ⚠️  Invalid request - check image format or API key")
            return "UNKNOWN", 0.0, f"Error: {error_msg}"
    
    def _build_vision_prompt(self, username: str, full_name: str, bio: str, 
                            captions: str, num_images: int) -> str:
        """Build the GPT-4 Vision prompt for categorization"""
        
        categories_description = "\n".join([
            f"{i+1}. {key}: {desc}"
            for i, (key, desc) in enumerate(CATEGORIES.items())
        ])
        
        prompt = f"""You are analyzing an Instagram page to categorize it. Here's the profile information:

**Username:** @{username}
**Name:** {full_name}
**Bio:** {bio}

**Sample Captions:**
{captions[:500] if captions else "No captions available"}

**Images Provided:** {num_images} images (1 profile picture + recent posts)

Please analyze the visual content and text to categorize this page into ONE of these categories:

{categories_description}

**Key Analysis Points:**
- Look at the people featured in the images (skin tone, ethnicity)
- Analyze the visual style (text overlays, backgrounds, design aesthetic)
- Consider the language style in captions (formal business, motivational, AAVE patterns, casual)
- Check if this is a celebrity (verified + millions of followers + personal brand)
- Determine if it's a business/entrepreneur coach vs entertainment content creator

**Important Distinctions:**
- BLACK_THEME: Specifically targets African American audience, features Black individuals prominently
- MIXED_THEME: Shows diversity, not focused on one ethnicity
- TEXT_ONLY: Mostly or entirely text-based posts, minimal photos of people
- BLACK_BG_WHITE_TEXT: Specific aesthetic with black backgrounds and white text overlay
- PERSONAL_BRAND_ENTREPRENEUR: Focused on business/self-improvement value content (competitors)
- STREAMER_YOUTUBER: Entertainment-focused content creators

Return your analysis as JSON in this exact format:
{{
  "category": "CATEGORY_NAME",
  "confidence": 0.85,
  "reasoning": "Brief explanation of why this category fits"
}}

**CRITICAL: Use the EXACT category name from the list above (e.g., "BLACK_THEME", "GENERAL_WHITE_THEME", "PERSONAL_BRAND_ENTREPRENEUR").**
**Do NOT use variations like "Black Theme" or "White Theme" - use the exact underscore format shown above.**

Be decisive. Choose the BEST fitting category even if some overlap exists."""
        
        return prompt
    
    def _parse_vision_response(self, response_text: str) -> Dict:
        """Parse the JSON response from GPT-4 Vision"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Try multiple JSON extraction methods
            result = None
            
            # Method 1: Try to find JSON block with proper braces matching
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except:
                    pass
            
            # Method 2: Try parsing the whole response
            if not result:
                try:
                    result = json.loads(response_text)
                except:
                    pass
            
            # Method 3: Try to extract JSON from markdown code blocks
            if not result:
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if code_block_match:
                    try:
                        result = json.loads(code_block_match.group(1))
                    except:
                        pass
            
            if not result:
                raise ValueError("Could not extract valid JSON from response")
            
            # Validate and normalize
            category = result.get("category", "UNKNOWN").upper().strip()
            
            # Remove underscores and normalize spacing for matching
            category_normalized = category.replace("_", " ").replace("-", " ")
            
            # Map variations to standard categories
            if category not in CATEGORIES:
                # Try exact match first
                found_match = False
                for cat_key in CATEGORIES.keys():
                    cat_key_normalized = cat_key.replace("_", " ").replace("-", " ")
                    # Check if category contains key or vice versa
                    if (cat_key.upper() in category or 
                        category in cat_key.upper() or
                        cat_key_normalized.upper() in category_normalized or
                        category_normalized in cat_key_normalized.upper()):
                        category = cat_key
                        found_match = True
                        break
                
                if not found_match:
                    # Last resort: try partial word matching
                    category_words = category_normalized.split()
                    for cat_key in CATEGORIES.keys():
                        cat_key_words = cat_key.replace("_", " ").split()
                        if any(word.upper() in [w.upper() for w in cat_key_words] for word in category_words if len(word) > 3):
                            category = cat_key
                            found_match = True
                            break
                    
                    if not found_match:
                        print(f"  ⚠️  Category '{category}' not found in valid categories. Valid options: {list(CATEGORIES.keys())}")
                        category = "UNKNOWN"
            
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
            
            reasoning = result.get("reasoning", "No reasoning provided")
            
            return {
                "category": category,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            print(f"  ⚠️  Error parsing response: {e}")
            print(f"  📄 Response text was: {response_text[:500]}")
            return {
                "category": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}"
            }
    
    def categorize_page(self, username: str) -> Optional[Dict]:
        """
        Main function to categorize a single page
        Returns full categorization result or None if failed
        """
        print(f"\n🔍 Categorizing @{username}...")
        
        # Step 1: Scrape page content
        profile_data = self.scrape_page_content(username)
        if not profile_data:
            return None
        
        # Step 2: Extract contact email
        contact_email = self.extract_contact_email(
            profile_data["bio"],
            profile_data.get("business_email")
        )
        
        if contact_email:
            print(f"  📧 Email found: {contact_email}")
        
        # Step 3: Detect promo openness
        promo_status, promo_indicators = self.detect_promo_openness(
            profile_data["bio"],
            profile_data.get("highlights", [])
        )
        
        if promo_status == "Warm":
            print(f"  🟢 Promo Status: WARM ({len(promo_indicators)} indicators)")
        
        # Step 4: AI Vision analysis
        category, confidence, reasoning = self.analyze_with_vision(profile_data)
        
        # Compile results
        result = {
            "username": username,
            "category": category,
            "category_confidence": confidence,
            "contact_email": contact_email,
            "promo_status": promo_status,
            "promo_indicators": promo_indicators,
            "last_categorized": datetime.now().isoformat(),
            "reasoning": reasoning
        }
        
        return result
    
    def categorize_pages_batch(self, usernames: List[str], 
                               show_cost_estimate: bool = True) -> Dict[str, Dict]:
        """
        Categorize multiple pages in batch
        Returns dict mapping username to categorization result
        """
        num_pages = len(usernames)
        
        if show_cost_estimate:
            # Estimate costs
            apify_cost = num_pages * 0.20  # ~$0.20 per scrape
            vision_cost = num_pages * 0.02  # ~$0.02 per analysis (10 images)
            total_cost = apify_cost + vision_cost
            
            print(f"\n💰 Cost Estimate:")
            print(f"   Apify scraping: ~${apify_cost:.2f}")
            print(f"   GPT-4 Vision: ~${vision_cost:.2f}")
            print(f"   Total: ~${total_cost:.2f} for {num_pages} pages")
            print()
            
            confirm = input(f"Proceed with categorizing {num_pages} pages? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Cancelled")
                return {}
        
        results = {}
        
        for i, username in enumerate(usernames, 1):
            print(f"\n[{i}/{num_pages}] Processing @{username}")
            
            result = self.categorize_page(username)
            if result:
                results[username] = result
            else:
                print(f"  ⚠️  Skipped @{username}")
        
        print(f"\n✅ Completed! Categorized {len(results)}/{num_pages} pages")
        return results


def test_categorizer():
    """Test the categorizer with example pages"""
    apify_token = os.environ.get("APIFY_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not apify_token or not openai_key:
        print("❌ Missing API tokens!")
        print("Set APIFY_TOKEN and OPENAI_API_KEY environment variables")
        return
    
    categorizer = InstagramCategorizer(apify_token, openai_key)
    
    # Test with a few example pages
    test_pages = [
        "blacksuccesslive",
        "inspirationation00",
        "healersmindset"
    ]
    
    results = categorizer.categorize_pages_batch(test_pages, show_cost_estimate=True)
    
    print("\n" + "="*80)
    print("CATEGORIZATION RESULTS")
    print("="*80)
    
    for username, result in results.items():
        print(f"\n@{username}")
        print(f"  Category: {result['category']} ({result['category_confidence']*100:.0f}%)")
        print(f"  Email: {result['contact_email'] or 'Not found'}")
        print(f"  Promo Status: {result['promo_status']}")
        if result['promo_indicators']:
            print(f"  Indicators: {', '.join(result['promo_indicators'])}")


if __name__ == "__main__":
    test_categorizer()



