# OMrnaseq: a rnaseq pipeline based on luigi

OMrnaseq, developed at the [OnMath](http://www.onmath.cn/), is designed for analysis RNAseq data. Including 4 major modules: fastqc, mapping, quant and enrich.
- qc: using [fastqc](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/) to examine basic information (data size, GC, Q30) about fastq files.
- mapping: using [STAR](https://github.com/alexdobin/STAR) to map reads to the genome.
- quant: using [kallisto](https://pachterlab.github.io/kallisto/) to quantifying abundances, and using [edgeR](https://bioconductor.org/packages/release/bioc/html/edgeR.html) to perform differential analysis.
- enrich: using [goseq](https://bioconductor.org/packages/release/bioc/html/goseq.html) and [KOBAS](http://kobas.cbi.pku.edu.cn/) to analsyis enrichment of differential expressed gene to GO Terms and KEGG pathways.


## virtualenv

OMrnaseq is under development, so its better to install it in a virtualenv, so you can keep up with the updating.
virtualenvwrapper is a set of extensions to virtualenv tool. Its convinient to using for virtualenv management.

```bash

# install virtualenvwrapper
pip install virtualenvwrapper

# configure your bash profile
# add below two command to your ~/.bash_profile
export WORKON_HOME=/your/virturalenv/path
source /usr/bin/virtualenvwrapper.sh

# make OMrnaseq virturalenv
mkvirtualenv OMrnaseq

# enter OMrnaseq virturalenv
workon OMrnaseq

```

## Dependencies

Before install OMrnaseq, you need to install [omplotr](https://github.com/bioShaun/omplotr) and [rnaReport](https://github.com/bioShaun/rnaReport) first.
`omplotr` is a R package needed for OMrnaseq to generate plots in analysis. `rnaReport` is needed for OMrnaseq to generate a report.


## Installation

Now you are in the virtualenv for the OMrnaseq, you can download the OMrnaseq source code from github and install it in the environment.

```bash

# download
git clone https://github.com/bioShaun/OMrnaseq.git

# install
cd OMrnaseq
pip install -e .

```

## Usage


### qc

```bash

mrna \
    -p /path/of/analysis \
    -s /path/of/sample_inf \
    -f /path/of/fastqs \
    -w parallels_number \
    fastqc

```

- sample_inf: tab-delimited text file indicating biological replicate relationships; see [example](example/example.sample_inf).
- fastqs: fastq files named format sample_1.clean.fq.gz, sample_2.clean.fq.gz.

### mapping

```bash
mrna \
    -p /path/of/analysis \
    -s /path/of/sample_inf \
    -f /path/of/fastqs \
    -w parallels_number \
    --star_index /path/to/star/index \
    mapping
	
```

### quant

```bash

mrna \
    -p /path/of/analysis \
    -s /path/of/sample_inf \
    -f /path/of/fastqs \
    -w parallels_number \
    --gene2tr /gene/transcript/map/file \
    --kallisto_idx /path/to/kallsito/index 

```

- gene2tr: file containing 'gene(tab)transcript' identifiers per line; see [example](example/example.gene2tr).

### enrich

```bash
mrna \
    -p /path/of/analysis \
    -w parallels_number \
    -n result_name \
    --go /go/annotation/file \
    --gene_length /gene/length/file \
    --kegg_blast /gene/blast/to/kegg/pep/tab/outfile \
    --kegg_abbr species_kegg_abbr \
    --kegg_background species_kegg_background_abbr \ # default is kegg abbr
    --gene_list_file /file/of/gene/list/path \
    enrich
```

- go: file containing 'gene(tab)go_ids' per line, go_ids are seperated with ","; see [example](example/example.go).
- gene_length: file containing 'gene(tab)gene_length' per line; see [example](example/example.gene_length).
- kegg_blast: blast result of gene with KOBAS pep sequence; see [example](example/example.kegg_blast).
- gene_list_file: file containing gene list file path. see [example](example/example.gene_list_file).

### rnaseq

rnaseq is a collection of module: qc, quant and enrich. So you could run three module in one command.

```bash
# run rnaseq
mrna \
    -p /path/of/analysis \
    -s /path/of/sample_inf \
    -f /path/of/fastqs \
    -w parallels_number \
    --gene2tr /gene/transcript/map/file \
    --kallisto_idx /path/to/kallsito/index \
    --go /go/annotation/file \
    --gene_length /gene/length/file \
    --kegg_blast /gene/blast/to/kegg/pep/tab/outfile \
    --kegg_abbr species_kegg_abbr \
    rnaseq

# you can also combine the module by yourself
mrna \
    ... # parameters required for each module
    module1 \
    module2

```
