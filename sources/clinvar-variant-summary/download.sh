BASE=https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/
FILE=variant_summary.txt.gz
MD5=${FILE}.md5

wget ${BASE}/${FILE} -O ${FILE}
wget ${BASE}/${MD5} -O ${MD5}
if [ `md5 -q ${FILE}` == `cut -d" " -f1 ${MD5}` ]
then
    echo "SUCCESS: Dowloaded and verified most recent ClinVar Variant Summary data release."
else
    echo "ERROR: ClinVar Variant Summary download md5 checksum does not match! Aborting!"
    exit -1
fi
gunzip ${FILE}