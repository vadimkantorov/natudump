This is example of scraping public LegiFrance registry's naturalisation decrees for research purposes only (`naturalisation par mariage` is not included in these decrees). Code license is MIT.

```shell
pip install selenium charset_normalizer

mkdir -p jo
# python3 natudump.py -o jo --years $(seq 2000 2021) --output-directory-prefix "$(wslpath -a -w "$PWD")\\" # for WSL systems, must be on a NTFS drive
python3 natudump.py   -o jo --years $(seq 2000 2021) --output-directory-prefix "$PWD/"
ls jo | wc -l

mkdir -p txtjo
# https://github.com/pdfminer/pdfminer.six/issues/809
git clone --branch 20220524 --depth 1 https://github.com/pdfminer/pdfminer.six
PYTHONPATH="pdfminer.six:pdfminer.six/tools:$PYTHONPATH" find jo -name '*.pdf' -exec python3 -m pdf2txt {} -o txt{}.txt \;
ls txtjo | wc -l

python3 tabulate.py -i txtjo -o natufrance_2000_2021.tsv
grep 'Russie\|URSS\|U.R.S.S' natufrance_2000_2021.tsv | wc -l

mkdir -p catjo
git clone --branch v0.4 --depth 1 https://github.com/pmaupin/pdfrw
rm $(PYTHONPATH="$PWD/pdfrw:$PYTHONPATH" find jo/ -type f -not -exec python3 -c 'import sys, pdfrw; pdfrw.PdfReader(sys.argv[1])' {} \; -print)
for years in $(seq 2000 2021); do PYTHONPATH="$PWD/pdfrw:$PYTHONPATH" python3 pdfrw/examples/cat.py jo/JORF_${years}*; mv cat.JORF_${years}*.pdf catjo; done
ls catjo | wc -l

mkdir -p tarjo
for years in $(seq 2000 2021); do tar -cf tarjo/jo${years}.tar jo/*_${years}*; done
ls tarjo | wc -l
```
