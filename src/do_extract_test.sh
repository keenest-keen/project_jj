rm -R ../cache_test
python3 -m extractor.batch ../data_test --cache ../cache_test
cp -rf ../cache_override/* ../cache_test/

# rm -R ../cache_prod
# python3 -m extractor.batch ../data_prod --cache ../cache_prod
# cp -rf ../cache_override/* ../cache_prod/