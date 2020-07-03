suppressMessages(library(ggplot2))
suppressMessages(library(argparser))
suppressMessages(library(omplotr))
suppressMessages(library(dplyr))
suppressMessages(library(gridExtra))
suppressMessages(library(scales))

options(stringsAsFactors = F)

p <- arg_parser("Plot snp plot")
p <- add_argument(
  p, '--snp_stats_dir',
  help = 'snp stats directory.')
argv <- parse_args(p)

# snp_stats_dir <- 'snp/'

palette_colors <- function(pal_name, sample_num) {
  col_pal_inf <- RColorBrewer::brewer.pal.info
  if (! pal_name %in% rownames(col_pal_inf)) {
    print('Palette for analysis:')
    print(rownames(col_pal_inf))
    stop('Wrong palette name!')
  }
  col_num <- col_pal_inf[pal_name, 'maxcolors']
  if (sample_num <= col_num) {
    return(RColorBrewer::brewer.pal(sample_num, pal_name))
  } else {
    return(colorRampPalette(RColorBrewer::brewer.pal(col_num, pal_name))(sample_num))
  }
}

blank_theme <- function(base_size = 14) {
  theme_minimal()+
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_blank(),
    panel.border = element_blank(),
    panel.grid=element_blank(),
    axis.ticks = element_blank(),
    plot.title=element_text(size=rel(1),
                            face="bold",
                            colour = 'grey30')
  )
}


snp_stats_dir <- argv$snp_stats_dir
out_prefix <- file.path(snp_stats_dir, 'var_plot')

prepare_plot_data <- function(var_file, filter_var=FALSE) {
  var_df <- read.delim(var_file)
  var_df$portion <- 100 * round(var_df$overall / sum(var_df$overall), 4)
  if (filter_var) {
    var_df <- filter(var_df, portion >= 0.05)
  }
  return(var_df)
}


var_pie_plot <- function(sample_var_stats, color_pal='Set2', 
                         title="", plot_type='pie') {
  type_num <- length(sample_var_stats$Type)
  type_color <- palette_colors(pal_name = color_pal,
                               sample_num = type_num)
  names(type_color) <- sample_var_stats$Type
  lg_label <- paste(sample_var_stats$Type,
                    ' (',
                    sample_var_stats$portion,
                    '%)', sep = '')
  names(lg_label) <- sample_var_stats$Type
  sample_var_stats <- arrange(sample_var_stats, desc(overall))
  sample_var_stats$Type <- factor(sample_var_stats$Type,
                                  levels = sample_var_stats$Type)
  if (plot_type == 'pie') {
    var_plot <- ggplot(sample_var_stats, aes(x = "", y=overall, fill = Type)) +
      geom_bar(width = 1, stat = "identity", color='white') +
      coord_polar("y", start = 0) +
      blank_theme() + theme(axis.text.x=element_blank()) +
      scale_fill_manual(values = type_color,
                        labels = lg_label) +
      guides(fill=guide_legend(title = '')) +
      ggtitle(title)   
  } else {
    var_plot <- ggplot(sample_var_stats, 
                       aes(x = Type, y=overall, fill = Type)) +
      geom_bar(stat = "identity", color='white',
               width = 0.6) +
      theme_onmath()    +
      scale_fill_manual(values = type_color,
                        labels = lg_label) +
      scale_y_log10() +
      guides(fill=guide_legend(title = '')) +
      theme(axis.text.x = element_blank(),
            plot.title=element_text(size=rel(1),
                                    face="bold",
                                    colour = 'grey30')) +
      xlab('') + ylab('Count') +
      ggtitle(title)
  }

  return(var_plot)
}

vartype_file <- file.path(snp_stats_dir, 'varType.txt')
vartype_df <- prepare_plot_data(vartype_file)
var_type_plot <- var_pie_plot(vartype_df, title='Variants by type')

var_region_file <- file.path(snp_stats_dir, 'varRegion.txt')
var_region_df <- prepare_plot_data(var_region_file, filter_var = T)
var_region_plot <- var_pie_plot(
  var_region_df, 
  color_pal = 'Dark2', 
  title='Variants by genomic region')


var_effect_file <- file.path(snp_stats_dir, 'varEffects.txt')
var_effect_df <- prepare_plot_data(var_effect_file, filter_var = T)
var_effect_plot <- var_pie_plot(
  var_effect_df, 
  color_pal = 'Set1', 
  title='Variants by effects',
  plot_type = 'bar')



merged_plot <- grid.arrange(var_type_plot, var_region_plot, var_effect_plot,
                            nrow = 2, layout_matrix = rbind(c(1,2), c(3, 3)))

save_ggplot(merged_plot, out_prefix,
            width = 12,
            height = 9)
