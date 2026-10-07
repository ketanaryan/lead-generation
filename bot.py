import os
import random
import time
import requests
import re
from bs4 import BeautifulSoup
from ddgs import DDGS
import smtplib
from email.message import EmailMessage

def analyze_website_and_get_email(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        load_time = time.time() - start_time
        
        if response.status_code != 200: return None, None
            
        html = response.text.lower()
        issues = []
        
        if 'name="viewport"' not in html and "name='viewport'" not in html: issues.append("Not Mobile Friendly")
        if load_time > 3.0: issues.append("Slow Load Time")
        if url.startswith("http://"): issues.append("Not Secure (No SSL)")
        if '<h1' not in html: issues.append("Bad SEO")
        if html.count('<table') > 3: issues.append("Outdated Design")
        if 'google-analytics.com' not in html: issues.append("No Analytics")
            
        has_major = any(i in ["Not Mobile Friendly", "Not Secure (No SSL)", "Outdated Design"] for i in issues)
        if not has_major and len(issues) < 2:
            return None, None
            
        email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        emails = set(email_pattern.findall(response.text))
        
        # Smart Feature: If email isn't on the homepage, check the /contact page!
        if not emails:
            base_url = url.rstrip('/')
            for path in ['/contact', '/contact-us']:
                try:
                    contact_response = requests.get(base_url + path, headers=headers, timeout=5)
                    if contact_response.status_code == 200:
                        emails.update(email_pattern.findall(contact_response.text))
                except:
                    pass
        
        phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        phones = set(phone_pattern.findall(response.text))
        valid_phone = list(phones)[0] if phones else None
        
        bad_emails = ['your@email.com', 'email@', 'example.com', 'domain.com', 'name@', 'test@', 'info@yoursite.com']
        valid_emails = [e for e in emails if not any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', 'wixpress.com']) and not any(bad in e.lower() for bad in bad_emails)]
        
        if valid_emails:
            return valid_emails[0], valid_phone, " | ".join(issues)
        elif valid_phone:
            return None, valid_phone, " | ".join(issues)
            
    except Exception:
        pass
    return None, None, None

def send_email(target_email, company, website, issues):
    sender_email = os.environ.get('GMAIL_USER')
    app_password = os.environ.get('GMAIL_PASS')
    
    if not sender_email or not app_password:
        print("Missing Email Credentials in Environment Variables!")
        return False
        
    subject = f"Quick question about {website}"
    body = f"""Hi {company},

I was doing some research on local businesses and came across your website ({website}). 

I noticed a few technical issues that might be hurting your Google ranking and turning away customers on mobile phones:
- {issues}

I am a freelance web developer and I specialize in rebuilding websites for local businesses to fix exactly these issues. A faster, mobile-friendly website usually pays for itself by bringing in just one or two extra jobs.

Would you be open to a quick 5-minute chat to see if a redesign makes sense for you?

Best,
Ketan
Web Developer"""
        
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = target_email
    msg.set_content(body)
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def main():
    # 1. Load Data
    with open('niches.txt') as f: niches = f.read().splitlines()
    with open('cities.txt') as f: cities = f.read().splitlines()
    
    contacted_file = 'contacted.txt'
    if not os.path.exists(contacted_file):
        open(contacted_file, 'w').close()
        
    with open(contacted_file) as f:
        contacted = set(f.read().splitlines())
        
    # 2. Pick Random Target
    niche = random.choice(niches)
    city = random.choice(cities)
    query = f'"{niche}" in "{city}"'
    
    print(f"=== GITHUB ACTIONS OUTREACH BOT ===")
    print(f"Targeting: {query}")
    
    # Ignore huge directories so we only audit small business websites
    ignore_sites = ['yelp', 'yellowpages', 'bbb', 'angi', 'justia', 'facebook', 'instagram', 'linkedin', 'zillow', 'houzz', 'thumbtack', 'homeadvisor', 'expertise', 'chamberofcommerce']
    
    emails_sent_today = 0
    
    try:
        with DDGS() as ddgs:
            # INCREASED to 150 results so it audits a massive amount of websites
            results = list(ddgs.text(query, max_results=150))
            print(f"Found {len(results)} total search results from DuckDuckGo.")
            
            skipped_dirs = 0
            for result in results:
                if emails_sent_today >= 15: # Max 15 emails per run to stay super safe
                    break
                    
                website_url = result['href']
                name = result['title']
                
                if any(site in website_url.lower() for site in ignore_sites): 
                    skipped_dirs += 1
                    continue
                    
                if website_url in contacted: 
                    continue
                    
                print(f"\nAuditing: {website_url}")
                email, phone, website_problems = analyze_website_and_get_email(website_url)
                
                if email and email not in contacted:
                    print(f"  -> Found BAD SITE. Email: {email}")
                    success = send_email(email, name, website_url, website_problems)
                    
                    if success:
                        print(f"  -> EMAIL SENT AUTOMATICALLY!")
                        with open(contacted_file, 'a') as f:
                            f.write(website_url + '\n')
                            f.write(email + '\n')
                        emails_sent_today += 1
                        time.sleep(10) # Pause between emails
                elif website_problems and phone:
                    print(f"  -> Bad site, NO email, but FOUND PHONE: {phone}")
                    with open('phone_leads.txt', 'a') as f:
                        f.write(f"Company: {name} | Phone: {phone} | URL: {website_url} | Issues: {website_problems}\n")
                elif website_problems:
                    print("  -> Bad site, but NO email and NO phone found.")
                else:
                    print("  -> Passed strict audit. Skipping.")
                    
            print(f"\nSkipped {skipped_dirs} big directory websites (Yelp, BBB, etc.)")
    except Exception as e:
        print(f"Error: {e}")
        
    print(f"\nJob Complete. Sent {emails_sent_today} automated emails today.")

if __name__ == "__main__":
    main()
