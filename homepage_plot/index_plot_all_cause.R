library(ggplot2)
library(plotly)
library(tidyverse)
library(ggthemes)
library(stringr)
library(scales)

disease.data <- read_csv("./IHME-GBD_2019_DATA-49614913-1.csv") %>%
  filter(metric_name=='Number') %>%
  filter(measure_name=="Deaths")

categories <- read_csv("./categories.csv")
disease.data$cause <- disease.data$cause_name
disease.data$category <- categories$category[match(disease.data$cause, categories$cause)]

disease.data$deaths <- disease.data$val
disease.data$Year <- as.integer(disease.data$year)

disease.data$cause[disease.data$cause=="Neoplasms"] = "Neoplasms including Cancer"

disease.data <- disease.data[,c('Year', 'cause', 'deaths', 'category')]%>% 
  arrange(cause, Year) %>% 
  group_by(cause)

colours <- c("#984ea3", "#e41a1c", "#4daf4a", "#377eb8")


gg <- ggplot(disease.data) +
  geom_point(aes(x = deaths, y = cause, color = category, size = deaths, frame = Year, groups = cause)) +
  theme_bw() +
  theme_tufte(base_size = 16) +
  scale_x_continuous(trans="sqrt", breaks=c(0, 5e6, 2e7), labels=c("0", "5 million", "20 million")) +
  scale_y_discrete(labels = function(x) str_wrap(x, width = 50)) +
  scale_colour_manual(values = colours) +
  theme(axis.text.y = element_text(size = 12))

# Convert ggplot object to a plotly object
p <- ggplotly(gg, tooltip = "none") %>%
  animation_opts(300, easing = "linear", redraw = FALSE) %>%
  animation_button(x = 1, xanchor = "right", y = 0.90, yanchor = "bottom", pad=list(t=0)) %>%
  animation_slider(hide = FALSE,
                   currentvalue = list(prefix = "YEAR ", font = list(color = "black")),
                   bgcolor = "#fffff8",
                   tickcolor = "#fffff8",
                   pad = list(t = 80)) %>%
  layout(showlegend = FALSE,
         xaxis = list(title = "Deaths"),
         yaxis = list(title = ""),
         font = list(size = 16),
         margin = list(pad=2)) %>%
  config(displayModeBar = FALSE) # Hide the mode bar

p

# Save the plotly object as an HTML file
htmlwidgets::saveWidget(p, '../static/plotly_animation.html', selfcontained = TRUE)

