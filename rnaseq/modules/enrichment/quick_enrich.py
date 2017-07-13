#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare
from rnaseq.modules.base_module import simple_task
from rnaseq.modules.base_module import collection_task
import pandas as pd
import sys

script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
GOSEQ_R = os.path.join(script_dir, 'go_analysis.R')


class q_enrich_prepare_dir(prepare):
    _module = MODULE
    go = luigi.Parameter()
    topgo = luigi.Parameter()
    gene_length = luigi.Parameter()
    kegg = luigi.Parameter()
    sp = luigi.Parameter()
    kegg_bg = luigi.Parameter(default="")


@requires(q_enrich_prepare_dir)
class run_goseq(simple_task):

    _R = config.module_software['Rscript']
    _run_goseq_script = GOSEQ_R
    name = luigi.Parameter()
    genes = luigi.Parameter()
    _go_dir = config.module_dir[MODULE]['go']
    _module = MODULE

    def get_tag(self):
        return self.name


@requires(q_enrich_prepare_dir)
class run_kobas(simple_task):

    def get_tag(self):
        return self.name


@inherits(q_enrich_prepare_dir)
class q_enrich_collection(collection_task):
    _module = MODULE
    gene_files = luigi.Parameter()

    def requires(self):
        gene_files_df = pd.read_table(self.gene_files, header=None)
        if len(gene_files_df.columns) == 1:
            gene_files_df.columns = ['path']

            def get_name(x): return os.path.splitext(os.path.basename(x))[0]
            gene_files_df.loc[:, 'name'] = map(get_name, gene_files_df.path)
        elif len(gene_files_df.columns) == 2:
            gene_files_df.columns = ['name', 'path']
        else:
            print "Wrong gene list file format!"
            print "----------------------------"
            print "1. Two column file: tab seperated, first column is gene list name, second column is gene list path."
            print "2. Or one column file: gene list path (using gene list prefix as name)"
            print "----------------------------"
            sys.exit(1)
        return [run_goseq(go=self.go, topgo=self.topgo,
                          gene_length=self.gene_length, kegg=self.kegg,
                          sp=self.sp, proj_dir=self.proj_dir,
                          name=gene_files_df.name[each],
                          genes=gene_files_df.path[each]) for each in gene_files_df.index]


if __name__ == '__main__':
    luigi.run()
