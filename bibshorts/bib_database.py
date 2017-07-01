from bib_entry import BibEntry


class BibDatabase(object):
    """ BibDatabase

        A class that holds a list of BibEntry instances each
        representing an entry in a bibtex file.

        Parameters
        ----------
        raw_bibtex : str
            Some raw bibtex from which to create a database

        Attributes
        ----------
        BibEntry_list : list(BibEntry)
            The list of individual BibEntry instances, each
            representing an entry in a bibtex file.
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
        for entry in self.BibEntry_list:
            out_str += "{0:s}\n".format(entry)
        return out_str

    def __len__(self):
        return len(self.BibEntry_list)

    def remove_duplicates(self):
        """ remove_duplicates()

            Remove duplicate entries in BibEntry_list

            Parameters
            ----------
            None

            Retturns
            --------
            None
        """
        i = 0
        while i < self.__len__():
            for j in range(i):
                if self.BibEntry_list[i] == self.BibEntry_list[j]:
                    del self.BibEntry_list[i]
                    break
            else:
                i += 1

    def write_to_file(self, filename):
        """ write_to_file(filename)

            Write the bibtex database to a *.bib file.

            Parameters
            ----------
            filename : str
                The name of the file to write to.

            Returns
            -------
            None
        """
        output = open(filename, "w")
        output.write(str(self))
        output.close()
