#!/bin/bash
DIRECTORY=`dirname "$0"`
cd "$DIRECTORY"
Rscript -e '{if(system.file("",package="servr")==""){install.packages("servr",repos="https://cloud.r-project.org")};servr::httd(browser=TRUE)}'
