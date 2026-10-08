import os
import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ddgs import DDGS
import smtplib
import ssl
from email.message import EmailMessage

# UPGRADE 1: Enterprise-Grade Network Robustness
session = requests.Session()
retries = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

def extract_emails_advanced(html_content, text_content):
    # Regex updated: Enforces that the Top Level Domain (TLD) ends with at least 2 letters (e.g., .com, .uk) 
    # This prevents catching javascript packages like "katex@0.16.21" or image files like "user@2x.png"
    emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', text_content))
    soup = BeautifulSoup(html_content, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].lower().startswith('mailto:'):
            clean_email = a['href'][7:].split('?')[0].strip()
            if clean_email:
                emails.add(clean_email)
    return emails

def detect_tech_stack(html):
    # CLAY.COM FEATURE: Deep Tech Stack & Pixel Detection
    platform = "Custom Code"
    if 'wp-content' in html or 'wp-includes' in html: platform = "WordPress"
    elif 'cdn.shopify.com' in html: platform = "Shopify"
    elif 'data-wf-site' in html or 'w-webflow' in html: platform = "Webflow"
    elif 'wix.com' in html or 'wixpress' in html: platform = "Wix"
    elif 'squarespace.com' in html: platform = "Squarespace"
    elif 'id="root"' in html or 'id="__next"' in html: platform = "React/Modern JS"
    
    pixels = []
    if 'fbevents.js' in html: pixels.append("Facebook Pixel")
    if 'googletagmanager' in html or 'google-analytics' in html: pixels.append("Google Analytics")
    if 'snap.licdn.com' in html: pixels.append("LinkedIn Insight Tag")
    if 'hotjar' in html: pixels.append("Hotjar")
    
    return platform, pixels

def analyze_website_and_get_email(url):
    try:
        headers = {'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ])}
        
        start_time = time.time()
        response = session.get(url, headers=headers, timeout=12)
        load_time = time.time() - start_time
        
        if response.status_code != 200: return None, None, None, None, None
            
        html = response.text.lower()
        platform, pixels = detect_tech_stack(html)
        is_spa = platform == "React/Modern JS"
        
        rebuild_issues = []
        if load_time > 3.0: rebuild_issues.append("Slow Load Time")
        if url.startswith("http://"): rebuild_issues.append("Not Secure (No SSL)")
        
        if not is_spa:
            if 'name="viewport"' not in html and "name='viewport'" not in html: rebuild_issues.append("Not Mobile Friendly")
            if html.count('<table') > 3: rebuild_issues.append("Outdated Design")
        
        seo_issues = []
        if not is_spa and '<h1' not in html: seo_issues.append("Missing H1 SEO Tags")
        if "Google Analytics" not in pixels: seo_issues.append("No Traffic Analytics")
        if "Facebook Pixel" not in pixels: seo_issues.append("No Retargeting Pixel")
        
        # SMART CATEGORIZATION ENGINE
        if rebuild_issues:
            lead_category = "REBUILD"
            issues_str = " | ".join(rebuild_issues)
        elif seo_issues:
            lead_category = "SEO_MARKETING"
            issues_str = " | ".join(seo_issues)
        else:
            lead_category = "AUTOMATION"
            issues_str = f"Perfect {platform} Website"
            
        emails = extract_emails_advanced(response.text, response.text)
        
        if not emails:
            base_url = url.rstrip('/')
            for path in ['/contact', '/contact-us', '/about', '/about-us']:
                try:
                    contact_response = session.get(base_url + path, headers=headers, timeout=6)
                    if contact_response.status_code == 200:
                        emails.update(extract_emails_advanced(contact_response.text, contact_response.text))
                except:
                    pass
        
        # Highly accurate Phone Number Extraction
        valid_phone = None
        soup = BeautifulSoup(html, 'html.parser')
        
        # Method 1: Look for explicit 'tel:' links (100% accurate)
        for a in soup.find_all('a', href=True):
            if a['href'].lower().startswith('tel:'):
                clean_phone = a['href'][4:].split('?')[0].strip()
                if len(re.sub(r'[^\d]', '', clean_phone)) >= 10:
                    valid_phone = clean_phone
                    break
                    
        # Method 2: Scan visible text only (prevents catching JS timestamps/coordinates)
        if not valid_phone:
            visible_text = soup.get_text(separator=' ')
            # Comprehensive regex: Matches standard US, standard India (including 5-5 splits like 98765 43210)
            phone_pattern = re.compile(r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b(?:\+91|0)?[-.\s]?[6789]\d{4}[-.\s]?\d{5}\b|\b(?:\+91|0)?[-.\s]?[6789]\d{9}\b')
            phones = phone_pattern.findall(visible_text)
            for p in phones:
                if not p.strip(): continue
                clean_p = re.sub(r'[^\d]', '', p)
                # Valid length and doesn't look like a Unix timestamp (17xxxx)
                if 10 <= len(clean_p) <= 12 and not clean_p.startswith('17'):
                    valid_phone = p.strip()
                    break
        
        bad_emails = ['your@', 'email@', 'example.com', 'domain.com', 'name@', 'test@', 'info@yoursite', 'no-reply', 'noreply', 'sentry.io', 'wixpress', 'admin@example']
        valid_emails = [e for e in emails if not any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']) and not any(bad in e.lower() for bad in bad_emails)]
        
        tech_data = {"platform": platform, "pixels": pixels}
        
        if valid_emails:
            return valid_emails[0], valid_phone, lead_category, issues_str, tech_data
        elif valid_phone:
            return None, valid_phone, lead_category, issues_str, tech_data
            
    except Exception:
        pass
    return None, None, None, None, None

def get_indepth_issue_text(issues_str):
    issue_details = {
        "Not Mobile Friendly": "Missing responsive viewport tags. Your site breaks on modern phones, forcing customers to pinch and zoom (massive bounce rate).",
        "Slow Load Time": "Core server response is lagging. Google penalizes slow load times, actively pushing you down the search rankings.",
        "Not Secure (No SSL)": "Your site loads over HTTP. Modern browsers show a red 'Not Secure' warning, breaking customer trust.",
        "Outdated Design": "Built using an outdated HTML structure. It makes the business look like it hasn't been updated in years.",
        "Missing H1 SEO Tags": "Your homepage is missing the primary H1 tag. Google's algorithm literally doesn't know what keywords to rank you for.",
        "No Traffic Analytics": "No Google Analytics tracking detected. You have zero visibility on where your traffic is coming from.",
        "No Retargeting Pixel": "No Meta/Facebook Pixel detected. You are unable to run retargeting ads to people who visit your site and leave."
    }
    
    bullets = []
    for raw_issue in issues_str.split(' | '):
        if raw_issue in issue_details:
            bullets.append(f"❌ {raw_issue}:\n   {issue_details[raw_issue]}")
            
    if bullets:
        return "\n".join(bullets)
    return "- " + issues_str

def generate_dynamic_email(company, website, lead_category, issues, tech_data):
    platform = tech_data['platform']
    
    greetings = [f"Hi {company},", f"Hey {company},", f"Hello team at {company},"]
    intros = [
        f"I was doing some research on local businesses and came across your website ({website}).",
        f"I recently found your website ({website}) while looking for local businesses in the area."
    ]
    signoffs = ["Best,", "Cheers,", "Regards,", "Thanks,"]

    # CLAY-LIKE HYPER-PERSONALIZATION based on Tech Stack
    platform_comment = ""
    if platform != "Custom Code":
        platform_comment = f"I noticed your site is currently running on {platform}. "

    if lead_category == "REBUILD":
        mid = [
            f"{platform_comment}I ran a quick technical audit and noticed a few deep issues that are actively turning away mobile customers:",
            f"{platform_comment}While browsing, I noticed a couple of technical red flags in your source code that usually push mobile visitors away:"
        ]
        pitch = [
            f"I'm a freelance developer, and I specialize in rebuilding local business sites to fix these exact issues. Because you're already familiar with {platform}, upgrading to a lightning-fast modern version of it is very straightforward.",
            "I help local businesses fix these problems by rebuilding their websites to be lightning-fast and fully mobile responsive."
        ]
        cta = ["Would you be open to a quick 5-minute chat to see if a redesign makes sense for you?"]

    elif lead_category == "SEO_MARKETING":
        mid = [
            f"Your website looks visually great, but I ran an audit and noticed you are missing some critical tracking infrastructure:",
            f"{platform_comment}I love the design of your site, but I noticed it's missing fundamental on-page tracking in the backend:"
        ]
        pitch = [
            "I specialize in Technical SEO and Analytics for local businesses. I can optimize your site's code so you actually rank higher and start tracking where your customers are coming from.",
            "I help businesses fix these tracking gaps so they can finally see their data and stop losing traffic to competitors."
        ]
        cta = ["Are you open to a brief 5-minute chat this week to see if we can boost your tracking and ranking?"]

    else:
        mid = [
            f"Honestly, your {platform} website looks fantastic. It's fast, mobile-friendly, and perfectly optimized. You clearly invest in your online presence.",
            f"I run technical audits on local sites, and yours is one of the few {platform} sites that passed with flying colors. Great job on the web presence!"
        ]
        pitch = [
            "Since your front-facing marketing is locked in, I'm curious if your back-office is fully optimized? I build custom internal software, CRM integrations, and AI automations to help businesses eliminate manual data entry and save hours of admin work every week.",
            "Because your website is already perfect, I wanted to reach out regarding back-office automation. I build custom scripts and AI tools that automate tedious manual tasks, invoicing, and lead follow-ups for local businesses."
        ]
        cta = ["If you have any manual processes you'd love to automate, would you be open to a quick 5-minute chat?"]

    body = f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{random.choice(mid)}\n\n"
    
    if lead_category in ["REBUILD", "SEO_MARKETING"]:
        body += f"{get_indepth_issue_text(issues)}\n\n"
        
    body += f"{random.choice(pitch)}\n\n{random.choice(cta)}\n\n{random.choice(signoffs)}\nKetan\nWeb Developer / Tech Consultant"
    return body

def send_email(target_email, company, website, lead_category, issues, tech_data):
    sender_email = os.environ.get('GMAIL_USER')
    app_password = os.environ.get('GMAIL_PASS')
    
    if not sender_email or not app_password:
        return False
        
    subject = f"Quick question about {website}"
    body = generate_dynamic_email(company, website, lead_category, issues, tech_data)
        
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = target_email
    msg.set_content(body)
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

def get_domain(url):
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return url

def main():
    with open('niches.txt') as f: niches = f.read().splitlines()
    with open('cities.txt') as f: cities = f.read().splitlines()
    
    contacted_file = 'contacted.txt'
    if not os.path.exists(contacted_file): open(contacted_file, 'w', encoding='utf-8').close()
    if not os.path.exists('phone_leads.txt'): open('phone_leads.txt', 'w', encoding='utf-8').close()
    if not os.path.exists('no_website_leads.txt'): open('no_website_leads.txt', 'w', encoding='utf-8').close()
        
    with open(contacted_file, 'r', encoding='utf-8') as f:
        contacted = set(f.read().splitlines())
        
    custom_niche = os.environ.get('CUSTOM_NICHE')
    custom_city = os.environ.get('CUSTOM_CITY')
    
    niche = custom_niche if custom_niche else random.choice(niches)
    city = custom_city if custom_city else random.choice(cities)
    
    print(f"=== CLAY.COM STYLE OUTREACH BOT v8.0 (HUNTER MODE) ===")
    print(f"Targeting: {niche} in {city} | Goal: 25+ Phone Leads")
    
    ignore_sites = ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com', 'youtube.com', 'zillow', 'tripadvisor']
    
    emails_sent_today = 0
    phone_leads_harvested = 0
    skipped_dirs = 0
    
    # Endless modifiers to keep the bot searching until it hits the target
    modifiers = ["", "services", "near me", "contact number", "list", "top rated", "directory", "best", "affordable", "local", "experts", "contractors", "agencies"]
    random.shuffle(modifiers)
    
    try:
        with DDGS() as ddgs:
            print("\n[Deep Signal Scanning] Hunting for Websites & Phone Numbers...")
            
            for modifier in modifiers:
                if phone_leads_harvested >= 25:
                    print("\n🎯 GOAL REACHED! 25+ Phone numbers harvested. Stopping script.")
                    break
                    
                q = f"{niche} {city} {modifier}".strip()
                print(f"\n--- Running Search Query: {q} ---")
                
                try:
                    # Fetching 50 results per query to avoid heavy rate limits
                    results = list(ddgs.text(q, max_results=50))
                except Exception as e:
                    print(f"  -> Search Rate Limit Hit. Sleeping for 15 seconds...")
                    time.sleep(15)
                    continue
                    
                print(f"  -> Found {len(results)} links. Scanning...")
            
                # Massive list of directory/blog keywords to avoid pitching them
                directory_keywords = ['category', 'directory', 'top-', 'best-', 'list', 'yelp', 'yellowpages', 'justdial', 'sulekha', 'indiamart', 'practo', 'lybrate', 'zocdoc', 'lentlo', 'threebestrated', 'urbancompany', 'wiki', 'pedia', 'blog', 'article', 'news', '/resources/', '/guides/', '/insights/', '/post/', '/author/']
                
                for result in results:
                    # Stop if we hit 25 phones
                    if phone_leads_harvested >= 25: 
                        break
                        
                    website_url = result['href']
                    name = result['title']
                    domain = get_domain(website_url)
                    
                    # Check if it's obviously a social media site to skip entirely
                    if any(site in website_url.lower() for site in ignore_sites): 
                        skipped_dirs += 1
                        continue
                        
                    if website_url in contacted or domain in contacted: 
                        continue
                        
                    # SMART DIRECTORY & BLOG DETECTION
                    is_directory = False
                    url_path = website_url.split(domain)[-1] if domain in website_url else ""
                    
                    if any(k in website_url.lower() for k in directory_keywords):
                        is_directory = True
                    elif any(k in name.lower() for k in ['top', 'best', 'list of', 'directory', 'most']):
                        is_directory = True
                    elif url_path.count('-') >= 3: 
                        # If the URL path has 3+ hyphens (e.g. /top-luxury-spa-dubai), it's almost certainly a blog post, not a business homepage
                        is_directory = True
                        
                    print(f"\nAuditing: {website_url} {'[DIRECTORY DETECTED]' if is_directory else ''}")
                    email, phone, lead_category, issues, tech_data = analyze_website_and_get_email(website_url)
                    
                    if tech_data and not is_directory:
                        print(f"  -> Stack Detected: {tech_data['platform']} | Pixels: {tech_data['pixels']}")
                    
                    # If it's a directory, DO NOT SEND EMAIL. Just harvest data.
                    if is_directory:
                        if phone:
                            print(f"  -> Harvested Phone from Directory: {phone}")
                            with open('phone_leads.txt', 'a', encoding='utf-8') as f:
                                f.write(f"Name: {name} | Category: DIRECTORY_LEAD | Source: {domain} | Phone: {phone} | URL: {website_url}\n")
                            contacted.update([website_url, domain])
                            phone_leads_harvested += 1
                        continue
                    
                    if email and email not in contacted:
                        print(f"  -> Found {lead_category} Lead! Email: {email}")
                        success = send_email(email, name, website_url, lead_category, issues, tech_data)
                        
                        if success:
                            print(f"  -> CLAY-STYLE PITCH SENT AUTOMATICALLY!")
                            with open(contacted_file, 'a', encoding='utf-8') as f:
                                f.write(website_url + '\n')
                                f.write(domain + '\n')
                                f.write(email + '\n')
                            contacted.update([website_url, domain, email])
                            emails_sent_today += 1
                            time.sleep(12)
                    elif lead_category and phone:
                        print(f"  -> Lead, NO email, but FOUND PHONE: {phone}")
                        with open('phone_leads.txt', 'a', encoding='utf-8') as f:
                            f.write(f"Category: {lead_category} | Tech: {tech_data['platform']} | Phone: {phone} | URL: {website_url}\n")
                        phone_leads_harvested += 1
                    elif lead_category:
                        print(f"  -> {lead_category} site, but NO contact info found.")
                        
            print(f"\nSkipped {skipped_dirs} directory websites.")
    except Exception as e:
        print(f"Error during search: {e}")
        
    print(f"\nJob Complete. Sent {emails_sent_today} automated emails today.")

if __name__ == "__main__":
    main()
