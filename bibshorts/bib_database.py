import glob

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

    def __init__(self):
        self.BibEntry_list = []

    def extend_list(self, raw_bibtex):
        """ extend_list(raw_bibtex)

            Add additional entries to the database from some
            raw bibtex.

            Parameters
            ----------
            raw_bibtex : str
                The raw bibtex containing the entry(ies) to be
                added.

            Returns
            -------
            None
        """
        # Split raw_bibtex into individual entries
        bibtex_list = ("@"+entry for entry in raw_bibtex.lstrip("@").split("@")
                       if entry)

        # Convert each raw entry into a BibEntry object
        for entry in bibtex_list:
            try:
                self.BibEntry_list.append(BibEntry.from_bibtex(
                                                    entry,
                                                    search=[["dx", False],
                                                            ["isbn", False]]))
                print(self.BibEntry_list[-1].key,
                      self.BibEntry_list[-1].search_successes)
            except (AttributeError, IndexError, ValueError):
                print("Parsing Failed")

    def __unicode__(self):
        out_str = ""
        for entry in self.BibEntry_list:
            out_str += u"{0:s}\n".format(entry)
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
        # First sort
        self.BibEntry_list.sort()

        for entry in self.BibEntry_list:
            verified, missing = entry.verify_complete()
            if not verified:
                print("{0} is missing entries: {1}  searched: {2}"
                      .format(entry.key, missing, entry.search_successes))

        # Now write
        output = open(filename, "w")
        to_write = unicode(self).encode('utf-8')
        output.write(to_write)
        output.close()

    def csv_dump(self, filename):
        """ csv_dump(filename)

            Dump the database to a csv like file (using semi-colons
            in place of commas).

            Parameters
            ----------
            filename : str
                The name of the file to which the database summary is
                dumped

            Returns
            -------
            None
        """

        # First sort
        self.BibEntry_list.sort()

        # now write
        output_text = u""
        for entry in self.BibEntry_list:
            output_text += u"{0}\n".format(entry.csv_string())

        output = open(filename, "w")
        to_write = output_text.encode('utf-8')
        output.write(to_write)
        output.close()

    @classmethod
    def from_file(cls, filename):
        """ from_file(filename)

            Create a database from a *.bib file

            Parameters
            ----------
            filename : str
                The name of the input bibtex file

            Returns
            -------
            new_database : BibDatabase
        """
        new_database = cls()

        with open(filename, "r") as input_file:
            input_bibtex = input_file.read()

        new_database.extend_list(input_bibtex)
        new_database.remove_duplicates()

        return new_database

    @classmethod
    def from_dir(cls, dirname):
        """ from_dir(dirname)

            Create a database from a directory of *.bib files

            Parameters
            ----------
            dirname : str
                The name directory that contains bibtex files

            Returns
            -------
            new_database : BibDatabase
        """
        new_database = cls()

        filenames = glob.glob("{0}/*.bib".format(dirname))

        for filename in filenames:
            with open(filename, "r") as input_file:
                input_bibtex = input_file.read()

            new_database.extend_list(input_bibtex)
        new_database.remove_duplicates()

        return new_database
