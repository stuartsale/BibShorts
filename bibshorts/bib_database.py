from bib_entry import BibEntry


class BibDatabase(object):
    """
    """

    def __init__(self, raw_bibtex):
        # SPlit raw_bibtex into individual entries
        bibtex_list = ("@"+entry for entry in raw_bibtex.lstrip("@").split("@")
                       if entry)

        self.BibEntry_list = []

        # Convert each raw entry into a BibEntry object
        for entry in bibtex_list:
            self.BibEntry_list.append(BibEntry.from_bibtex(entry))
            print self.BibEntry_list[-1].key

    def __str__(self):
        out_str = ""
        for entry in self.BibEntry_list :
            out_str += "{0:s}\n".format(entry)
        return out_str
