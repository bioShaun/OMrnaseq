# 2016-10-18 for mRNA report reads qulity barplot
options(stringsAsFactors = F)
suppressMessages(library('omplotr'))
suppressMessages(library('plyr'))
suppressMessages(library('argparser'))
suppressMessages(library('dplyr'))

p <- arg_parser('reads quality plot')
p <- add_argument(p,'--rq_dir',help = 'reads quality directory.')
argv <- parse_args(parser = p)

file_path <- argv$rq_dir

all_files <- list.files(file_path)
qulity_data_files <- all_files[grep("*reads_quality.txt", all_files)]
qulity_data <- list()

for (i in 1:length(qulity_data_files)) {
  qulity_data[[i]] <- read.delim(paste(file_path, qulity_data_files[i], sep = "/"))
}
for (i in 1:length(qulity_data)) {
  qulity_data[[i]]$color <- ifelse(qulity_data[[i]]$Quality <= 30, "dodgerblue",
    "navy")
}

split_str <- function(strings, Split) {
  for (i in 1:nchar(strings)) {
    if (substr(strings, i, i) == Split) {
      return(c(substr(strings, 1, i - 1), substr(strings, i + 1, nchar(strings))))
    }
  }
}
for (i in 1:length(qulity_data)) {
  plot_title <- split_str(qulity_data_files[i], Split = ".")[1]
  qulity_data[[i]]$sample <- plot_title
  each_sample_out_name <- paste(plot_title, 'reads_quality.bar', sep = '.')
  each_sample_out_path <- file.path(file_path, each_sample_out_name)
  reads_quality_plot(qulity_data[[i]], each_sample_out_path)
}

qulity_data_df <- ldply(qulity_data, data.frame)
qulity_data_samples <- unique(qulity_data_df$sample)
selected_number <- ifelse(length(qulity_data_samples) < 9, length(qulity_data_samples), 9)
selected_df <- filter(qulity_data_df, sample %in% qulity_data_samples[1:selected_number])
selected_df$sample <- factor(selected_df$sample, levels = qulity_data_samples)
qulity_data_out <- file.path(file_path, 'reads_quality.bar.report')
reads_quality_plot(selected_df, qulity_data_out)
