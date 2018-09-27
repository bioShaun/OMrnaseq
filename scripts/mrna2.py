#!/usr/bin/env python

import luigi
import click
import os
import sys
from rnaseq.utils import config
from rnaseq.utils.util_functions import nohuprun_cmd, clean_logs
from rnaseq.utils.util_functions import MutuallyExclusiveOption
from rnaseq.utils.util_functions import pipe_default_para
from rnaseq.utils.util_functions import check_data
from rnaseq.modules.fastqc import fastqc
from rnaseq.modules.quantification import quant
from rnaseq.modules.mapping import star_mapping
from rnaseq.modules.enrichment import enrich
import itertools


CURRENT_DIR = os.getcwd()
DEFAULT_SAMPLE_INI = os.path.join(CURRENT_DIR, 'sample.ini')
DEFAULT_FQ_DIR = os.path.join(CURRENT_DIR, 'cleandata')


MODULE_PARAMS = {
    'fastqc': (),
    'quant': ('kallisto_idx', 'gene2tr')
}


def check_params(ctx, module):
    missing_params = []
    for each in MODULE_PARAMS[module]:
        if ctx.obj[each] is None:
            missing_params.append(each)
    return missing_params


def load_module(ctx):
    # define modules
    fastqc_missing_params = check_params(ctx, 'fastqc')
    if fastqc_missing_params:
        fastqc_module = fastqc_missing_params
    else:
        fastqc_module = fastqc.fastqc_results(
            proj_name=ctx.obj['proj_name'],
            clean_dir=ctx.obj['fq_dir'],
            sample_inf=ctx.obj['sample_inf'],
            proj_dir=ctx.obj['proj_dir'])

    quant_missing_params = check_params(ctx, 'quant')
    if quant_missing_params:
        quant_module = quant_missing_params
    else:
        quant_module = quant.quant_results(
            clean_dir=ctx.obj['fq_dir'],
            proj_name=ctx.obj['proj_name'],
            sample_inf=ctx.obj['sample_inf'],
            proj_dir=ctx.obj['proj_dir'],
            tr_index=ctx.obj['kallisto_idx'],
            gene2tr=ctx.obj['gene2tr'],
            contrasts=ctx.obj['contrasts']
        )

    # map modules to name
    module_dict = {
        'fastqc': [fastqc_module],
        'quant': [quant_module]
    }

    return module_dict


def launch_module(ctx, module_name):
    module_obj = ctx.obj['MODULE_DICT'][module_name]
    out_obj = []
    for each in module_obj:
        if isinstance(each, list):
            param_list = ['--{each}'.format(each=each)
                          for each in each]
            param_str = ','.join(param_list)
            out_obj.append('{mp} is needed for module {mn}'.format(
                mp=param_str, mn=module_name
            ))
        else:
            out_obj.append(each)
    return out_obj


@click.group(chain=True)
@click.option('-p',
              '--proj_dir',
              type=click.Path(exists=True),
              default=CURRENT_DIR,
              help='project analysis directory, default is current dir.')
@click.option('-n',
              '--proj_name',
              type=click.STRING,
              default='results',
              help='project name.')
@click.option('-s',
              '--sample_inf',
              type=click.Path(exists=True),
              default=DEFAULT_SAMPLE_INI,
              help='group vs sample file, default is "sample.ini"\
              in current directory.')
@click.option('-w',
              '--workers',
              default=4,
              type=int,
              help='paralle number.')
@click.option('-f',
              '--fq_dir',
              type=click.Path(exists=True),
              help='directory place analysis fq files, \
              default is "cleandata" in current dir.',
              default=None)
@click.option('--gene2tr',
              type=click.Path(exists=True, dir_okay=False),
              help='transcript_id <-> gene_id map file.\
              required for [quant] module.',
              default=None)
@click.option('--kallisto_idx',
              type=click.Path(exists=True, dir_okay=False),
              help='kallisto index for quantification.\
              required for [quant] module.')
@click.option('--contrasts',
              type=click.Path(dir_okay=False),
              help='compare list to perform diff analysis.',
              default='None')
@click.pass_context
def cli(ctx, proj_dir, sample_inf, fq_dir, workers,
        gene2tr, kallisto_idx, contrasts, proj_name):
    ctx.obj['proj_dir'] = proj_dir
    ctx.obj['proj_name'] = proj_name
    ctx.obj['sample_inf'] = sample_inf
    ctx.obj['fq_dir'] = fq_dir
    ctx.obj['workers'] = workers
    ctx.obj['gene2tr'] = gene2tr
    ctx.obj['kallisto_idx'] = kallisto_idx
    ctx.obj['contrasts'] = contrasts
    ctx.obj['MODULE_DICT'] = load_module(ctx)


@cli.resultcallback()
def process_pipeline(modules, proj_dir, sample_inf,
                     fq_dir, workers, gene2tr,
                     kallisto_idx, contrasts, proj_name):
    module_list = []
    param_list = []
    for each in itertools.chain.from_iterable(modules):
        if isinstance(each, str):
            param_list.append(each)
        else:
            module_list.append(each)
    if param_list:
        click.secho('=' * 60)
        for each_param in param_list:
            click.secho(each_param)
        click.secho('=' * 60)
        sys.exit('Paramters needed!')
    else:
        return luigi.build(module_list, workers=workers)


@cli.command('fastqc')
@click.pass_context
def qc(ctx):
    return launch_module(ctx, 'fastqc')


@cli.command('quant')
@click.pass_context
def quantification(ctx):
    return launch_module(ctx, 'quant')


if __name__ == '__main__':
    cli(obj={})
