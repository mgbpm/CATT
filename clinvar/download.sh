CLINVAR_BASE=https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/

CLINVAR_FILE_1=variant_summary.txt.gz
CLINVAR_MD5_1=${CLINVAR_FILE_1}.md5

# wget ${CLINVAR_BASE}/${CLINVAR_FILE_1} -O ${CLINVAR_FILE_1}
# wget ${CLINVAR_BASE}/${CLINVAR_MD5_1} -O ${CLINVAR_MD5_1}
# if [ `md5 -q ${CLINVAR_FILE_1}` == `cut -d" " -f1 ${CLINVAR_MD5_1}` ]
# then
#     echo "SUCCESS: Dowloaded and verified most recent ClinVar variant summary data release."
# else
#     echo "ERROR: ClinVar download md5 checksum does not match! Aborting!"
#     exit -1
# fi
# gunzip ${CLINVAR_FILE_1}


CLINVAR_FILE_2=submission_summary.txt.gz
CLINVAR_MD5_2=${CLINVAR_FILE_2}.md5

wget ${CLINVAR_BASE}/${CLINVAR_FILE_2} -O ${CLINVAR_FILE_2}
wget ${CLINVAR_BASE}/${CLINVAR_MD5_2} -O ${CLINVAR_MD5_2}
if [ `md5 -q ${CLINVAR_FILE_2}` == `cut -d" " -f1 ${CLINVAR_MD5_2}` ]
then
    echo "SUCCESS: Dowloaded and verified most recent ClinVar submission summary data release."
else
    echo "ERROR: ClinVar download md5 checksum does not match! Aborting!"
    exit -1
fi
gunzip ${CLINVAR_FILE_2}
