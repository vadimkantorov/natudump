This is example of scraping public LegiFrance registry's naturalisation decrees for research purposes only. Code license is MIT.

```shell
pip install selenium charset_normalizer

mkdir -p jo
# python3 natudump.py -o jo --years $(seq 2000 2021) --output-directory-prefix "$(wslpath -a -w "$PWD")\\" # for WSL system, must be on a NTFS drive
python3   natudump.py -o jo --years $(seq 2000 2021) --output-directory-prefix "$PWD/"
ls jo | wc -l

mkdir -p txtjo
git clone --branch 20220524 --depth 1 https://github.com/pdfminer/pdfminer.six
PYTHONPATH="pdfminer.six:pdfminer.six/tools:$PYTHONPATH" find jo -name '*.pdf' -exec python3 -m pdf2txt {} -o txt{}.txt \;
ls txtjo | wc -l

python3 tabulate.py -i txtjo -o natufrance_2016_2021.tsv --section naturalisation
grep 'Russie\|URSS\|U.R.S.S' natufrance_2016_2021.tsv | wc -l
```
