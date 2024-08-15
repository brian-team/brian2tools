from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter
import os
import inspect
import subprocess
from .expander import *


class MdExporter(BaseExporter):
    """
    Device to export human-readable format in markdown from the Brian model.
    The class derives from BaseExporter to use the dictionary representation
    to export model descriptions.
    """

    def build(self, direct_call=True, debug=False, expander=None,
              filename=None, additional_formats=None, template_type='default', temp_dir_path=None):
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

        additional_formats : str or list of str or all
                If user wants to have the output file in additional_formats they
                can specify them under this variable and the options are pdf, 
                latex, html and all.  

        template_type : str   
            Based on your selected template, it will rendered otherwise
            a default template will be used for rendering              
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

        if temp_dir_path is not None:
            self.expander.set_temp_dir_path(temp_dir_path)
    

        # start creating markdown descriptions using expander
        self.md_text = self.expander.create_md_string(self.runs, template_type)

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
            source_file = self.filename + ".md"
            md_file = open(source_file, "w")
            md_file.write(self.md_text)
            md_file.close()
            
            # Check if Pandoc is installed
            try:
                subprocess.check_call(["pandoc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                raise Exception("Pandoc is not installed. Please install Pandoc and try again.")
            
            formats_extensions = {'latex':'.tex', 'html':'.html', 'pdf':'.pdf'}
            if isinstance(additional_formats, str):
                if additional_formats == "all":
                    formats = ['latex', 'html', 'pdf']
                else:
                    formats = [additional_formats]
            else:
                formats = additional_formats if additional_formats is not None else []
            for format_name in formats:
                filename = self.filename + formats_extensions[format_name]
                try:
                    subprocess.run(["pandoc", "--from", "markdown", "--to", format_name, "-o", filename, source_file],
                                   check=True)
                    print("Conversion complete! Files generated:", filename) 
                except subprocess.CalledProcessError as ex:
                    print(f"Could not generate format '{format_name}': {str(ex)}")
        else:
            pass  # do nothing


md_device = MdExporter()
all_devices['markdown'] = md_device
