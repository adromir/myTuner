import os
import re

template_dir = 'e:/myTuner/app/templates'
dark_class_pattern = re.compile(r'\bdark:[a-zA-Z0-9/-]+\b')

count = 0
for root, _, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = dark_class_pattern.sub('', content)
            # Fix any double spaces created by removal
            new_content = re.sub(r' +', ' ', new_content).replace(' \'', '\'').replace(' "', '"')
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f'Updated {file}')

print(f'Total files updated: {count}')
