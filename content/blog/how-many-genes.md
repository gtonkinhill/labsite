---
title: How many gene annotations are there?
author: "Gerry Tonkin-Hill"
date: 2021-06-01
draft: false
---

[Grace Blackwell](https://scholar.google.com/citations?user=QhkA-dQAAAAJ&hl=en&oi=ao) recently gave a really interesting talk on her [work](https://www.biorxiv.org/content/10.1101/2021.03.02.433662v1.abstract) generating a standardised and curated database of 661,405 bacterial genome assemblies using read data retrieved from the European Nucleotide Archive (ENA).

This dataset is already proving to be very [useful](https://www.biorxiv.org/content/10.1101/2021.06.09.447586v1). Grace has plans to generate gene annotations for the assemblies but was still deciding on the best approach for doing this in a standardised way across the very diverse dataset. We have run into this issue previously when developing [panaroo](https://gtonkinhill.github.io/panaroo/#/). It is possible to force annotation algorithms like [prodigal](https://github.com/hyattpd/prodigal) to use the same annotation model for each assembly. This helps to prevent the scenario where the *exact* same nucleotide sequence is annotated differently in separate genome assemblies. While this generates more standardised annotations it could repeatedly generate the same errors so it is unclear whether this is a preferable approach to allowing the algorithm to adapt to each genome individually.

In discussing this after her talk the question of how many possible annotations there are in a typical bacterial genome came up. As I did not have any intuition for this I thought it would be worth taking a quick look. Conveniently, prodigal has an output option `-s` that lists all possible annotations (after some rough [filtering](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-11-119)).

Taking a random *S. pneumoniae*, *M. tuberculosis* and *K. pneumoniae* genome assembly from the sets we used in the panaroo paper I ran prodigal using the `-s` option on each. I also ran the program excluding genes with N's or that overlapped the ends of contigs to see how much impact these sources of error had.

```bash
for f in *.fasta
do
prefix=$(basename $f .fasta)
prodigal -i $f -o ${prefix}.gff -s ${prefix}_all.txt -f gff
prodigal -i $f -o ${prefix}_filt.gff -s ${prefix}_filt_all.txt -f gff -c -m 
done
```

We can then use a bit of python to count the number of annotations. I split this up to also count those that shared the same stop codon.

```python
import glob

counts = {}
for f in glob.glob('*_all.txt'):
  name = f.replace('_all.txt', '')
  annotations = []
  with open(f, 'r') as infile:
    for line in infile:
      if line[0] in ['#', 'B', '\n']: continue
      line = line.split()
      if line[2]=='-':
        annotations.append((line[0], '-'))
      else:
        annotations.append((line[1], '+'))
  counts[name] = [str(len(annotations)), str(len(set(annotations)))]
  with open(name + '.gff', 'r') as infile:
    count = 0
    for line in infile:
      if line[0]=='#': continue
      count += 1
  counts[name].append(str(count))

with open('annotation_counts.csv', 'w') as outfile:
  outfile.write('species,all,same_start,final\n')
  for name in counts:
    outfile.write(','.join([name]+list(counts[name])) + '\n')
```

We can then plot the final counts using ggplot

```r
library(ggplot2)
library(data.table)

counts <- fread("~/Downloads/annotation_counts.csv", data.table=FALSE)
counts$filtered <- ifelse(grepl('*filt', counts$species), 
                          'without closed ends', 'with closed ends')
counts$species <- gsub('_filt', '', counts$species)
plotdf <- melt(counts)
plotdf$species[grepl('k', plotdf$species)] <- 'K. pneumoniae'
plotdf$species[grepl('s', plotdf$species)] <- 'S. pneumoniae'
plotdf$species[grepl('tb', plotdf$species)] <- 'M. tuberculosis'

ggplot(plotdf, aes(x=species, y=value, fill=species)) + 
  geom_col() + 
  facet_grid(variable~filtered) +
  theme_minimal(base_size = 16) +
  scale_y_sqrt(labels = function(x) format(
    x, scientific = TRUE, digits=1, trim=TRUE),
                     breaks = c(0,1e4,1e5)) +
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank()) +
  xlab("") + ylab("annotation count")
```

{{< centeredImage src="/img/blog/how-many-genes/annotation_counts.png" alt="Annotation counts" >}}

Overall it looks like there are around an order of magnitude more potential stop sites than the final list of genes output by prodigal. If we instead include the number of possible start sides for each stop site we find a further order of magnitude increase in the number of possible annotations. This is quite large and underscores the challenge of automatic gene annotation and the potential for small algorithmic decisions to have large consequences.

The exact number of annotations including those that overlap with contig ends is given in the following table.

|Species  |    All| Same stop codon| Final|
|:--------:|:------:|:----------:|:-----:|
|*K. pneumoniae* | 234,325|      31,006|  5,791|
|*M. tuberculosis*     | 246,940|      45,640|  4,044|
|*S. pneumoniae* |  74,255|      17,242|  2,184|


Looking at the same table after excluding genes annotated at contig ends or across N's we see that this has a small but not insignificant impact. In fact, we have previously found that the accumulation of these differences over many genomes can lead to [large](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-020-02090-4) differences in pangenome inference.

|Species  |    All| Same stop codon| Final|
|:--------:|:------:|:----------:|:-----:|
|*K. pneumoniae* | 220,963|      30,463|  5,351|
|*M. tuberculosis*     | 244,993|      45,484|  4,047|
|*S. pneumoniae* |  73,552|      17,163|  2,147|


<!-- {{< gist "https://gist.github.com/gtonkinhill/59943ac73aa267900e63d07f1ba862de.js" >}} -->
