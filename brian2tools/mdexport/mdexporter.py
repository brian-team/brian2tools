from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter
import os
import inspect
from .expander import *


class MdExporter(BaseExporter):
    """
    Device to export human-readable format in markdown from the Brian model.
    The class derives from BaseExporter to use the dictionary representation
    to export model descriptions.
    """

    def build(self, direct_call=True, debug=False, expander=None,
              filename=None):
        """
        Build the exporter

        Parameters
        ----------
        direct_call : bool
            To check whether build() called directly

        debug : bool, optional
            To run in debug mode, that will print the output markdown text

        expander : `MdExpander` or its instance
            Class that has collections of functions to expand baseexport
            dictionary format in markdown

        filename : str, optional
            By default, no file writing is done
            If mentioned, the markdown text would be written in that
            particular filename. When empty string '' is passed the user file
            name would be taken
        """
        # buil_on_run = True but called build() directly
        if self.build_on_run and direct_call:
            raise RuntimeError('You used set_device with build_on_run=True '
                               '(the default option), which will '
                               'automatically build the simulation at the '
                               'first encountered run call - do not call '
                               'device.build manually in this case. If you '
                               'want to call it manually, '
                               'e.g. because you have multiple run calls, use'
                               ' set_device with build_on_run=False.')

        # if already built
        if self.has_been_run:
            raise RuntimeError('The network has already been built and run '
                               'before. To build several simulations in '
                               'the same script, call "device.reinit()" '
                               'and "device.activate()". Note that you '
                               'will have to set build options (e.g. the '
                               'directory) and defaultclock.dt again.')

        # change the flag
        self.has_been_run = True

        # check expander
        if expander:
            if not issubclass(type(expander), MdExpander):
                raise NotImplementedError('The expand class must be a \
                                           sub-class of `MdExpander` \
                                           to override expand functions')
            self.expander = expander
        else:
            # default standard md expander
            self.expander = MdExpander()

        # start creating markdown descriptions using expander
        self.md_text = self.expander.create_md_string(self.runs)

        # check output filename
        if filename:
            if not isinstance(filename, str):
                raise Exception('Output filename should be string, \
                                 not {} type'.format(type(filename)))
            self.filename = filename
        # auto-select filename
        elif isinstance(filename, str):
            # get source file name
            self.filename = self.expander.user_file[:-3]
        else:
            self.filename = None

        # check whether in debug mode to print output in stdout
        if debug:
            print(self.md_text)
        elif self.filename:
            # start writing markdown text in file
            md_file = open(self.filename + '.md', "w")
            md_file.write(self.md_text)
            md_file.close()
        else:
            pass  # do nothing


md_device = MdExporter()
all_devices['markdown'] = md_device
