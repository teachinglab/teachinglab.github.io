library(tidyverse)
library(webshot)

save_screenshot_report <- function(files_input_loc, files_output_loc) {
  all_files <- list.files(files_input_loc, full.names = T)
  
  all_files_png <- list.files(files_input_loc) |>
    stringr::str_replace_all("\\.html", "\\.png")
  
  purrr::walk2(all_files, all_files_png, ~ webshot(url = .x, 
                                                   file = paste0(here::here(files_output_loc), .y),
                                                   cliprect = "viewport",
                                                   vwidth = 1590,
                                                   vheight = 1632))
}

### This workflow needs fixing ###
#"~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/ANAs/Reports"
save_screenshot_report(files_input_loc = here::here("Reports/2022Reports/Final"),
                       files_output_loc = "Images/Reports/2021-2022/")
