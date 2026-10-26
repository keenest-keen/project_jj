# перегонка ljsm-данных о постах (в .html-виде) в концентрированный информативный json
rm -R ../posts_json
python3 -m extractor.batch ../ljsm_data --cache ../posts_json
