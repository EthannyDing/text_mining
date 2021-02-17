#!/bin/bash
set -x
set -v

spm_encode --model=law-finance-gov_eng_fra.model --vocabulary=vocab.eng --vocabulary_threshold=50 < /linguistics/ethan/Canlii_data/historic_html/Legislation/legislation_alltime.merge_dedup_postprocessed.eng > /linguistics/ethan/Canlii_data/historic_html/Legislation/legislation_alltime.merge_dedup_postprocessed.sp.eng
# spm_encode --model=law-finance-gov_eng_fra.model --vocabulary=vocab.fra --vocabulary_threshold=50 < ./test.fra > ./test.fra.sp