import requests
from collections import defaultdict

MAX_AUTHORS = 5
LAB_LAST_NAMES = set(['Tonkin-Hill', 'Mallawaarachchi'])

def fetch_orcid_publications(orcid_id):
    """Fetch public publications from an ORCID ID."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching ORCID data: {response.status_code}")
        return None

def fetch_orcid_publication_details(orcid_id, put_code):
    """Fetch detailed publication information including authors."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/work/{put_code}"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching publication details: {response.status_code}")
        return None

def format_author_name(name):
    """Format the author's name as 'Lastname, Initial.'"""
    parts = name.split()
    if len(parts) > 1:
        firstname, lastname = parts[0], parts[-1]
        if lastname in LAB_LAST_NAMES:
            return f"**{lastname}, {firstname[0]}**"
        else:
            return f"{lastname}, {firstname[0]}."
    return name  # Fallback if the name does not split correctly

def publications_to_markdown(publications):
    """Convert publications data from ORCID to Markdown format."""
    pubs_by_year = defaultdict(list)
    for publication in publications.get('group', []):
        # Attempt to extract title and publication date
        # print(publication['work-summary'])
        
        title = publication['work-summary'][0].get('title', {}).get('title', {}).get('value', 'No Title')
        type = publication['work-summary'][0].get('type', None)
        journal = publication['work-summary'][0].get('journal-title', None)
        if (journal is None) or (type=='preprint'):
            journal = "Preprint"
        else:
            journal = journal.get('value', 'No Title')
        url = publication['work-summary'][0].get('url', None)
        
        link_type = publication['work-summary'][0].get('external-ids', {}).get('external-id', [{}])[0].get('external-id-type', [{}])
        linkid = publication['work-summary'][0].get('external-ids', {}).get('external-id', [{}])[0].get('external-id-value', [{}])
        if link_type == 'doi':
            weblink = f"https://doi.org/{linkid}"
        elif link_type == 'pmid':
            weblink = f"https://pubmed.ncbi.nlm.nih.gov/{linkid}"

        publication_year = publication['work-summary'][0].get('publication-date', {}).get('year', {}).get('value', 'No Year')

        # Get author names
        put_code = publication['work-summary'][0]['put-code']
        publication_detail = fetch_orcid_publication_details(orcid_id, put_code)
        authors = [contributor['credit-name']['value'] for contributor in publication_detail.get('contributors', {}).get('contributor', []) if 'credit-name' in contributor]
        formatted_authors = [format_author_name(author) for author in authors[:MAX_AUTHORS]]
        
        # Write markdown for each citation
        markdown = f"{title}. "
        markdown += f"{', '.join(formatted_authors)}"
        if len(authors) > MAX_AUTHORS:
            markdown += f" et al., "            
        if journal:
            markdown += f" *{journal}*"
        markdown += f" ({publication_year})"

        if link_type in ['doi', 'pmid']:
            markdown += f"  {{{{< fa-link url=\"{weblink}\" >}}}}"
        
        # print("\n\n")
        # print(markdown)
        # print("********\n\n")
        pubs_by_year[publication_year].append(markdown)

    return pubs_by_year


# Example ORCID ID - Replace 'your_orcid_id' with the actual ORCID ID
orcid_id = '0000-0003-4397-2224'
publications = fetch_orcid_publications(orcid_id)
pubmarkdown = publications_to_markdown(publications)


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
"""     )    
    for year in sorted(pubmarkdown.keys(), reverse=True):
        outfile.write(f"\n## {year}\n")
        for pub in pubmarkdown[year]:
            outfile.write(f"- {pub}\n")
