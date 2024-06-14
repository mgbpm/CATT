import helper
import yaml
import os
import pandas as pd

sources = []


def count():
    print(len(sources))


def show():
    for s in sources:
        print(s.name)


def source_list():
    tmp_list = []
    for s in sources:
        tmp_list.append(s.name)
    return tmp_list


def df():
    dataframe = pd.DataFrame(columns=['name', 'suffix', 'path', 'url', 'download_file', 'file', 'gzip', 'header_row',
                                      'skip_rows', 'delimiter', 'quoting', 'strip_hash', 'md5_url', 'md5_file',
                                      'template', 'dictionary', 'mapping'])
    for s in sources:
        dataframe.loc[len(dataframe)] = [
            s.name, s.suffix, s.path, s.url, s.download_file,
            s.file, s.gzip, s.header_row,
            s.skip_rows, s.delimiter, s.quoting,
            s.strip_hash, s.md5_url, s.md5_file,
            s.template, s.dictionary, s.mapping
        ]

    dataframe.set_index('name')
    return dataframe


def load(sources_path, selected_sources):
    for root, dirs, files in os.walk(sources_path):
        for f in files:
            if f == 'config.yml':
                name = os.path.basename(root)
                if (name in selected_sources) or (len(selected_sources) == 0):
                    file = str(os.path.join(sources_path, os.path.basename(root), f))
                    Source(file)
                    helper.debug(file)


class Source:

    # keep a list of sources
    def __init__(self, configfile):
        path = configfile.replace('config.yml', '')[:-1]  # path is everything but trailing /config.yml
        with (open(configfile, "r") as stream):
            try:
                config = yaml.safe_load(stream)[0]
                helper.debug("config:", str(configfile))
                helper.debug(config)
                # add to config dataframe
                self.name = config.get('name')
                self.suffix = config.get('suffix')
                self.path = path
                self.url = config.get('url')
                self.download_file = config.get('download_file')
                self.file = config.get('file')
                self.gzip = config.get('gzip')
                self.header_row = config.get('header_row')
                self.skip_rows = config.get('skip_rows')
                self.delimiter = config.get('delimiter')
                self.quoting = config.get('quoting')
                self.strip_hash = config.get('strip_hash')
                self.md5_url = config.get('md5_url')
                self.md5_file = config.get('md5_file')
                self.template = config.get('template')
                self.dictionary = 'dictionary.csv'
                self.mapping = 'mapping.csv'

            except yaml.YAMLError as exc:
                helper.critical(exc)
                exit(-1)

        # add new source to the shared class list
        sources.append(self)
