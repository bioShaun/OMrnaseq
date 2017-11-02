import click
from Bio import SeqIO, bgzf
import re
import os


def exract_diff_seq(diff_genes, fasta):
    gene_dict = {each.strip(): 1 for each in open(diff_genes)}
    seq_list = []
    for seq_record in SeqIO.parse(fasta, "fasta"):
        gene_id = re.search('gene=(\S+)', seq_record.description).groups()[0]
        if gene_id in gene_dict:
            seq_list.append(seq_record)

    d_path, d_name = os.path.split(os.path.abspath(diff_genes))
    d_prefix = os.path.splitext(d_name)[0]
    d_fa_path = os.path.join(d_path, '{p}.fa.gz'.format(p=d_prefix))
    with bgzf.BgzfWriter(d_fa_path, "wb") as outgz:
        SeqIO.write(sequences=seq_list, handle=outgz, format="fasta")


@click.command()
@click.option('-f', '--fasta', type=click.Path(exists=True),
              required=True, help='transcript fasta file.')
@click.option('-d', '--diff_dir', type=click.Path(exists=True),
              required=True, help='diff gene list file.')
@click.option('-c', '--compare', type=click.STRING, required=True,
              help='compare name.')
def main(diff_dir, fasta, compare):
    reg_list = ['{e}-UP'.format(e=each) for each in compare.split('_vs_')]
    reg_list.append('ALL')
    for each_reg in reg_list:
        diff_name = '{c}.{r}.edgeR.DE_results.diffgenes.txt'.format(
            c=compare, r=each_reg)
        each_diff_genes = os.path.join(
            diff_dir, compare, diff_name)
        exract_diff_seq(each_diff_genes, fasta)


if __name__ == '__main__':
    main()
