from __future__ import print_function
import bibtexparser as bp
from HTMLParser import HTMLParser  # python 2.x
import re            # regular expresions
import requests            # for working with remote resources
import urllib2
import isbnlib as isbn
from isbnlib.registry import bibformatters

import google_scholar
import requirements


unescape = HTMLParser().unescape
bibtex_formatter = bibformatters['bibtex']


class BibEntry(object):
    """ BibEntry

        A class that holds a single bibtex entry.

        It also provides various methods for querying and manipulating
        entries.

        Attributes
        ----------
        bibtex : str
            The raw bibtex
        bibtex_dict : dict
            The bibtex entry as a dict, arranged as key: attribute pairs.
        bibtype : str
            The entry's type (e.g. ARTICLE, INPROCEEDINGS, etc).
        key : str
            The entry's bibtex key
        search_successes : list
            A list of which searches have been succesful
            (e.g. of Google scholar, dx.doi.org, etc).
    """

    def __init__(self, bibtex_in):
        """
        Initialise the object with a string containing a single bibtex
        entry

        Parameters
        ----------
        bibtex_in : str
            The raw bibtex entry
        """
        self.bibtex = bibtex_in
        self.bibtex_dict = bp.loads(self.bibtex).entries_dict.values()[0]
        self.bibtype = self.bibtex_dict['ENTRYTYPE']

        self.key = None
        self.search_successes = []

    def __eq__(self, other):
        if self.key == other.key:
            if 'doi' in self.bibtex_dict and 'doi' in other.bibtex_dict:
                return self.bibtex_dict['doi'] == other.bibtex_dict['doi']
            else:
                return True
        else:
            return False

    def __lt__(self, other):
        self_auth1 = self.key.split("_")[0]
        other_auth1 = other.key.split("_")[0]

        if not self_auth1 == other_auth1:
            return self_auth1 < other_auth1

        self_auth2 = self.key.split(".")[0].split("_")[1]
        other_auth2 = other.key.split(".")[0].split("_")[1]

        if not self_auth2 == other_auth2:
            if self_auth2 == "only":
                return True
            elif other_auth2 == "only":
                return False
            else:
                return self_auth1 < other_auth1

        self_year = self.key.split(".")[1]
        other_year = other.key.split(".")[1]

        return self_year < other_year

    def get_dx_doi(self):
        """
        Scrape full bibtex off dx.doi.org if a doi is contained in entry.

        Parameters
        ----------
        None

        Returns
        -------
        str
            A raw bibtex string as retrieved from dx.doi.org
        """

        doi_pattern = re.compile('doi = .*$', re.MULTILINE)

        try:
            doi = doi_pattern.search(self.bibtex).group().lstrip("doi = {").\
                    rstrip("},")

        except AttributeError:
            raise AttributeError("no DOI")

        url = "http://dx.doi.org/" + doi

        url_headers = {"Accept": "application/x-bibtex"}
        r = requests.get(url, headers=url_headers)

        # trap 503 errors etc
        if r.status_code != requests.codes.ok:
            raise IOError("Error code {0}".format(r.status_code))

        bibtex = r.text

        return bibtex

    def get_google_doi(self):
        """
        Scrape full bibtex of google scholar using the doi as search term.

        Parameters
        ----------
        None

        Returns
        -------
        str
            A raw bibtex string as retrieved from Google scholar
        """

        doi_pattern = re.compile('doi = .*$', re.MULTILINE)

        try:
            doi = doi_pattern.search(self.bibtex).group().lstrip("doi = {").\
                    rstrip("},")

        except AttributeError:
            raise AttributeError("no DOI")

        url = google_scholar.url_ + '/scholar?q=' + urllib2.quote(doi)

        url_headers = google_scholar.headers_
        url_headers['Cookie'] = url_headers['Cookie'] + ":CF=4"
        r = requests.get(url, headers=url_headers)

        # trap 503 errors etc
        if r.status_code != requests.codes.ok:
            raise IOError("Error code {0}".format(r.status_code))

        bib_pattern = re.compile(r'<a href="([^"]*/scholar\.bib\?[^"]*)')
        ref_list = bib_pattern.findall(r.text)
        bibtex_url = unescape(ref_list[0])

        r = requests.get(bibtex_url, headers=url_headers)

        # trap 503 errors etc
        if r.status_code != requests.codes.ok:
            print("Error code {0}".format(r.status_code))
            raise IOError("Error code {0}".format(r.status_code))

        bibtex = r.text
        bibtex = bibtex.replace("=", " = ")

        return bibtex

    def get_isbnlib_isbn(self):
        """ get_isbnlib_isbn()

            scrape Bibtex using the isbnlib and the given isbn.

            Parameters
            ----------
            None

            Returns
            -------
            str
                A raw bibtex string
        """
        if "isbn" in self.bibtex_dict:
            if (isbn.is_isbn10(self.bibtex_dict["isbn"])
                or isbn.is_isbn13(self.bibtex_dict["isbn"])):
                    try:
                        bibtex = bibtex_formatter(
                                    isbn.meta(self.bibtex_dict["isbn"],
                                              service='wcat'))
                        return bibtex
                    except isbn.DataWrongShapeError:
                        pass
            else:
                raise AttributeError("No valid ISBN present")
        else:
            raise AttributeError("No ISBN present")

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

        # find authors
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

        # first author
        name_pattern = re.compile('[^,]*')
        name1 = (name_pattern.search(author_list[0]).group().lstrip("{")
                 .rstrip("}"))
        name1 = (name1.replace("{", "").replace("\\", "").replace("}", "").
                 replace("'", "").replace("`", "").replace('"', "").
                 replace("\n", "").replace("\t", "").replace("^", "").
                 replace(" ", "").strip(" "))

        # check if single author
        if len(author_list) == 1:
            name2 = "only"

        # second author
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

        # find year
        year_pattern = re.compile('year = .*$', re.MULTILINE)
        try:
            year = (year_pattern.search(self.bibtex).group().lstrip('year =')
                    .rstrip(",").replace("{", "").replace("}", ""))
        except AttributeError:
            year = "0000"

        self.key = name1+"_"+name2+"."+year

    def __unicode__(self):
        output_str = ""

        output_str += u"@{0}{{{1},\n".format(self.bibtype, self.key)

        for field in sorted(self.bibtex_dict):
            if field not in ["ENTRYTYPE", "ID"]:
                output_str += u" {0:>9} = {{{1}}},\n".format(
                                        field, self.bibtex_dict[field])
        output_str += "}\n"

        return output_str

    def verify_complete(self):
        """ verify_complete()

            Check if an instance has all the bibtex fields that it
            should have.

            Parameters
            ----------
            None

            Returns
            -------
            verified : bool
                True if all fields are present, False otherwise
            missing_fields : list
                A list of missing fields
        """
        missing_fields = []
        for req in requirements.required[self.bibtype.lower()]:
            if req not in self.bibtex_dict:
                missing_fields.append(req)

        verified = (len(missing_fields) == 0)

        return verified, missing_fields

    def csv_string(self):
        """ csv_string()

            Return a string in csv format

            Parameters
            ----------
            None

            Return
            ------
            out_str : str
                A string set up in csv like format containg key,
                authors, year, title
        """

        out_str = u""

        # key
        out_str += self.key

        # other fields
        for field in ["author", "year", "title"]:
            out_str += u" ; "
            try:
                out_str += u"{0}".format(self.bibtex_dict[field].replace('"',
                                                                         ''))
            except KeyError:
                out_str += u"MISSING"

        return out_str

    @classmethod
    def from_bibtex(cls, bibtex, search=[["dx", False], ["Google", False],
                                         ["isbn", False]]):
        """ from_bibtex(bibtex)

            A factory function that creates a BibEntry instance,
            searches the web to fill in any missing fields and sets
            the entry's key.

            Parameters
            ----------
            bibtex : str
                The raw bibtex string
            search : list
                A list that contains entries which are themselves a list
                of [search engine, replace] where replace indicates if the
                values recovered from that search engine should overwrite
                those already in hand.
                Allowable search engines are: "Google", "dx" .
                If None no searches are performed.

            Returns
            -------
            BibEntry
                A BibEntry object with all attributes set, potentially
                after qquerying some search engine(s)
        """

        new_entry = cls(bibtex)

        for search_engine in search:
            if search_engine[0] == "dx":
                try:
                    search_bibtex = new_entry.get_dx_doi()
                    search_success = True
                except:
                    search_success = False
            elif search_engine[0] == "Google":
                try:
                    search_bibtex = new_entry.get_google_doi()
                    search_success = True
                except:
                    search_success = False
            elif search_engine[0] == "isbn":
                try:
                    search_bibtex = new_entry.get_isbnlib_isbn()
                    search_success = True
                except:
                    search_success = False
            else:
                raise ValueError("Search Engine Name not recognised.")

            if search_success:
                new_entry.search_successes.append(search_engine[0])
                new_entry.merge_bibtex(search_bibtex, search_engine[1])

        new_entry.set_key()
        return new_entry
