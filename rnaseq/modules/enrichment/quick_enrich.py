#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task, cp_analysis_result
import pandas as pd
import sys
import inspect

script_dir, script_name = os.path.split(os.path.abspath(__file__))
UTIL_DIR = os.path.dirname(inspect.getfile(config))
MODULE, _ = os.path.splitext(script_name)
GOSEQ_R = os.path.join(script_dir, 'go_analysis.R')
EXTRACT_INF_PY = os.path.join(
    UTIL_DIR, 'util_scripts', 'extract_info_by_id.py')
KEGG_PATHWAY_PY = os.path.join(script_dir, 'kegg_pathview.py')
TREAT_KEGG_OUT = os.path.join(script_dir, 'treat_kegg_table.py')
ENRICH_PLOT = os.path.join(script_dir, 'simple_enrich_plot.R')


class Pubvar:
    _module = MODULE


class q_enrich_prepare_dir(prepare, Pubvar):

    go = luigi.Parameter()
    gene_length = luigi.Parameter()
    kegg = luigi.Parameter()
    sp = luigi.Parameter()
    kegg_bg = luigi.Parameter(default="")


@requires(q_enrich_prepare_dir)
class run_goseq(simple_task, Pubvar):

    _run_goseq_script = GOSEQ_R
    name = luigi.Parameter()
    genes = luigi.Parameter()
    _go_dir = config.module_dir[MODULE]['go']
    _plot_enrich = ENRICH_PLOT

    def get_tag(self):
        return self.name


@requires(q_enrich_prepare_dir)
class run_kobas(simple_task, Pubvar):

    _extract_inf_py = EXTRACT_INF_PY
    _blast_dir = config.module_dir[MODULE]['blast']
    _kegg_dir = config.module_dir[MODULE]['kegg']
    _plot_enrich = ENRICH_PLOT
    _treat_table_py = TREAT_KEGG_OUT
    name = luigi.Parameter()
    genes = luigi.Parameter()

    def get_tag(self):
        return self.name


@inherits(q_enrich_prepare_dir)
class q_enrich_collection(collection_task, Pubvar):

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
        return [(run_goseq(go=self.go,
                           gene_length=self.gene_length, kegg=self.kegg,
                           sp=self.sp, proj_dir=self.proj_dir,
                           name=gene_files_df.name[each],
                           genes=gene_files_df.path[each]),
                 run_kobas(go=self.go, kegg_bg=self.kegg_bg,
                           gene_length=self.gene_length, kegg=self.kegg,
                           sp=self.sp, proj_dir=self.proj_dir,
                           name=gene_files_df.name[each],
                           genes=gene_files_df.path[each])
                 ) for each in gene_files_df.index]


@requires(q_enrich_collection)
class q_enrich_result(cp_analysis_result, Pubvar):

    proj_name = luigi.Parameter()
    _tag = 'cp_results_rename'
    main_dir = config.module_dir[Pubvar._module]['main']
    result_dir = None


if __name__ == '__main__':
    luigi.run()
