# -*- coding: utf-8 -*-

import json
import re
import urllib

import helper

BASE_URI = 'http://search.ccb.state.or.us'


def main():
    client = LicenseScraper(BASE_URI)
    client.search(term='Smi')


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

        # print '>>>', content.find('table', attrs={'class': 'bodyWellContentTable'}).find('table').findAll('tr')[4:]

        with open('output.html', 'wb') as file:
            file.write(content.prettify('utf-8'))

        tables = content.findAll('table', attrs={'class': 'bodyText'})

        print '>>> Tables: ', len(tables)

        print tables[0]

        with open('output.json', 'w') as fp:
            json.dump([self.parse(table) for table in tables],
                      fp, indent=4)


    def parse(self, table):
        """Extract all data from a table of results
        """
        header = self.header(table.findAll('tr')[1]) # the header is the second row all the time
        print 'Header is: ', header
        rows = []
        try:
            for tr in table.findAll('tr', attrs={'valign':'top'}):
                rows.extend([self.row(tds) for tds in chunks(tr.findAll('td'), 5)])
            return [dict(zip(header, row)) for row in rows if row]
        except Exception, e:
            pass

    def header(self, tr):
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


def chunks(l, n):
    """Some of the rows present chunks longer than 5 tds
    We need to break these into smaller chunks
    """
    if n < 1:
        n = 1
    return [l[i:i + n] for i in range(0, len(l), n)]


if __name__ == "__main__":
    main()