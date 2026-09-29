rm -R ../blog
cd ./generator

# тестовый прогон
python3 main.py --json-dir ../../cache_test -v

# продакшн-прогон
# python3 main.py --json-dir ../../cache_prod --output-dir ../../blog -v

# всё, включая private/friends
# python3 main.py --json-dir ../../cache_test --output-dir ../../blog --private -v