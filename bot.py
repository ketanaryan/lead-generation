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
    emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text_content))
    soup = BeautifulSoup(html_content, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].lower().startswith('mailto:'):
            clean_email = a['href'][7:].split('?')[0].strip()
            if clean_email:
                emails.add(clean_email)
    return emails

def analyze_website_and_get_email(url):
    try:
        headers = {'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ])}
        
        start_time = time.time()
        response = session.get(url, headers=headers, timeout=12)
        load_time = time.time() - start_time
        
        if response.status_code != 200: return None, None, None, None
            
        html = response.text.lower()
        
        # UPGRADE 5: Javascript-Heavy SPA Detection
        # Prevents false positives where React/Next.js sites look "empty" or lack traditional tags.
        is_spa = any(marker in html for marker in [
            'id="root"', 'id="__next"', 'id="app"', 'data-reactroot', 
            'ng-version', 'nuxt', '<script src="/_next/', 'gatsby'
        ])
        
        rebuild_issues = []
        if load_time > 3.0: rebuild_issues.append("Slow Load Time")
        if url.startswith("http://"): rebuild_issues.append("Not Secure (No SSL)")
        
        # Only check traditional HTML structure if it's NOT a modern Javascript framework
        if not is_spa:
            if 'name="viewport"' not in html and "name='viewport'" not in html: rebuild_issues.append("Not Mobile Friendly")
            if html.count('<table') > 3: rebuild_issues.append("Outdated Design")
        
        seo_issues = []
        if not is_spa and '<h1' not in html: seo_issues.append("Missing H1 SEO Tags")
        if 'google-analytics.com' not in html and 'googletagmanager' not in html: seo_issues.append("No Traffic Analytics")
        
        # SMART CATEGORIZATION ENGINE
        if rebuild_issues:
            lead_category = "REBUILD"
            issues_str = " | ".join(rebuild_issues)
        elif seo_issues:
            lead_category = "SEO"
            issues_str = " | ".join(seo_issues)
        else:
            lead_category = "AUTOMATION"
            issues_str = "Modern JS Framework (Perfect)" if is_spa else "Perfect Website"
            
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
        
        phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        phones = set(phone_pattern.findall(response.text))
        valid_phone = list(phones)[0] if phones else None
        
        bad_emails = ['your@', 'email@', 'example.com', 'domain.com', 'name@', 'test@', 'info@yoursite', 'no-reply', 'noreply', 'sentry.io', 'wixpress', 'admin@example']
        valid_emails = [e for e in emails if not any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']) and not any(bad in e.lower() for bad in bad_emails)]
        
        if valid_emails:
            return valid_emails[0], valid_phone, lead_category, issues_str
        elif valid_phone:
            return None, valid_phone, lead_category, issues_str
            
    except Exception:
        pass
    return None, None, None, None

def get_indepth_issue_text(issues_str):
    # IN-DEPTH ISSUE EXPANSION: Maps basic flags to painful business impacts
    issue_details = {
        "Not Mobile Friendly": "Missing responsive viewport tags. Your site breaks on modern phones, forcing customers to pinch and zoom (which causes a massive bounce rate).",
        "Slow Load Time": "Core server response took too long. Google penalizes local businesses with slow load times, actively pushing you down the search rankings.",
        "Not Secure (No SSL)": "Your site loads over an unencrypted HTTP connection. Modern browsers now show a red 'Not Secure' warning to your visitors, which breaks customer trust.",
        "Outdated Design": "Built using an outdated HTML structure (table-based layouts). It makes the business look like it hasn't been updated in years compared to local competitors.",
        "Missing H1 SEO Tags": "Your homepage is completely missing the primary H1 header tag. This means Google's algorithm literally doesn't know what keywords to rank you for.",
        "No Traffic Analytics": "No Google Analytics or Tag Manager tracking detected. You have zero visibility on how many people visit your site or where you are losing customers."
    }
    
    bullets = []
    for raw_issue in issues_str.split(' | '):
        if raw_issue in issue_details:
            bullets.append(f"❌ {raw_issue}:\n   {issue_details[raw_issue]}")
            
    if bullets:
        return "\n".join(bullets)
    return "- " + issues_str

def generate_dynamic_email(company, website, lead_category, issues):
    greetings = [f"Hi {company},", f"Hey {company},", f"Hello team at {company},", f"Hi there,"]
    intros = [
        f"I was doing some research on local businesses and came across your website ({website}).",
        f"I recently found your website ({website}) while looking for local businesses in the area."
    ]
    signoffs = ["Best,", "Cheers,", "Regards,", "Thanks,"]

    if lead_category == "REBUILD":
        mid = [
            "I ran a quick technical audit and noticed a few deep issues that are actively turning away mobile customers:",
            "While browsing, I noticed a couple of technical red flags in your source code that usually push mobile visitors away:"
        ]
        pitch = [
            "I'm a freelance developer, and I specialize in rebuilding local business sites to fix these exact issues. A fast, modern, mobile-friendly website usually pays for itself by bringing in just one extra client.",
            "I help local businesses fix these problems by rebuilding their websites to be lightning-fast and fully mobile responsive."
        ]
        cta = ["Would you be open to a quick 5-minute chat to see if a redesign makes sense for you?"]

    elif lead_category == "SEO":
        mid = [
            "Your website looks visually great, but I ran an audit and noticed you are missing some critical SEO tags and traffic tracking software:",
            "I love the design of your site, but I noticed it's missing fundamental on-page SEO optimization in the backend:"
        ]
        pitch = [
            "I specialize in Technical SEO for local businesses. I can optimize your site's code so you actually rank on the first page of Google and start tracking where your customers are coming from.",
            "I help businesses fix these SEO gaps so they rank higher locally and stop losing search traffic to competitors."
        ]
        cta = ["Are you open to a brief 5-minute chat this week to see if we can boost your Google ranking?"]

    else:
        mid = [
            "Honestly, your website looks fantastic. It's fast, mobile-friendly, and perfectly optimized. You clearly invest in your online presence.",
            "I run technical audits on local sites, and yours is one of the few that passed with flying colors. Great job on the web presence!"
        ]
        pitch = [
            "Since your front-facing marketing is locked in, I'm curious if your back-office is fully optimized? I build custom internal software, CRM integrations, and AI automations to help businesses eliminate manual data entry and save hours of admin work every week.",
            "Because your website is already perfect, I wanted to reach out regarding back-office automation. I build custom scripts and AI tools that automate tedious manual tasks, invoicing, and lead follow-ups for local businesses."
        ]
        cta = ["If you have any manual processes you'd love to automate, would you be open to a quick 5-minute chat?"]

    body = f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{random.choice(mid)}\n\n"
    
    if lead_category in ["REBUILD", "SEO"]:
        body += f"{get_indepth_issue_text(issues)}\n\n"
        
    body += f"{random.choice(pitch)}\n\n{random.choice(cta)}\n\n{random.choice(signoffs)}\nKetan\nWeb Developer / Tech Consultant"
    return body

def send_email(target_email, company, website, lead_category, issues):
    sender_email = os.environ.get('GMAIL_USER')
    app_password = os.environ.get('GMAIL_PASS')
    
    if not sender_email or not app_password:
        return False
        
    subject = f"Quick question about {website}"
    body = generate_dynamic_email(company, website, lead_category, issues)
        
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
        
    # v5.0: Manual Target Override
    custom_niche = os.environ.get('CUSTOM_NICHE')
    custom_city = os.environ.get('CUSTOM_CITY')
    
    niche = custom_niche if custom_niche else random.choice(niches)
    city = custom_city if custom_city else random.choice(cities)
    query = f'"{niche}" in "{city}"'
    
    print(f"=== MULTI-SERVICE AGENCY OUTREACH BOT v5.0 ===")
    print(f"Targeting: {query}")
    
    ignore_sites = ['yelp', 'yellowpages', 'bbb', 'angi', 'justia', 'facebook', 'instagram', 'linkedin', 'zillow', 'houzz', 'thumbtack', 'homeadvisor', 'expertise', 'chamberofcommerce', 'tripadvisor', 'mapquest', 'superpages', 'porch', 'indiamart', 'justdial', 'sulekha']
    
    emails_sent_today = 0
    skipped_dirs = 0
    
    try:
        with DDGS() as ddgs:
            # -------------------------------------------------------------
            # NEW FEATURE: Local Map Scan for "NO WEBSITE" Businesses (Great for India)
            # -------------------------------------------------------------
            print("\n[Phase 1] Scanning Local Maps for businesses with NO websites...")
            try:
                # DuckDuckGo Maps API
                maps_results = list(ddgs.maps(query, max_results=30))
                no_web_count = 0
                for place in maps_results:
                    name = place.get('title', '')
                    phone = place.get('phone', '')
                    site = place.get('url', '')
                    
                    if phone and not site: # BINGO! No website, but has phone
                        lead_line = f"Company: {name} | Phone: {phone} | Location: {place.get('address', '')}"
                        if lead_line not in contacted:
                            with open('no_website_leads.txt', 'a', encoding='utf-8') as f:
                                f.write(lead_line + '\n')
                            contacted.add(lead_line)
                            with open(contacted_file, 'a', encoding='utf-8') as f:
                                f.write(lead_line + '\n')
                            no_web_count += 1
                if no_web_count > 0:
                    print(f"  -> BINGO! Found {no_web_count} businesses with NO website but with Phone Numbers. Saved to no_website_leads.txt!")
            except Exception as e:
                pass # Maps might fail if place is too broad, silently skip

            # -------------------------------------------------------------
            # Phase 2: Web Scan for Existing Websites
            # -------------------------------------------------------------
            print("\n[Phase 2] Scanning Web for Technical Audits...")
            results = list(ddgs.text(query, max_results=150))
            
            for result in results:
                if emails_sent_today >= 15: 
                    break
                    
                website_url = result['href']
                name = result['title']
                domain = get_domain(website_url)
                
                if any(site in website_url.lower() for site in ignore_sites): 
                    skipped_dirs += 1
                    continue
                    
                if website_url in contacted or domain in contacted: 
                    continue
                    
                print(f"\nAuditing: {website_url}")
                email, phone, lead_category, issues = analyze_website_and_get_email(website_url)
                
                if email and email not in contacted:
                    print(f"  -> Found {lead_category} Lead! Email: {email}")
                    success = send_email(email, name, website_url, lead_category, issues)
                    
                    if success:
                        print(f"  -> {lead_category} PITCH SENT AUTOMATICALLY!")
                        with open(contacted_file, 'a') as f:
                            f.write(website_url + '\n')
                            f.write(domain + '\n')
                            f.write(email + '\n')
                        contacted.update([website_url, domain, email])
                        emails_sent_today += 1
                        time.sleep(12)
                elif lead_category and phone:
                    print(f"  -> {lead_category} Lead, NO email, but FOUND PHONE: {phone}")
                    with open('phone_leads.txt', 'a', encoding='utf-8') as f:
                        f.write(f"Category: {lead_category} | Company: {name} | Phone: {phone} | URL: {website_url} | Issues: {issues}\n")
                elif lead_category:
                    print(f"  -> {lead_category} site, but NO contact info found.")
                    
            print(f"\nSkipped {skipped_dirs} directory websites.")
    except Exception as e:
        print(f"Error during search: {e}")
        
    print(f"\nJob Complete. Sent {emails_sent_today} automated emails today.")

if __name__ == "__main__":
    main()
