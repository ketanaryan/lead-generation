with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('    phone_leads_harvested = 0', '    phone_leads_harvested = 0
    seen_domains = set()')
content = content.replace('                domain = get_domain(website_url)', '                domain = get_domain(website_url)
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)')
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)
