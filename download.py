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


def all_files(source_files_df, force):
    download_count = 0
    for i, s in source_files_df.iterrows():
        if download(s, force):
            download_count = download_count + 1

    if download_count > 0:
        helper.info("Downloading complete;", download_count, "files.")
    else:
        helper.info("All files present. No files to download.")


def download(source, force):
    # TODO: use os path join instead

    name = source.get('name')
    source_path = source.get('path')
    file = source.get('file')
    file_path = ''
    if file:
        file_path = source_path + '/' + file
        helper.debug("datafile specified for ", name, "as", file_path)

    # if not forced, let's check if the file already exists to see if we need to download or not
    if not force:
        if len(file_path) > 0:
            if isfile(file_path) and access(file_path, R_OK):
                helper.debug("Found existing readable file", file_path)
                # False indicates we did not download file
                return False
        else:
            helper.critical("No datafile specified for", name, "!")
            exit(-1)

    # we need to download the file
    download_file = source.get('download_file')
    download_file_path = ''
    if download_file:
        download_file_path = source_path + '/' + download_file
        helper.debug("download_file specified for ", name, "as", download_file)
    md5_file = source.get('md5_file')
    md5_file_path = ''
    if md5_file:
        md5_file_path = source_path + '/' + md5_file
    md5_hash_downloaded = ''
    md5_url = source.get('md5_url')
    url = source.get('url')
    if url:
        if download_file:
            helper.download(url, download_file_path)
            file_we_downloaded = download_file_path
        else:
            helper.download(url, file_path)
            file_we_downloaded = file_path
        if md5_url:  # if we are doing md5 check then get the hash for the downloaded file
            md5_hash_downloaded = helper.get_md5(file_we_downloaded)
        helper.info("Completed data file download;", file_we_downloaded)
    else:
        print("ERROR: no url for", file, "for source", source.get('name'), "; Please acquire manually.")
        helper.critical("No url for", file, "for source", source.get('name'), "; Please acquire manually.")
        exit(-1)
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

    # unzip the downloaded file if configured to do so and output as "file"
    gzip_flag = source.get('gzip')
    if gzip_flag:
        if file != download_file:  # for gzip datafile and download file should be different
            helper.gunzip_file(download_file_path, file_path)
        else:
            helper.error("gzip option requires differing data/download file names for", name)

    # else:  if there's a future case where we need to change the name of a non-gzip downloaded file afterward

    # return True since we downloaded a file
    return True
