with open('bot.py', 'r', encoding='utf-8') as f: lines = f.readlines()
start = next(i for i, l in enumerate(lines) if 'Massive list' in l)
end = next(i for i, l in enumerate(lines) if 'Skipped' in l)
for i in range(start, end): lines[i] = '    ' + lines[i]
with open('bot.py', 'w', encoding='utf-8') as f: f.writelines(lines)
