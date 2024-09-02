#!/usr/bin/env bash

### Read CLI input
bedfile=$1
### Rename output BED as tagged_*
tagged_bed="tagged_${bedfile}"

### Add annotation column
sed 's/$/\tTRUE/g' $bedfile > $tagged_bed
