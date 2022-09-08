```shell
pip install selenium charset_normalizer

mkdir -p jo
python3 natudump.py -o jo --years 2016 2017 2018 2019 2020 2021
ls jo | wc -l

mkdir -p jotxt
git clone --branch 20220524 --depth 1 https://github.com/pdfminer/pdfminer.six
for f in $(ls jo); do PYTHONPATH=$PWD/pdfminer.six:$PWD/pdfminer.six/tools:$PYTHONPATH python3 -m pdf2txt jo/$f > jotxt/$f.txt; done
ls jotxt | wc -l

python3 tabulate.py -i jotxt -o natu_2016_2021.txt
```
