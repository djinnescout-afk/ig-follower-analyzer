"""
Streamlit App for Human-Assisted Instagram Page Categorization
"""

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from categorizer import CATEGORIES

# Hotlist keywords for priority categorization
# Note: Uses partial matching - "black" matches "blacksuccess", "hustl" matches "hustlersimage"
HOTLIST_KEYWORDS = [
    "hustl",      # Matches: hustlersimage, hustlingquiet, etc.
    "afri",       # Matches: african, afro-american, etc.
    "afro",       # Matches: afro-american, etc.
    "black",      # Matches: blacksuccess, blackbillionaire, etc.
    "melanin",    # Matches: melaninmagic, melaninpoppin, etc.
    "blvck",      # Alternative spelling of black
    "culture",    # Matches: culture, cultural, etc.
    "kulture",    # Alternative spelling of culture
    "brown",      # Matches: brownskin, brownbeauty, brownsuccess, etc.
    "noir",       # French for black, used in some contexts
    "ebony"       # Another term for black/dark
]

CONTACT_METHODS = ["IG DM", "Email", "Phone", "WhatsApp", "Telegram", "Other"]

# Page config
st.set_page_config(
    page_title="Instagram Page Categorizer",
    page_icon="📱",
    layout="wide"
)

# Initialize session state
if 'current_page_idx' not in st.session_state:
    st.session_state.current_page_idx = 0
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = {}
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False


def get_data_file_path() -> str:
    """Get the data file path, checking for Railway volume first"""
    # Check for Railway volume mount (persistent storage)
    volume_path = "/data/clients_data.json"
    if os.path.exists(volume_path):
        return volume_path
    # Fall back to local file
    return "clients_data.json"


def load_data(data_file: str = None) -> Optional[Dict]:
    """Load client data from JSON file, create empty structure if it doesn't exist"""
    if data_file is None:
        data_file = get_data_file_path()
    
    if not os.path.exists(data_file):
        # Create empty structure for new deployments
        empty_data = {
            "clients": {},
            "pages": {}
        }
        try:
            # Ensure directory exists (for volume path)
            os.makedirs(os.path.dirname(data_file) if os.path.dirname(data_file) else ".", exist_ok=True)
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, indent=2, ensure_ascii=False)
            st.info(f"📝 Created new {data_file}. You can start adding clients and pages.")
        except Exception as e:
            st.error(f"❌ Could not create {data_file}: {str(e)}")
            return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data: Dict, data_file: str = None):
    """Save client data to JSON file"""
    if data_file is None:
        data_file = get_data_file_path()
    data["last_updated"] = datetime.now().isoformat()
    # Ensure directory exists (for volume path)
    os.makedirs(os.path.dirname(data_file) if os.path.dirname(data_file) else ".", exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def matches_hotlist(page_data: Dict) -> bool:
    """Check if page matches hotlist keywords"""
    username = page_data.get("username", "").lower()
    full_name = page_data.get("full_name", "").lower()
    
    text = f"{username} {full_name}"
    return any(keyword.lower() in text for keyword in HOTLIST_KEYWORDS)


def get_pages_for_categorization(data: Dict, filter_type: str = "uncategorized", 
                                 min_clients: int = 1) -> List[Tuple[str, Dict]]:
    """Get pages sorted for categorization"""
    pages = data.get("pages", {})
    result = []
    
    for username, page_data in pages.items():
        client_count = len(page_data.get("clients_following", []))
        
        if client_count < min_clients:
            continue
        
        # Apply filter
        category = page_data.get("category")
        if filter_type == "uncategorized":
            if category and category != "UNKNOWN":
                continue
        elif filter_type == "all":
            pass  # Include all
        elif filter_type == "specific":
            # This would need a category selector - for now, show all
            pass
        
        result.append((username, page_data))
    
    # Sort: hotlist first, then by clients following, then by followers
    def sort_key(item):
        username, page_data = item
        is_hotlist = matches_hotlist(page_data)
        client_count = len(page_data.get("clients_following", []))
        follower_count = page_data.get("follower_count", 0)
        return (not is_hotlist, -client_count, -follower_count)
    
    result.sort(key=sort_key)
    return result


def get_pages_by_category(data: Dict, category: str, min_clients: int = 1) -> List[Dict]:
    """Get pages for a specific category, sorted properly"""
    pages = data.get("pages", {})
    result = []
    
    for username, page_data in pages.items():
        client_count = len(page_data.get("clients_following", []))
        
        if client_count < min_clients:
            continue
        
        page_category = page_data.get("category", "UNCATEGORIZED")
        if category == "UNCATEGORIZED":
            if page_category and page_category != "UNKNOWN":
                continue
        elif page_category != category:
            continue
        
        # Calculate metrics
        follower_count = page_data.get("follower_count", 0)
        promo_price = page_data.get("promo_price")
        
        page_info = {
            "username": username,
            "page_data": page_data,
            "client_count": client_count,
            "follower_count": follower_count,
            "promo_price": promo_price,
            "concentration": client_count / follower_count if follower_count > 0 else 0,
            "followers_per_client": follower_count / client_count if client_count > 0 else 0
        }
        
        # Calculate concentration_per_dollar if price available
        if promo_price and promo_price > 0:
            page_info["concentration_per_dollar"] = page_info["concentration"] / promo_price
        else:
            page_info["concentration_per_dollar"] = None
        
        result.append(page_info)
    
    # Sort: pages with price first (by concentration_per_dollar), then without price (by followers_per_client)
    def sort_key(page_info):
        has_price = page_info["concentration_per_dollar"] is not None
        if has_price:
            return (0, -page_info["concentration_per_dollar"])  # 0 = first group
        else:
            return (1, -page_info["followers_per_client"])  # 1 = second group
    
    result.sort(key=sort_key)
    return result


def main():
    st.title("📱 Instagram Page Categorizer")
    st.markdown("**Human-Assisted Categorization Tool for Instagram Pages**")
    st.markdown("---")
    
    # Load data
    data = load_data()
    if data is None:
        st.stop()
    
    st.session_state.data_loaded = True
    
    # Show quick stats
    pages = data.get("pages", {})
    total_pages = len(pages)
    uncategorized = sum(1 for p in pages.values() if not p.get("category") or p.get("category") == "UNKNOWN")
    categorized = total_pages - uncategorized
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pages", f"{total_pages:,}")
    with col2:
        st.metric("Categorized", f"{categorized:,}")
    with col3:
        st.metric("Uncategorized", f"{uncategorized:,}")
    
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Categorize Pages", "✏️ Edit Page Details", "📂 View by Category", "📤 Data Management"])
    
    # TAB 1: Categorize Pages
    with tab1:
        st.header("Categorize Pages")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox(
                "Filter Pages",
                ["uncategorized", "all", "specific"],
                format_func=lambda x: {
                    "uncategorized": "Uncategorized Only",
                    "all": "All Pages",
                    "specific": "Specific Category"
                }[x],
                index=0
            )
        
        with col2:
            min_clients = st.number_input("Minimum Clients Following", min_value=1, value=2)
        
        # Get pages
        pages_list = get_pages_for_categorization(data, filter_type, min_clients)
        
        if not pages_list:
            st.info("✅ No pages found matching the filter criteria!")
            st.stop()
        
        total_pages = len(pages_list)
        
        # Navigation
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        
        with col1:
            if st.button("◀ Previous", disabled=st.session_state.current_page_idx == 0):
                st.session_state.current_page_idx = max(0, st.session_state.current_page_idx - 1)
                st.rerun()
        
        with col2:
            jump_to = st.number_input("Jump to", min_value=1, max_value=total_pages, 
                                     value=st.session_state.current_page_idx + 1, key="jump_input")
            if jump_to != st.session_state.current_page_idx + 1:
                st.session_state.current_page_idx = jump_to - 1
                st.rerun()
        
        with col3:
            st.markdown(f"**Page {st.session_state.current_page_idx + 1} of {total_pages}**")
        
        with col4:
            if st.button("Next ▶", disabled=st.session_state.current_page_idx >= total_pages - 1):
                # Save current selection before moving
                if st.session_state.current_page_idx < len(pages_list):
                    username, _ = pages_list[st.session_state.current_page_idx]
                    selected_cat = st.session_state.selected_category.get(username)
                    if selected_cat:
                        data["pages"][username]["category"] = selected_cat
                        data["pages"][username]["last_categorized"] = datetime.now().isoformat()
                        save_data(data)
                        st.success("💾 Saved!")
                
                st.session_state.current_page_idx = min(total_pages - 1, st.session_state.current_page_idx + 1)
                st.rerun()
        
        st.markdown("---")
        
        # Display current page
        if st.session_state.current_page_idx < len(pages_list):
            username, page_data = pages_list[st.session_state.current_page_idx]
            
            # Check if hotlist
            is_hotlist = matches_hotlist(page_data)
            if is_hotlist:
                st.markdown("### 🔥 **PRIORITY PAGE** (Matches hotlist keywords)")
            
            # Profile info
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Profile picture - try base64 first, fallback to URL
                profile_data = page_data.get("profile_data")
                if profile_data and isinstance(profile_data, dict):
                    pic_displayed = False
                    
                    # Try base64 first (doesn't expire)
                    if profile_data.get("profile_pic_base64") and profile_data.get("profile_pic_mime_type"):
                        try:
                            data_uri = f"data:{profile_data['profile_pic_mime_type']};base64,{profile_data['profile_pic_base64']}"
                            st.image(data_uri, width=200)
                            pic_displayed = True
                        except:
                            pass
                    
                    # Fallback to URL
                    if not pic_displayed and profile_data.get("profile_pic_url"):
                        try:
                            st.image(profile_data["profile_pic_url"], width=200)
                            pic_displayed = True
                        except:
                            pass
                    
                    if not pic_displayed:
                        st.info("📷 Profile picture not available")
                else:
                    st.info("📷 Profile picture not scraped yet. Run scrape_profiles.py")
                
                # Basic stats
                st.metric("Followers", f"{page_data.get('follower_count', 0):,}")
                st.metric("Clients Following", len(page_data.get("clients_following", [])))
            
            with col2:
                st.markdown(f"### @{username}")
                st.markdown(f"**{page_data.get('full_name', 'N/A')}**")
                
                # Bio
                if profile_data and isinstance(profile_data, dict) and profile_data.get("bio"):
                    st.markdown("**Bio:**")
                    st.markdown(profile_data["bio"])
                else:
                    st.info("Bio not available. Run scrape_profiles.py")
            
            # Recent posts
            st.markdown("---")
            st.markdown("### Recent Posts")
            
            show_captions = st.checkbox("Show Captions", value=False)
            
            if profile_data and isinstance(profile_data, dict) and profile_data.get("posts"):
                posts = profile_data["posts"][:12]  # Show up to 12 posts
                
                # Display in grid
                cols = st.columns(3)
                for idx, post in enumerate(posts):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        # Try base64 first (doesn't expire), fallback to URL
                        image_displayed = False
                        if post.get("image_base64") and post.get("image_mime_type"):
                            try:
                                # Display base64 image
                                data_uri = f"data:{post['image_mime_type']};base64,{post['image_base64']}"
                                st.image(data_uri, use_container_width=True)
                                image_displayed = True
                            except Exception as e:
                                # Fallback to URL if base64 fails
                                pass
                        
                        # Fallback to URL if base64 not available
                        if not image_displayed and post.get("image_url"):
                            try:
                                st.image(post["image_url"], use_container_width=True)
                                image_displayed = True
                            except Exception as e:
                                st.error("Image unavailable (URL expired)")
                        
                        if not image_displayed:
                            st.info("📷 Image not available")
                        
                        if show_captions and post.get("caption"):
                            caption = post["caption"][:100] + "..." if len(post.get("caption", "")) > 100 else post.get("caption", "")
                            st.caption(caption)
            else:
                st.info("📸 Posts not scraped yet. Run scrape_profiles.py")
            
            # Category selection
            st.markdown("---")
            st.markdown("### Select Category")
            
            current_category = page_data.get("category", "UNKNOWN")
            category_options = ["UNKNOWN"] + list(CATEGORIES.keys())
            
            selected = st.selectbox(
                "Category",
                category_options,
                index=category_options.index(current_category) if current_category in category_options else 0,
                key=f"category_{username}"
            )
            
            # Store selection
            st.session_state.selected_category[username] = selected
            
            # Show category description
            if selected != "UNKNOWN" and selected in CATEGORIES:
                st.info(f"**{selected.replace('_', ' ')}**: {CATEGORIES[selected]}")
    
    # TAB 2: Edit Page Details
    with tab2:
        st.header("Edit Page Details")
        
        # Search/select page
        pages = data.get("pages", {})
        page_usernames = sorted(pages.keys())
        
        selected_username = st.selectbox("Select Page", page_usernames, key="edit_page_select")
        
        if selected_username:
            page_data = pages[selected_username]
            
            st.markdown(f"### @{selected_username}")
            st.markdown(f"**{page_data.get('full_name', 'N/A')}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Contact Information")
                
                # Known contact methods
                known_methods = page_data.get("known_contact_methods", [])
                selected_known = st.multiselect(
                    "Known Contact Methods",
                    CONTACT_METHODS,
                    default=known_methods,
                    key="known_methods"
                )
                
                # Successful contact method
                successful_method = page_data.get("successful_contact_method")
                selected_successful = st.selectbox(
                    "Successful Contact Method",
                    [None] + CONTACT_METHODS,
                    index=0 if successful_method is None else CONTACT_METHODS.index(successful_method) + 1,
                    key="successful_method"
                )
                
                # Current main contact method
                current_main = page_data.get("current_main_contact_method")
                selected_main = st.selectbox(
                    "Current Main Contact Method",
                    [None] + CONTACT_METHODS,
                    index=0 if current_main is None else CONTACT_METHODS.index(current_main) + 1,
                    key="main_method"
                )
                
                # IG Account for DM (only show if IG DM is in known methods or is the main method)
                ig_account_dm = page_data.get("ig_account_for_dm", "")
                if "IG DM" in selected_known or selected_main == "IG DM":
                    ig_account_input = st.text_input(
                        "IG Account Used for DM",
                        value=ig_account_dm,
                        placeholder="e.g., @your_account",
                        key="ig_account_dm",
                        help="Which Instagram account username you use to DM this page"
                    )
                else:
                    ig_account_input = ""
            
            with col2:
                st.markdown("#### Pricing & Promo Status")
                
                # Promo price
                promo_price = page_data.get("promo_price")
                new_price = st.number_input(
                    "Promo Price ($)",
                    min_value=0.0,
                    value=float(promo_price) if promo_price else 0.0,
                    step=10.0,
                    key="promo_price"
                )
                
                # Promo status (manual override)
                current_promo_status = page_data.get("promo_status", "Unknown")
                promo_status_options = ["Unknown", "Warm", "Not Open"]
                selected_promo_status = st.selectbox(
                    "Promo Status",
                    promo_status_options,
                    index=promo_status_options.index(current_promo_status) if current_promo_status in promo_status_options else 0,
                    key="promo_status",
                    help="Manually set or override the promo status detected from bio/highlights"
                )
                
                # Display current promo indicators
                promo_indicators = page_data.get("promo_indicators", [])
                if promo_indicators:
                    st.markdown("**Auto-detected Indicators:**")
                    for indicator in promo_indicators:
                        st.text(f"  • {indicator}")
                
                # Website URL
                website_url = page_data.get("website_url", "")
                website_input = st.text_input(
                    "Website URL",
                    value=website_url,
                    placeholder="https://example.com",
                    key="website_url",
                    help="Website URL from bio or link in bio (auto-detected during scraping)"
                )
                
                # Website Promo Info (auto-detected)
                website_promo_info = page_data.get("website_promo_info")
                if website_promo_info:
                    st.markdown("**🌐 Website Promo Detection:**")
                    if website_promo_info.get("has_promo_mention"):
                        st.success("✅ Website mentions promo/advertising")
                    if website_promo_info.get("has_promo_page"):
                        st.success("✅ Website has promo/buy page")
                        promo_urls = website_promo_info.get("promo_page_urls", [])
                        if promo_urls:
                            for url in promo_urls[:3]:  # Show first 3
                                st.text(f"  • {url}")
                    if website_promo_info.get("has_contact_email"):
                        st.success("✅ Website has contact email for promo")
                        emails = website_promo_info.get("contact_emails", [])
                        if emails:
                            for email in emails:
                                st.text(f"  • {email}")
                    if website_promo_info.get("has_contact_form"):
                        st.success("✅ Website has contact form")
                        forms = website_promo_info.get("contact_forms", [])
                        if forms:
                            for form in forms[:3]:  # Show first 3
                                form_details = []
                                if form.get("has_email_field"):
                                    form_details.append("email field")
                                if form.get("has_message_field"):
                                    form_details.append("message field")
                                details_str = f" ({', '.join(form_details)})" if form_details else ""
                                st.text(f"  • {form.get('url', 'N/A')}{details_str}")
                
                # Display current values
                st.markdown("#### Current Values")
                st.text(f"Category: {page_data.get('category', 'N/A')}")
                st.text(f"Followers: {page_data.get('follower_count', 0):,}")
                st.text(f"Clients Following: {len(page_data.get('clients_following', []))}")
            
            # Save button
            if st.button("💾 Save Changes", type="primary"):
                page_data["known_contact_methods"] = selected_known
                page_data["successful_contact_method"] = selected_successful
                page_data["current_main_contact_method"] = selected_main
                page_data["ig_account_for_dm"] = ig_account_input if ig_account_input else None
                page_data["promo_price"] = new_price if new_price > 0 else None
                page_data["promo_status"] = selected_promo_status
                page_data["website_url"] = website_input if website_input else None
                
                save_data(data)
                st.success("✅ Changes saved!")
                st.rerun()
    
    # TAB 3: View by Category
    with tab3:
        st.header("View Pages by Category")
        
        # Category tabs
        category_list = ["UNCATEGORIZED"] + list(CATEGORIES.keys())
        category_tabs = st.tabs([cat.replace("_", " ").title() for cat in category_list])
        
        for idx, category in enumerate(category_list):
            with category_tabs[idx]:
                pages_in_category = get_pages_by_category(data, category, min_clients=1)
                
                if not pages_in_category:
                    st.info(f"No pages found in category: {category}")
                    continue
                
                st.metric("Total Pages", len(pages_in_category))
                
                # Search/filter
                search_term = st.text_input("🔍 Search pages", key=f"search_{category}")
                
                # Display pages
                for page_info in pages_in_category:
                    username = page_info["username"]
                    page_data = page_info["page_data"]
                    
                    # Filter by search
                    if search_term:
                        if search_term.lower() not in username.lower() and \
                           search_term.lower() not in page_data.get("full_name", "").lower():
                            continue
                    
                    with st.expander(f"@{username} - {page_data.get('full_name', 'N/A')}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Profile picture - try base64 first, fallback to URL
                            profile_data = page_data.get("profile_data")
                            if profile_data and isinstance(profile_data, dict):
                                pic_displayed = False
                                
                                # Try base64 first
                                if profile_data.get("profile_pic_base64") and profile_data.get("profile_pic_mime_type"):
                                    try:
                                        data_uri = f"data:{profile_data['profile_pic_mime_type']};base64,{profile_data['profile_pic_base64']}"
                                        st.image(data_uri, width=150)
                                        pic_displayed = True
                                    except:
                                        pass
                                
                                # Fallback to URL
                                if not pic_displayed and profile_data.get("profile_pic_url"):
                                    try:
                                        st.image(profile_data["profile_pic_url"], width=150)
                                        pic_displayed = True
                                    except:
                                        pass
                                
                                if not pic_displayed:
                                    st.text("Image unavailable")
                            
                            # Instagram link
                            st.markdown(f"[🔗 View on Instagram](https://instagram.com/{username})")
                        
                        with col2:
                            st.markdown("**Stats:**")
                            st.text(f"Followers: {page_info['follower_count']:,}")
                            st.text(f"Clients Following: {page_info['client_count']}")
                            st.text(f"Concentration: {page_info['concentration']:.2e}")
                            
                            if page_info["promo_price"]:
                                st.text(f"Price: ${page_info['promo_price']:,.2f}")
                                if page_info["concentration_per_dollar"]:
                                    st.text(f"Value: {page_info['concentration_per_dollar']:.2e} conc/$")
                        
                        with col3:
                            st.markdown("**Contact Info:**")
                            known = page_data.get("known_contact_methods", [])
                            if known:
                                st.text(f"Known: {', '.join(known)}")
                            
                            successful = page_data.get("successful_contact_method")
                            if successful:
                                st.text(f"✅ Successful: {successful}")
                            
                            main = page_data.get("current_main_contact_method")
                            if main:
                                st.text(f"📞 Current: {main}")
                            
                            ig_account = page_data.get("ig_account_for_dm")
                            if ig_account:
                                st.text(f"📱 IG Account: {ig_account}")
                            
                            website = page_data.get("website_url")
                            if website:
                                st.markdown(f"🌐 [Website]({website})")
                            
                            # Show website promo info if available
                            website_promo = page_data.get("website_promo_info")
                            if website_promo:
                                promo_flags = []
                                if website_promo.get("has_promo_mention"):
                                    promo_flags.append("Mentions promo")
                                if website_promo.get("has_promo_page"):
                                    promo_flags.append("Has promo page")
                                if website_promo.get("has_contact_email"):
                                    promo_flags.append("Contact email")
                                if website_promo.get("has_contact_form"):
                                    promo_flags.append("Contact form")
                                if promo_flags:
                                    st.text(f"🌐 Website: {', '.join(promo_flags)}")
                            
                            if not known and not successful and not main and not website:
                                st.text("No contact info")
                        
                        # Quick edit button
                        if st.button(f"✏️ Quick Edit", key=f"edit_{username}_{category}"):
                            st.session_state.edit_page = username
                            st.rerun()


    # TAB 4: Data Management
    with tab4:
        st.markdown("### 📤 Upload & Sync Data")
        st.markdown("Upload your local `clients_data.json` to sync with Railway. VA's work will be preserved.")
        
        uploaded_file = st.file_uploader(
            "Choose clients_data.json file",
            type=['json'],
            help="Upload your local clients_data.json file. It will be merged with existing data, preserving VA's categorization work."
        )
        
        if uploaded_file is not None:
            try:
                # Read uploaded file
                new_data = json.load(uploaded_file)
                
                # Load current data
                current_data = load_data()
                
                if current_data:
                    st.info("🔄 Merging uploaded data with existing data (preserving VA's work)...")
                    
                    # Merge data (preserve VA's work)
                    merged_data = merge_data_smart(current_data, new_data)
                    
                    # Save merged data
                    save_data(merged_data)
                    
                    st.success("✅ Data uploaded and merged successfully! VA's work has been preserved.")
                    st.info("🔄 Refresh the page to see updated data.")
                else:
                    # No existing data, just save the uploaded file
                    save_data(new_data)
                    st.success("✅ Data uploaded successfully!")
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please upload a valid clients_data.json file.")
            except Exception as e:
                st.error(f"❌ Error uploading file: {str(e)}")
        
        st.markdown("---")
        st.markdown("### 📊 Current Data Status")
        data_file = get_data_file_path()
        if os.path.exists(data_file):
            file_size = os.path.getsize(data_file) / (1024 * 1024)  # MB
            st.info(f"📁 Data file: `{data_file}` ({file_size:.2f} MB)")
            
            data = load_data()
            if data:
                st.metric("Total Pages", len(data.get("pages", {})))
                st.metric("Total Clients", len(data.get("clients", {})))
        else:
            st.warning(f"⚠️ Data file not found at `{data_file}`")


def merge_data_smart(existing: Dict, new: Dict) -> Dict:
    """
    Smart merge: Preserves VA's work (categories, contact info) while updating scraped data
    """
    merged = {
        "clients": new.get("clients", {}),
        "pages": {}
    }
    
    existing_pages = existing.get("pages", {})
    new_pages = new.get("pages", {})
    
    for username, new_page_data in new_pages.items():
        existing_page_data = existing_pages.get(username, {})
        
        # Start with new scraped data
        merged_page = new_page_data.copy()
        
        # Preserve VA's categorization work
        if "category" in existing_page_data:
            merged_page["category"] = existing_page_data["category"]
        if "category_confidence" in existing_page_data:
            merged_page["category_confidence"] = existing_page_data["category_confidence"]
        
        # Preserve contact information (VA's edits)
        for field in [
            "known_contact_methods",
            "successful_contact_method",
            "current_main_contact_method",
            "ig_account_for_dm",
            "promo_price",
            "promo_status",  # Manual override
            "website_url"
        ]:
            if field in existing_page_data and existing_page_data[field]:
                merged_page[field] = existing_page_data[field]
        
        # Preserve website_promo_info if it exists
        if "website_promo_info" in existing_page_data:
            if "website_promo_info" not in new_page_data or not new_page_data.get("website_promo_info"):
                merged_page["website_promo_info"] = existing_page_data["website_promo_info"]
        
        merged["pages"][username] = merged_page
    
    # Add any pages that exist in old data but not in new
    for username, existing_page_data in existing_pages.items():
        if username not in merged["pages"]:
            merged["pages"][username] = existing_page_data
    
    return merged


if __name__ == "__main__":
    main()

