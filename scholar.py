import requests
import bibtexparser
from collections import defaultdict
import re

LAB_LAST_NAMES = set(['Tonkin-Hill', 'Mallawaarachchi'])

def remove_latex_commands(text):
    text = text.replace(r"$\alpha$", "α")
    # Map of LaTeX formatted characters to their standard letter equivalents
    # Expanded to handle more specific cases like umlauts
    latex_to_standard = {
        r"\\'([a-zA-Z])": r"\1", r'\\"([a-zA-Z])': r'\1', r'\\^([a-zA-Z])': r'\1', 
        r'\\`([a-zA-Z])': r'\1', r'\\~([a-zA-Z])': r'\1', r'\\=([a-zA-Z])': r'\1', 
        r'\\\.([a-zA-Z])': r'\1', r'\\u([a-zA-Z])': r'\1', r'\\v([a-zA-Z])': r'\1', 
        r'\\H([a-zA-Z])': r'\1', r'\\c([a-zA-Z])': r'\1', r'\\d([a-zA-Z])': r'\1', 
        r'\\b([a-zA-Z])': r'\1', r'\\t([a-zA-Z]{2})': r'\1', r'\\r([a-zA-Z])': r'\1', 
        r'\\aa': 'a', r'\\AA': 'A', r'\\ae': 'ae', r'\\AE': 'AE',
        r'\\o': 'o', r'\\O': 'O', r'\\l': 'l', r'\\L': 'L', r'\\ss': 'ss',
        r'\\i': 'i', r'\\j': 'j'
    }
    
    # Remove braces around letters, keeping the letters
    text = re.sub(r'{([a-zA-Z])}', r'\1', text)
    
    # Apply replacements for LaTeX commands with their standard equivalents
    for latex_command, replacement in latex_to_standard.items():
        text = re.sub(latex_command, replacement, text)
    
    # Remove any remaining LaTeX commands (simplistic approach) and braces
    text = re.sub(r'\\[a-zA-Z]+\{? ?', '', text)
    text = re.sub(r'[{}]', '', text)
    
    return text


# Step 1: Download the BibTeX file
url = "https://scholar.googleusercontent.com/citations?view_op=export_citations&user=rpyuABcAAAAJ&citsig=ALAJMKEAAAAAZhN6s0ppVucahMZPdrPrFwQGeXY&hl=en"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
response = requests.get(url, headers=headers)
bibtex_str = response.text

print(bibtex_str)

# Step 2: Parse the BibTeX file
parser = bibtexparser.loads(bibtex_str)
entries = parser.entries

# Step 3: Convert the citations into Markdown
citations_by_year = defaultdict(list)

for entry in entries:
    # Process authors to replace first names with initials
    authors = remove_latex_commands(entry.get('author', '')).replace('others', 'et al.').split(' and ')
    processed_authors = []
    for author in authors:
        parts = author.split(', ')
        if len(parts) > 1:
            initials = ''.join([part[0] + '.' for part in parts[1].split()])
            processed_authors.append(f"{parts[0]}, {initials}")
        else:
            processed_authors.append(author)
        if parts[0] in LAB_LAST_NAMES:
            processed_authors[-1] = f"**{processed_authors[-1]}**"
    entry['author'] = ', '.join(processed_authors)
    
    # Organize by year
    year = entry.get('year', 'Unknown Year')
    citations_by_year[year].append(entry)

# Output the citations in Markdown, organized by year
with open("./content/publications.md", "w") as outfile:
    outfile.write(
"""
---
title: Publications
hideTitle: true
authorbox: false
sidebar: false
menu: main
weight: 4
---

This list is updated occasionally. A full list can be found on [Google Scholar](https://scholar.google.co.uk/citations?user=rpyuABcAAAAJ&hl=en&oi=ao) or [Orcid](https://orcid.org/0000-0003-4397-2224).

---
""")
    for year, entries in sorted(citations_by_year.items(), reverse=True):
        outfile.write(f"\n## {year}\n")
        for entry in entries:
            outfile.write(f"- {entry.get('author', 'No Author')}, {remove_latex_commands(entry.get('title', 'No Title'))}.  *{entry.get('journal', 'No Journal')}* ({entry.get('year', '')}).\n")
