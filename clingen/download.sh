CLINGEN_DOSAGE_URL="https://search.clinicalgenome.org/kb/gene-dosage/download"
CLINGEN_DOSAGE_FILE=gene-dosage-sensitivity.tsv
wget ${CLINGEN_DOSAGE_URL} -O ${CLINGEN_DOSAGE_FILE}

#wget ${CLINGEN_BASE}/${CLINGEN_FILE} -O ${CLINGEN_FILE}
#wget ${CLINGEN_BASE}/${CLINGEN_MD5} -O ${CLINGEN_MD5}
#if [ `md5 -q ${CLINGEN_FILE}` == `cut -d" " -f1 ${CLINGEN_MD5}` ]
#then
    #echo "SUCCESS: Dowloaded and verified most recent ClinVar data release."
#else
    #echo "ERROR: ClinVar download md5 checksum does not match! Aborting!"
    #exit -1
#fi
#gunzip ${CLINGEN_FILE}
