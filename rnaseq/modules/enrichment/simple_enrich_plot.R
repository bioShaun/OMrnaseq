suppressMessages(library(ggplot2)) # plot
suppressMessages(library(ggthemes)) # plot theme
suppressMessages(library(argparser)) # read parameter
suppressMessages(library(tools)) # get file prefix and extension

p <- arg_parser("perform go analysis")
p <- add_argument(p, "--enrich_table", help = "enrich result table")
argv <- parse_args(p)

# for test
enrich_table <- 'up_genes.kegg.enrichment.txt'

# read parameters
enrich_table <- argv$enrich_table

# get file name, type and out_prefix
file_name <- basename(enrich_table)
file_path <- dirname(enrich_table)
file_prefix_path <- file_path_sans_ext(enrich_table)
enrich_type <- rev(strsplit(file_prefix_path, "\\.")[[1]])[2]

# max term name length
max_name_length <- 60

# clean data
enrich_data <- read.delim(file = enrich_table, sep = "\t", header = T, stringsAsFactors=F)
if (enrich_type == 'go') {
  enrich_data_plot <- enrich_data[, c('over_represented_pvalue', 'term', 'ontology')]
} else if (enrich_type == 'kegg') {
  enrich_data_plot <- enrich_data[, c('P.Value', 'X.Term', 'Database')]
}
colnames(enrich_data_plot) <- c('pvalue', 'term', 'ontology')
enrich_data_plot_filter <- enrich_data_plot[enrich_data_plot$pvalue < 0.05, ]
if (dim(enrich_data_plot_filter)[1] < 15) {
  enrich_data_plot_filter <- enrich_data_plot[1:15,]
}

enrich_data_plot_filter$logpvalue <- -log10(enrich_data_plot_filter$pvalue)

# trim too long term name
enrich_data_plot_filter$term.cut  <- ""
for(i in 1:dim(enrich_data_plot_filter)[1]){
  if(nchar(enrich_data_plot_filter$term[i]) > max_name_length){
    enrich_data_plot_filter$term.cut[i] <- paste0(substr(enrich_data_plot_filter$term[i],1,max_name_length/2),'...',
           substr(enrich_data_plot_filter$term[i],(nchar(enrich_data_plot_filter$term[i]) - max_name_length/2),nchar(enrich_data_plot_filter$term[i])))
  }else{
    enrich_data_plot_filter$term.cut[i] <- enrich_data_plot_filter$term[i]
  }
}

# set theme
enrich_theme <- theme_calc() +
  theme(
        axis.text.x = element_text(color = "black", face = "bold", angle = 90, hjust = 1, vjust = 0.5, size = rel(0.8)),
        axis.text.y = element_text(color = "black", face = "bold", size = rel(0.8)),
        axis.title.y = element_text(color = "black", face = "bold", size = rel(0.8))
        )
theme_set(enrich_theme)

# plot
p <- ggplot(data=enrich_data_plot_filter, aes(x=term.cut, y=logpvalue, fill = ontology)) +
  geom_bar(stat="identity",width = 0.75)+
  ylab("-log10(pvalue)") + xlab("") +
  scale_fill_brewer(palette="Set1") + guides(fill=F)

if (enrich_type == 'go') {
  p <- p + facet_grid(.~ontology, scales = "free_x", space="free")
}

# adjust output size according to term number
term_number <- dim(enrich_data_plot_filter)[1]
plot_width <- term_number/5 + 3
plot_heith <- term_number/8 + 3
ggsave(filename=paste(file_prefix_path, 'barplot.png', sep = '.'), type = 'cairo-png', plot = p, width = plot_width, height = plot_heith, dpi=300)
ggsave(filename=paste(file_prefix_path, 'barplot.pdf', sep = '.'), plot = p, width = plot_width, height = plot_heith)
