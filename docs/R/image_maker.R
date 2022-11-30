library(tidyverse)
library(webshot)

save_screenshot_report <- function(files_input_loc, files_output_loc, filetype = "html") {
  ### Get all files in folder ###
  all_files <- list.files(files_input_loc, full.names = T)
  
  ### Rename all files as png from pdf or html ###
  if (filetype == "html") {
    all_files_type <- list.files(files_input_loc) |>
      stringr::str_replace_all("\\.html", "\\.png")
  } else  if (filetype == "pdf") {
    all_files_type <- list.files(files_input_loc) |>
      stringr::str_replace_all("\\.pdf", "\\.png")
  }
  
  purrr::walk2(all_files, all_files_type, ~ webshot(url = .x, 
                                                   file = paste0(here::here(files_output_loc), .y),
                                                   cliprect = "viewport",
                                                   vwidth = 1590,
                                                   vheight = 1632))
}

### This workflow needs fixing ###
#"~/Teaching Lab/Coding/TeachingLab/Analysis/2021-2022/ANAs/Reports"
save_screenshot_report(files_input_loc = here::here("Reports/2023Reports/MidYear"),
                       files_output_loc = here::here("Images/Reports/2022-2023/MidYear/"),
                       filetype = "html")

