# -*- coding: utf-8 -*-

import argparse
import json
import re
import urllib

import helper

BASE_URI = 'http://search.ccb.state.or.us'


def main():
    parser = argparse.ArgumentParser(description='Scrape CCB License Information')
    parser.add_argument('term', help='The search term')
    parser.add_argument('--name', action='store_true', help='Indicates the search term is a person\'s name')
    
    args = parser.parse_args()

    client = LicenseScraper(BASE_URI)
    
    key = 'name' if args.name else 'term'
    print client.search(**{key:args.term})


class LicenseScraper(helper.Scraper):
    def search(self, term=None, name=None):
        """Scrape CCB License Information

        CCB WEB SITE SEARCH TIPS

        - The most accurate search is by CCB license number. If you have that 
        number in your records, you will save time by finding it.
        - Make the search fairly broad and include a key word. So, search for 
        "Schmitt" instead of "Schmitt Contracting Inc" or search for "concrete" 
        instead of "Joes Concrete".
        - Leave out punctuation such as apostrophes and hyphens.
        - If you're searching for a phone number, search on the numbers only, 
        i.e. 5039991234 instead of (503) 999-1234.
        - Verify your spelling. A simple misspelling of a word will cause your 
        search to fail.

        :returns: List of CCB License Info
        """
        q = '%%%s' % name if name else (term or '')
        q = re.compile(r'[\'\-\(\)]').sub('', q)

        content = self.get('/search/search_results_list.asp', 
                           params=dict(search_criteria=q))

        # with open('output.html', 'wb') as file:
        #     file.write(content.prettify('utf-8'))

        tables = content.findAll('table', attrs={'class': 'bodyText'})
        parsed = [x for x in [self.parse(table) for table in tables] if x]

        # with open('output.json', 'w') as fp:
        #     json.dump(parsed, fp, indent=4)

        return json.dumps(parsed, indent=4)


    def parse(self, table):
        """Extract all data from a table of results
        """
        trs = table.findAll('tr')
        description = trs[0].find('td').text.split('&mdash')[0].strip()
        header = self.header(trs[1]) # the header is the second row all the time
        trs = None

        rows = []

        try:
            for tr in table.findAll('tr', attrs={'valign':'top'}):
                rows.extend([self.row(tds) for tds in chunks(tr.findAll('td'), 5)])
                results = [dict(zip(header, row)) for row in rows if row]
            
            total = len(results)
            return {'description':description, 'total':total, 'results':results} if total else None
        except Exception, e:
            pass

    def header(self, tr):
        """Extract the header from the table (used as keys for the data items)
        """
        return tuple([helper.slugify(td.text) for td in tr.findAll('td')] + ['url'])

    def row(self, tds):
        """Parse CCB/OCHI/ID #, status, name, address, detail_url.
        """
        try:
            return tuple([td.text.strip('\r\n ') for td in tds[:4]] + \
                         [self.resolve('/search/%s' % tds[4].find('a')['href'])])
        except Exception, e: # not a valid row
            pass

    def summary(self, url):
        pass


def chunks(items, length=1):
    """Some of the rows present chunks longer than 5 tds
    We need to break these into smaller chunks
    """
    return [items[i:i + length] for i in range(0, len(items), length)]


if __name__ == "__main__":
    main()