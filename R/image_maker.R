library(tidyverse)
library(webshot)

all_files <- list.files("~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/Mississippi/backup_reports", full.names = T)

all_files_png <- list.files("~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/Mississippi/backup_reports") %>% 
  stringr::str_replace_all(., "\\.html", "\\.png")
  
purrr::walk2(all_files, all_files_png, ~ webshot(url = .x, 
                                        file = paste0(here::here("Images/Reports/Mississippi/"), .y),
                                        cliprect = "viewport"))
