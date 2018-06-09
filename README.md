# OMrnaseq: a rnaseq pipeline based on luigi

-----

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

OMrnaseq is designed for RNAseq analysis. Including 5 major modules: fastqc, mapping, assembly, quant and enrich.
In addition, a QC module was added to OMrnaseq for generating a sequencing report.

### QC

QC module now supports fastq files sequenced from Annoroad.

```bash

# example1
# generate qc analysis result in current directory(cwd), and the report name is the name of cwd.
simple_qc -d /path/to/fastq/

# example2
# generate qc analysis result to specific path and use specific name.
simple_qc \
    -d /path/to/fastq/ \
    -n name_of_project \
    -p /path/of/analysis/result
```


