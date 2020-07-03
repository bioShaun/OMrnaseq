while read comp
do

    if [ ! -e "${comp}.png" ]
    then
           Rscript volcano.R ./diff_table/${comp}.edgeR.DE_results.txt ${comp} ./
    fi

done<cmp.list
