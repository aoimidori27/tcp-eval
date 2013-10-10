# tcp-eval

tcp-eval is Python-based framework to evaluate TCP flows. The framework consists of 3 parts

* **topology:** creates an arbitrary virtual network topology. The virtual network is based on XEN.
* **measurement:** contains different TCP measurements examples. Currently, only flowgrind measurement
  examples are available. In future there will be also some iperf and netperf examples are available.
* **analysis:** scripts to analyze the output of the different measurements scripts. The analysis
  scripts directly creates PDFs. 

The scripts are tested on Debian 7.0 (Wheezy) and Ubuntu 13.04.

## Install

* **Python packages** `sudo apt-get install python-simpleparse python-egenix-mxtexttools python-gnuplot \`
                      `python-pypdf python-mysqldb python-twisted python-scipy`
* **texlive packages** `sudo apt-get install texlive-font-utils texlive-latex-base texlive-latex-recommended \`
                       `texlive-science texlive-latex-extra`
