# local modules
import helper

# other libraries
from os import access, R_OK
from os.path import isfile

#########################
#
# DOWNLOAD DATA FILES
#
#########################


def all(sourcefiles, force):
    download_count = 0
    for i, s in sourcefiles.iterrows():
        if download(s, force):
            download_count = download_count + 1

    helper.info("Downloading complete;", download_count, "files.")
    exit(0)


def download(s, force):
    downloaded = False
    name = s.get('name')
    source_path = s.get('path')
    download_file = s.get('download_file')
    download_file_path = ''
    if download_file:
        download_file_path = source_path + '/' + download_file
        helper.debug("download_file specified for ", name, "as", download_file)
    md5_file = s.get('md5_file')
    md5_file_path = ''
    if md5_file:
        md5_file_path = source_path + '/' + md5_file
    datafile = s.get('file')
    datafile_path = ''
    if datafile:
        datafile_path = source_path + '/' + datafile
        helper.debug("datafile specified for ", name, "as", datafile_path)
    # see if the file is present
    need_download = False
    if len(datafile_path) > 0:
        if force:
            need_download = True
        else:
            if isfile(datafile_path) and access(datafile_path, R_OK):
                helper.debug("Found existing readable file", datafile_path)
            else:
                if args.download:
                    need_download = True
                else:
                    helper.critical("ERROR: missing source file", datafile_path, "; specify --download to acquire.")
                    exit(-1)
    else:
        helper.critical("No datafile specified for", name, "!")
        exit(-1)
    if need_download:
        if args.download:
            downloaded = True
            md5_hash_approved = ''
            md5_hash_downloaded = ''
            md5_url = s.get('md5_url')
            downloaded_file_path = ''
            url = s.get('url')
            if url:
                if download_file:
                    r = helper.download(url, download_file_path)
                    downloaded_file_path = download_file_path
                else:
                    r = helper.download(url, datafile_path)
                    downloaded_file_path = datafile_path
                if md5_url:  # if we are doing md5 check then get the hash for the downloaded file
                    md5_hash_downloaded = helper.get_md5(downloaded_file_path)
                helper.info("Completed data file download;", downloaded_file_path)
            else:
                print("WARNING: no url for", datafile, "for", s.get('name'), "; Please acquire manually.")
            if md5_url:
                if md5_file:
                    r = helper.download(md5_url, md5_file_path)
                    md5_hash_approved = r.text.split(' ')
                    if md5_hash_downloaded in md5_hash_approved:
                        helper.info("MD5 check successful")
                    else:
                        helper.error("ERROR: MD5 check failed")
                        helper.error("Approved:", md5_hash_approved)
                        helper.error("Downloaded:", md5_hash_downloaded)
                        exit(-1)
                else:
                    helper.warning("WARNING: md5_url specified but not md5_file. Not performing checksum.")
            gzip_flag = s.get('gzip')
            if gzip_flag:
                if datafile != download_file:  # for gzip datafile and download file should be different
                    helper.gunzip_file(downloaded_file_path, datafile_path)
                else:
                    helper.error("gzip option requires diffirng data/download file names for", name)
            # else:  if there's a future case where we need to change the name of a non-gzip downloaded file afterward

    else:
        helper.debug("Data file", datafile, "already present.")

    return downloaded