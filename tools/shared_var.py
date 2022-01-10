import json

with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")([0-9]+)"
    difficulty_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")"
plate_to_version = {
    '初': 'maimai',
    '真': 'maimai PLUS',
    '超': 'maimai GreeN',
    '檄': 'maimai GreeN PLUS',
    '橙': 'maimai ORANGE',
    '暁': 'maimai ORANGE PLUS',
    '晓': 'maimai ORANGE PLUS',
    '桃': 'maimai PiNK',
    '櫻': 'maimai PiNK PLUS',
    '樱': 'maimai PiNK PLUS',
    '紫': 'maimai MURASAKi',
    '菫': 'maimai MURASAKi PLUS',
    '堇': 'maimai MURASAKi PLUS',
    '白': 'maimai MiLK',
    '雪': 'MiLK PLUS',
    '輝': 'maimai FiNALE',
    '辉': 'maimai FiNALE',
    '熊': 'maimai でらっくす',
    # '華': 'maimai でらっくす PLUS',
    '華': 'maimai でらっくす',
    # '华': 'maimai でらっくす PLUS',
    '华': 'maimai でらっくす',
    '爽': 'maimai でらっくす Splash',
    # '煌': 'maimai でらっくす Splash PLUS',
    '煌': 'maimai でらっくす Splash',
}
achie_ranks = {'SSS+': 100.5, 'SSS': 100, 'SS+': 99.5, 'SS': 99, 'S+': 98, 'S': 97, 'AAA': 94,
               'AA': 90, 'A': 80, 'BBB': 75, 'BB': 70, 'B': 60, 'C': 50, 'D': 0}
combo_ranks = {"AP+": 0, "app": 0, "ap": 1, "AP": 1, "FC+": 2, "fcp": 2, "fc": 3, "FC": 3, "": 4}
combo_upper = {"fc": "FC", "fcp": "FC+", "ap": "AP", "app": "AP+", "": ""}
achie_ranks_regex = '(' + "|".join(achie_ranks.keys()) + ')?'
achie_ranks_regex = achie_ranks_regex.replace('+', '\+')
combo_ranks_regex = '(' + "|".join(combo_ranks.keys()) + ')?'
combo_ranks_regex = combo_ranks_regex.replace('+', '\+')
new_id_list = [10021, 10181, 10690, 11032, 11089, 11090, 11091, 11092, 11097, 11098, 11099, 11100, 11101,
               11102, 11103, 11105, 11107, 11108, 11109, 11110, 11111, 11113, 11114, 11115, 11125, 11126,
               11127, 11128, 11129, 11130, 11131, 11132, 11133, 11135, 11136, 11137, 11138, 11139, 11141,
               11142, 11143, 11146, 11147, 11148, 11149, 11150, 11152, 11153, 11154, 11155, 11157, 11158,
               11159, 11160, 11175, 11177, 11178, 11179, 11180, 11185, 11186, 11187, 11188, 11189, 11190,
               11191, 11192, 11193, 11194, 11195, 11199, 11200, 11206, 11214, 11215, 11216, 11217, 11221]
