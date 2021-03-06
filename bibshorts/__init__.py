from __future__ import print_function
import requests            # for working with remote resources
import re            # regular expresions
import os




class bib_entry:

    def __init__(self, bibtex_in):
        """ 
        Initialise the object with its arxiv reference number
        """
        self.bibtex = bibtex_in

    def __cmp__(self, other):
        return cmp(self.key, other.key)


    def get_bibtex_doi(self):
        """ 
        Scrape full bibtex off web if a doi is contained in entry
        """

        self.search_success = False

        doi_pattern = re.compile('doi = .*$', re.MULTILINE)
        
        try:
            doi = doi_pattern.search(self.bibtex).group().lstrip("doi = {").\
                    rstrip("},")

        except AttributeError:
            print("no DOI")
            return

        print(doi)
        url = "http://dx.doi.org/" + doi

        url_headers = {"Accept": "application/x-bibtex"}
        r = requests.get(url, headers=url_headers)
        print(r.text)
        self.bibtex = r.text
        self.search_sucess = True


    def set_key(self):
        """ 
        Alter the Bibtex entry's key to match prefered scheme
        """

        replace_list = ["{", "\\", "}", "'", "`", '"', "\n", "\t", "^", " "]


        author_pattern = re.compile('author = .*\.}\,$|author = .*\t}\,$', 
                                    re.MULTILINE | re.DOTALL)
        author_list = author_pattern.search(self.bibtex).group().\
                        lstrip("author = ").rstrip("},")[1:]
        author_list = author_list.split(' and ')


        if len(author_list)==0:
            print("ERROR")
            return

        name_pattern = re.compile('{[^,]*}')
        name1 = name_pattern.search(author_list[0]).group().lstrip("{").rstrip("}")
        name1 = name1.replace("{","").replace("\\","").replace("}","").\
                      replace("'","").replace("`","").replace('"',"").\
                      replace("\n","").replace("\t","").replace("^","").\
                      replace(" ","").strip(" ")


        if len(author_list)==1:
            name2 = "only"

        elif len(author_list)>1:
            try:
                name2 = name_pattern.search(author_list[1]).group().\
                                lstrip("{").rstrip("}")
                name2 = name2.replace("{","").replace("\\","").\
                              replace("}","").replace("'","").replace("`","").\
                              replace('"',"").replace("\n","").\
                              replace("\t","").replace("^","").\
                              replace(" ","").strip(" ")
            except AttributeError:
                name2 = "only"

        
        year_pattern = re.compile('year = .*$', re.MULTILINE)
        year = year_pattern.search(self.bibtex).group().lstrip('year =').\
                        rstrip(",")

        self.key = name1+"_"+name2+"."+year
        print(self.key)



    def bibtex_write(self, output_file):
        """
        Dump bibtex to file, checking key not already used
        """
        for other_key in written_keys:
            if other_key==self.key:
                self.key = self.key+"a"

            written_keys.append(self.key)

        split_bibtex = self.bibtex.split("\n")

        output_file.write(self.bib_type+"{"+self.key+",\n")

        for n in range(1, len(split_bibtex)):
            output_file.write(split_bibtex[n]+"\n")
