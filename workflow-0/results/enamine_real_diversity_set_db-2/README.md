# Raw Data Compression

GitHub does not allow for files > 100MB. 

* On Frontera's headnode, archive, compress, split, commit to github raw data with:

  ```
  tar -cjf - <receptor>/* | split -b 40M - "<receptor>.tar.bz2.part."
  git add <receptor>.tar.bz2.part.*
  git commit -m '<message>'
  git pull
  git push
  ```

* On the machine where to analyze the data, get, join, unarchive and uncpress the raw data with:
  ```
  git pull
  cat <receptor>.tar.bz2.part.* > <receptor>.tar.bz2
  tar xfj <receptor.tar.bz2
  ```

