library(tidyverse)
library(webshot)

all_files <- list.files("~/Downloads/2021-2022-tl-report_McNairy County, TN.html", full.names = T)

all_files_png <- list.files("~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/Mississippi/backup_reports") %>% 
  stringr::str_replace_all(., "\\.html", "\\.png")
  
purrr::walk2(all_files, all_files_png, ~ webshot(url = .x, 
                                        file = paste0(here::here("Images/Reports/Midyear/"), .y),
                                        cliprect = "viewport"))
