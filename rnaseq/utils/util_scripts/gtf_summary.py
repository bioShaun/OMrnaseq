from HTSeq import GFF_Reader
import click
import pandas as pd
import os

CURRENT_DIR = os.getcwd()


@click.command()
@click.option('-g', '--gtf', type=click.Path(exists=True), required=True,
              help='gtf file for summarize.')
@click.option('-o', '--output_dir', type=click.Path(), default=CURRENT_DIR,
              help='output directory.')
def main(gtf, output_dir):
    # read gtf file
    gtf_dict = dict()
    for eachline in GFF_Reader(gtf):
        if eachline.type == 'exon':
            gene_id = eachline.attr['gene_id']
            chrom = eachline.iv.chrom
            start = eachline.iv.start + 1
            end = eachline.iv.end
            transcript_id = eachline.attr['transcript_id']
            exon_len = eachline.iv.end - eachline.iv.start
            if 'gene_biotype' in eachline.attr:
                gtf_dict.setdefault('gene_biotype', []).append(
                    eachline.attr['gene_biotype'])
            gtf_dict.setdefault('gene_id', []).append(gene_id)
            gtf_dict.setdefault('transcript_id', []).append(transcript_id)
            gtf_dict.setdefault('exon', []).append(exon_len)
            gtf_dict.setdefault('chr', []).append(chrom)
            gtf_dict.setdefault('start', []).append(start)
            gtf_dict.setdefault('end', []).append(end)
    gtf_df = pd.DataFrame(gtf_dict)

    # generate gtf summary
    gene_stat_df = gtf_df.loc[:, ['gene_id', 'transcript_id']]
    gene_stat_df = gene_stat_df.drop_duplicates()
    gene_stat = gene_stat_df.groupby(['gene_id'])['transcript_id']
    gene_num = len(gene_stat.count())
    tr_per_gene = gene_stat.count().mean()
    tr_num = len(gene_stat_df)
    tr_stat = gtf_df.groupby(['transcript_id'])['exon']
    single_exon = tr_stat.count().value_counts()[1]
    tr_length = tr_stat.sum().mean()
    exon_length = gtf_df.loc[:, 'exon'].mean()
    exon_num = tr_stat.count().mean()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    gtf_summary_file = os.path.join(output_dir, 'transcriptome.summary.txt')
    with open(gtf_summary_file, 'w') as gtf_summary_inf:
        gtf_summary_inf.write(
            'Gene number\t{gn}'.format(gn=gene_num))
        gtf_summary_inf.write(
            'Transcript per gene\t{tg:.2f}'.format(tg=tr_per_gene))
        gtf_summary_inf.write(
            'Transcript number\t{tn}'.format(tn=tr_num))
        gtf_summary_inf.write(
            'Single exon transcripts\t{st}'.format(st=single_exon))
        gtf_summary_inf.write(
            'Mean transcript length\t{tl:.2f}'.format(tl=tr_length))
        gtf_summary_inf.write(
            'Mean exon length\t{el:.2f}'.format(el=exon_length))
        gtf_summary_inf.write(
            'Exon number per transcript\t{et:.2f}'.format(et=exon_num))

    # generate transcript information
    tr_list = []
    tr_list.append(gtf_df.groupby(['transcript_id'])['chr'].unique())
    tr_list.append(gtf_df.groupby(['transcript_id'])['start'].min())
    tr_list.append(gtf_df.groupby(['transcript_id'])['end'].max())
    tr_list.append(gtf_df.groupby(['transcript_id'])['gene_id'].unique())
    tr_list.append(gtf_df.groupby(['transcript_id'])['exon'].count())
    tr_list.append(gtf_df.groupby(['transcript_id'])['exon'].sum())
    if 'gene_biotype' in gtf_df.columns:
        tr_list.append(gtf_df.groupby(['transcript_id'])['gene_biotype'].unique())
    tr_df = pd.concat(tr_list, axis=1)
    tr_df.loc[:, 'chr'] = map(','.join, tr_df.loc[:, 'chr'])
    tr_df.loc[:, 'gene_id'] = map(','.join, tr_df.loc[:, 'gene_id'])
    if 'gene_biotype' in tr_df.columns:
        tr_df.loc[:, 'gene_biotype'] = map(','.join, tr_df.loc[:, 'gene_biotype'])
    tr_file = os.path.join(output_dir, 'transcripts.detail.txt')
    tr_df.to_csv(tr_file, sep='\t')



if __name__ == '__main__':
    main()
