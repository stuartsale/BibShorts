from __future__ import print_function
import bibtexparser as bp
import hashlib
import random
import re            # regular expresions
import requests            # for working with remote resources
import urllib2

from HTMLParser import HTMLParser  # python 2.x
unescape = HTMLParser().unescape

# fake google id (looks like it is a 16 elements hex)
rand_str = str(random.random()).encode('utf8')
google_id = hashlib.md5(rand_str).hexdigest()[:16]

GOOGLE_SCHOLAR_URL = "http://scholar.google.com"
# the cookie looks normally like:
#        'Cookie' : 'GSP=ID=%s:CF=4' % google_id }
# where CF is the format (e.g. bibtex). since we don't know the format yet, we
# have to append it later
HEADERS = {'User-Agent': 'Mozilla/5.0',
           'Cookie': 'GSP=ID=%s' % google_id}

FORMAT_BIBTEX = 4


class bib_entry:

    def __init__(self, bibtex_in):
        """
        Initialise the object with its arxiv reference number
        """
        self.bibtex = bibtex_in
        self.bibtex_dict = bp.loads(self.bibtex).entries_dict.values()[0]
        self.bibtype = self.bibtex_dict['ENTRYTYPE']

        self.search_success = False

    def __cmp__(self, other):
        return cmp(self.key, other.key)

    def get_dx_doi(self):
        """
        Scrape full bibtex off dx.doi.org if a doi is contained in entry
        """

        doi_pattern = re.compile('doi = .*$', re.MULTILINE)

        try:
            doi = doi_pattern.search(self.bibtex).group().lstrip("doi = {").\
                    rstrip("},")

        except AttributeError:
            print("no DOI")
            return

        url = "http://dx.doi.org/" + doi

        url_headers = {"Accept": "application/x-bibtex"}
        r = requests.get(url, headers=url_headers)
        bibtex = r.text
        self.search_sucess = True

        return bibtex

    def get_google_doi(self):
        """
        Scrape full bibtex of google scholar using the doi as search term
        """

        self.search_success = False

        doi_pattern = re.compile('doi = .*$', re.MULTILINE)

        try:
            doi = doi_pattern.search(self.bibtex).group().lstrip("doi = {").\
                    rstrip("},")

        except AttributeError:
            print("no DOI")
            return

        url = GOOGLE_SCHOLAR_URL + '/scholar?q=' + urllib2.quote(doi)

        url_headers = HEADERS
        url_headers['Cookie'] = url_headers['Cookie'] + ":CF=4"
        r = requests.get(url, headers=url_headers)

        bib_pattern = re.compile(r'<a href="([^"]*/scholar\.bib\?[^"]*)')
        ref_list = bib_pattern.findall(r.text)
        bibtex_url = unescape(ref_list[0])

        r = requests.get(bibtex_url)
        bibtex = r.text
        bibtex = bibtex.replace("=", " = ")
        self.search_success = True

        return bibtex

    def merge_bibtex(self, new_bibtex, replace=False):
        """ merge_bibtex(new_bibtex, replace=False)

            Merge a new block of bibtex into the existing bibtex_dict.
            If an attribute appears in both entries, either the original
            or the  new value can be used.

            bibtex_dict is overwritten by this method.

            Parameters
            ----------
            new_bibtex : str
                A new bibtex block as a single, multiline, string
            replace : bool
                Determine whether the new or original value of a 
                shared attribute is used. If False the original, if
                True the new value.

            Returns
            -------
            None
    """
    new_bibtex_dict = bp.loads(new_bibtex).entries_dict.values()[0]

    if replace:
        for key in new_bibtex_dict:
            self.bibtex_dict[key] = new_bibtex_dict[key]

    else:
        for key in new_bibtex_dict:
            if key not in self.bibtex_dict:
                self.bibtex_dict[key] = new_bibtex_dict[key]

    def set_key(self):
        """
        Alter the Bibtex entry's key to match prefered scheme

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        replace_list = ["{", "\\", "}", "'", "`", '"', "\n", "\t", "^", " "]

        try:
            author_list = self.bibtex_dict['author'].split(' and ')
        except:
            author_pattern = re.compile('author = .*\.}\,$|author = .*\t}\,$',
                                        re.MULTILINE | re.DOTALL)
            author_list = (author_pattern.search(self.bibtex).group().
                           lstrip("author = ").rstrip("},")[1:])
            author_list = author_list.split(' and ')

        if len(author_list) == 0:
            raise AttributeError("No author names found")
            return

        name_pattern = re.compile('{[^,]*}')
        name1 = (name_pattern.search(author_list[0]).group().lstrip("{")
                 .rstrip("}"))
        name1 = (name1.replace("{", "").replace("\\", "").replace("}", "").
                 replace("'", "").replace("`", "").replace('"', "").
                 replace("\n", "").replace("\t", "").replace("^", "").
                 replace(" ", "").strip(" "))

        if len(author_list) == 1:
            name2 = "only"

        elif len(author_list) > 1:
            try:
                name2 = name_pattern.search(author_list[1]).group().\
                                lstrip("{").rstrip("}")
                name2 = (name2.replace("{", "").replace("\\", "").
                         replace("}", "").replace("'", "").replace("`", "").
                         replace('"', "").replace("\n", "").replace("\t", "").
                         replace("^", "").replace(" ", "").strip(" "))
            except AttributeError:
                name2 = "only"

        year_pattern = re.compile('year = .*$', re.MULTILINE)
        year = (year_pattern.search(self.bibtex).group().lstrip('year =').
                rstrip(","))

        self.key = name1+"_"+name2+"."+year
        print(self.key)

    def bibtex_write(self, output_obj):
        """
        Dump bibtex to file.
        """

        output_obj.write(self.bib_type+"{"+self.key+",\n")

        for field in self.bibtex_dict:
            if field is not "ENTRYTYPE":
                output_obj.write(" {0} = \{{1}\},\n".format(
                            field, self.bbibtex_dict[field]))
        output_obj.write("}\n")
