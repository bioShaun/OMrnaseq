#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task
import pandas as pd
import inspect
import itertools


script_dir, script_name = os.path.split(os.path.abspath(__file__))
UTIL_DIR = os.path.dirname(inspect.getfile(config))
MODULE, _ = os.path.splitext(script_name)
GOSEQ_R = os.path.join(script_dir, 'go_analysis.R')
EXTRACT_INF_PY = os.path.join(
    UTIL_DIR, 'util_scripts', 'extract_info_by_id.py')
KEGG_PATHWAY_PY = os.path.join(script_dir, 'kegg_pathview.py')
TREAT_KEGG_OUT = os.path.join(script_dir, 'treat_kegg_table.py')
ENRICH_PLOT = os.path.join(script_dir, 'enrich_barplot.R')


class enrich_prepare(prepare):
    _module = MODULE
    go = luigi.Parameter()
    topgo = luigi.Parameter()
    gene_length = luigi.Parameter()
    kegg = luigi.Parameter()
    sp = luigi.Parameter()
    kegg_bg = luigi.Parameter(default="")


@requires(enrich_prepare)
class run_goseq(simple_task):

    _run_goseq_script = GOSEQ_R
    compare = luigi.Parameter()
    reg = luigi.Parameter()
    genes = luigi.Parameter()
    _module = MODULE
    go_dir = config.module_dir[MODULE]['go']

    def get_tag(self):
        return '{t.compare}.{t.reg}'.format(t=self)


@requires(enrich_prepare)
class run_kobas(simple_task):

    _module = MODULE
    _extract_inf_py = EXTRACT_INF_PY
    _treat_table_py = TREAT_KEGG_OUT
    compare = luigi.Parameter()
    reg = luigi.Parameter()
    genes = luigi.Parameter()
    blast_dir = config.module_dir[MODULE]['blast']
    kegg_dir = config.module_dir[MODULE]['kegg']

    def get_tag(self):
        return '{t.compare}.{t.reg}'.format(t=self)


@requires(run_kobas)
class run_pathway(run_kobas):

    _module = MODULE
    _pathway_py = KEGG_PATHWAY_PY
    diff_dir = config.module_dir['quant']['diff']
    diff_sfx = config.file_suffix['diff_table']
    blast_dir = config.module_dir[MODULE]['blast']
    kegg_dir = config.module_dir[MODULE]['kegg']


@inherits(enrich_prepare)
class run_enrich_barplot(simple_task):

    _module = MODULE
    compare = luigi.Parameter()
    _enrich_plot = ENRICH_PLOT
    diff_dir = config.module_dir['quant']['diff']
    go_dir = config.module_dir[MODULE]['go']
    kegg_dir = config.module_dir[MODULE]['kegg']

    def requires(self):
        diff_dir = os.path.join(
            self.proj_dir, self.diff_dir
        )
        reg_list = ['ALL']
        reg_list.extend(['{g}-UP'.format(g=group)
                         for group in self.compare.split('_vs_')])
        diff_list_sfx = config.file_suffix['diff_list']
        diff_files = ['{_dir}/{t.compare}/{t.compare}.{r}.{sfx}'.format(
            _dir=diff_dir, t=self, r=reg, sfx=diff_list_sfx
        ) for reg in reg_list]
        return [(run_goseq(proj_dir=self.proj_dir, go=self.go,
                           topgo=self.topgo, gene_length=self.gene_length,
                           compare=self.compare, reg=r,
                           genes=diff_files[n], kegg=self.kegg,
                           sp=self.sp, kegg_bg=self.kegg_bg),
                 run_pathway(proj_dir=self.proj_dir, go=self.go,
                             topgo=self.topgo, gene_length=self.gene_length,
                             compare=self.compare, reg=r,
                             genes=diff_files[n], kegg=self.kegg,
                             sp=self.sp, kegg_bg=self.kegg_bg), )
                for n, r in enumerate(reg_list)]

    def get_tag(self):
        return self.compare


@inherits(enrich_prepare)
class enrich_collection(collection_task):

    _module = MODULE
    diff_dir = config.module_dir['quant']['diff']

    def requires(self):
        diff_dir = os.path.join(
            self.proj_dir, self.diff_dir
        )
        compare_name_list = os.listdir(diff_dir)
        return [run_enrich_barplot(proj_dir=self.proj_dir, go=self.go,
                                   topgo=self.topgo, kegg_bg=self.kegg_bg,
                                   gene_length=self.gene_length,
                                   kegg=self.kegg, sp=self.sp,
                                   compare=compare)
                for compare in compare_name_list]


if __name__ == '__main__':
    luigi.run()
