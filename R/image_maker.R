library(tidyverse)
library(webshot)

save_screenshot_report <- function(files_input_loc, files_output_loc) {
  all_files <- list.files(files_input_loc, full.names = T)
  
  all_files_png <- list.files("~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/Mississippi/backup_reports") %>% 
    stringr::str_replace_all(., "\\.html", "\\.png")
  
  purrr::walk2(all_files, all_files_png, ~ webshot(url = .x, 
                                                   file = paste0(here::here(files_output_loc), .y),
                                                   cliprect = "viewport"))
}

save_screenshot_report(files_input_loc = "~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/Mid-Year Report/Mid-Year Report",
                       files_output_loc = "Images/Reports/Midyear/")