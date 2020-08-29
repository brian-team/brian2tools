from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter
import brian2
import os, inspect, datetime
from .expander import *


class MdExporter(BaseExporter):
    """
    Device to export human-readable format in markdown from the Brian model.
    The class derives from BaseExporter to use the dictionary representation
    to export model descriptions.
    """

    def build(self, direct_call=True, debug=False,
              expand_class=None, filename=None, author=None,
              add_meta=False):
        """
        Build the exporter

        Parameters
        ----------
        direct_call : bool
            To check whether build() called directly
        debug : bool, optional
            To run in debug mode, that will print the output markdown text
        expand_class : `Std_mdexpander` or its instance
            Class that has collections of functions to expand baseexport
            dictionary format in markdown
        filename : str, optional
            If mentioned, the markdown text would be written in that
            particular filename. By default, the same python filename
            is used
        author : str, optional
            Author field to add in the metadata
        add_meta : bool, optional
            Whether to attach meta field in output markdown text
        """

        # get source file name, datetime and Brian version
        frame = inspect.stack()[1]
        user_file = inspect.getmodule(frame[0]).__file__
        date_time = datetime.datetime.now()
        brian_version = brian2.__version__
        # if author name is given
        if author:
            if type(author) != str:
                raise Exception('Author field should be string, \
                                 not {} type'.format(type(author)))
        else:
            author = '-'
        # prepare meta-data
        meta_data = italics('Filename: {}\
                             \nAuthor: {}\
                             \nDate and localtime: {}\
                             \nBrian version: {}'.format(user_file, author,
                             date_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                             brian_version)) + endl + horizontal_rule() + endl
        self.meta_data = meta_data
        # chech expand_class
        if expand_class:
            if not isinstance(expand_class, Std_mdexpander):
                raise NotImplementedError('The expand class must be derived \
                                           from `Std_mdexpander` to override \
                                           expand functions')
            self.expand_class = expand_class
        else:
            self.expand_class = Std_mdexpander
        # check output filename
        if filename:
            if not isinstance(filename, str):
                raise Exception('Output filename should be string, \
                                 not {} type'.format(type(filename)))
            self.filename = filename
        else:
            self.filename = user_file[:-3] # to remove '.py'
        # start creating markdown descriptions using expand_class
        md_exporter = self.expand_class
        self.md_text = md_exporter.create_md_string(self.runs)
        # check whether meta data should be added
        if add_meta:
            self.md_text = meta_data + self.meta_data
        # check whether in debug mode to print output in stdout
        if debug:
            print(self.md_text)
        else:
            # start writing markdown text in file
            md_file = open(self.filename + '.md', "w")
            md_file.write(self.md_text)
            md_file.close()


he_device = MdExporter()
all_devices['mdexport'] = he_device
