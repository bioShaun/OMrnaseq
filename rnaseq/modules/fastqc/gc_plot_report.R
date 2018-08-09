#2017-03-01
options(warn = -1)
options(stringsAsFactors = F)
suppressMessages(require('tidyverse',quietly = T))
suppressMessages(require('reshape2',quietly = T))
suppressMessages(require('scales',quietly = T))
suppressMessages(require('argparser',quietly = T))
suppressMessages(require('dplyr', quietly = T))


script_dir <- dirname(rprojroot::thisfile())
lib_path = file.path(script_dir, '../../utils/RNAseq_plot_lib.R')
source(lib_path)

#----plot----
p <- arg_parser('gc plot')
p <- add_argument(p,'--gc_dir',help = 'gc stats')
argv <- parse_args(parser = p)

# for test
# source('myproj/OMrnaseq/rnaseq/utils//RNAseq_plot_lib.R')
# gc_dir <- 'myproj/ngs_report/fake_report/fastqc/gc_plot/'
# out_dir <- gc_dir

# read parameters
gc_dir <- argv$gc_dir

all_files <- list.files(gc_dir)
gc_files <- all_files[grep("*gc.txt", all_files)]


split_str <- function(strings, Split) {
  for (i in 1:nchar(strings)) {
    if (substr(strings, i, i) == Split) {
      return(c(substr(strings, 1, i - 1), substr(strings, i + 1, nchar(strings))))
    }
  }
}


#file.exists(gc_files)
gc_file_list <- list()
for (i in seq(length(gc_files))) {
  each_sample_gc_df <- read.delim(paste(gc_dir, gc_files[i], sep='/'))
  sample_id <- split_str(gc_files[i], Split='.')[1]
  each_sample_gc_df[,2:dim(each_sample_gc_df)[2]] <- each_sample_gc_df[,2:dim(each_sample_gc_df)[2]] / 100
  each_sample_gc_df$sample <- sample_id
  each_sample_gc_df[is.na(each_sample_gc_df)] <- 0
  gc_file_list[[i]] <- each_sample_gc_df
  each_sample_out_name <- paste(sample_id, 'gc_distribution.line', sep = '.')
  each_sample_out_path <- file.path(gc_dir, each_sample_out_name)
  rs_each_sample_gc_df <- melt(each_sample_gc_df,id=c('X.Base', 'sample'))
  gc_line_plot(rs_each_sample_gc_df, each_sample_out_path)
}
gc_file_df <- ldply(gc_file_list, data.frame)
rs_gc_file_df <- melt(gc_file_df,id=c('X.Base', 'sample'))

samples <- unique(rs_gc_file_df$sample)
sample_number <- length(samples)
selected_num <- ifelse(sample_number < 9, sample_number, 9)
selected_df <- filter(rs_gc_file_df, sample %in% samples[1:selected_num])
gc_plot_out <- file.path(gc_dir, 'gc_distribution.line.report')
selected_df$sample <- factor(selected_df$sample, levels = samples)
gc_line_plot(selected_df, gc_plot_out)
