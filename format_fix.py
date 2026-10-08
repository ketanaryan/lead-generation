with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('f\"Source: Directory ({domain}) | Phone: {phone} | Extracted Email: {email}\\n\"', 'f\"Name: {name} | Category: DIRECTORY_LEAD | Source: {domain} | Phone: {phone} | URL: {website_url}\\n\"')
content = content.replace('f\"Category: {lead_category} | Tech: {tech_data[''platform'']} | Phone: {phone} | URL: {website_url}\\n\"', 'f\"Name: {name} | Category: {lead_category} | Tech: {tech_data[''platform'']} | Phone: {phone} | URL: {website_url}\\n\"')
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)
