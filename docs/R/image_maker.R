library(tidyverse)
library(webshot)

all_files <- list.files(here::here("2022Reports"), full.names = T)

all_files_png <- list.files(here::here("2022Reports")) %>% 
  stringr::str_replace_all(., "\\.html", "\\.png")
  
purrr::walk2(all_files, all_files_png, ~ webshot(url = .x, 
                                        file = paste0(here::here("Images/Reports/Midyear/"), .y),
                                        cliprect = "viewport"))