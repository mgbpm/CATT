CLINVAR_BASE=https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/
CLINVAR_FILE=variant_summary.txt.gz
CLINVAR_MD5=${CLINVAR_FILE}.md5
wget ${CLINVAR_BASE}/${CLINVAR_FILE} -O ${CLINVAR_FILE}
wget ${CLINVAR_BASE}/${CLINVAR_MD5} -O ${CLINVAR_MD5}
if [ `md5 -q ${CLINVAR_FILE}` == `cut -d" " -f1 ${CLINVAR_MD5}` ]
then 
    echo "SUCCESS: Dowloaded and verified most recent ClinVar data release."
else 
    echo "ERROR: ClinVar download md5 checksum does not match! Aborting!"
    exit -1
fi
gunzip ${CLINVAR_FILE}
