# -*- coding: utf-8 -*-
# import os
import scrapy
import pdb
import datetime, time
import re
import json
from lxml import etree
import requests
import pymysql.cursors


match_name_dict = {
    'SPA CUP': '西杯',
    'SPA D1': '西甲',
    'SPA D2': '西乙',
    'GER D1': '德甲',
    'GER D2': '德乙',
    'ENG PR': '英超',
    'ENG LCH': '英冠',
    'ENG FAC': '英足总杯',
    'ITA D1': '意甲',
    'ITA D2': '意乙',
    'FRA D1': '法甲',
    'FRA D2': '法乙',
    'FRAC': '法国杯',
    'POR D1': '葡超',
    'SCO PR': '苏超',
    'SCO CH': '苏冠',
    'HOL D1': '荷甲',
    'HOL D2': '荷乙',
    'SWE D1': '瑞典超',
    'FIN D1': '芬兰超',
    'NOR D1': '挪超',
    'DEN D1': '丹麦超',
    'AUT D1': '奥地利超',
    'SUI Sl': '瑞士超',
    'IRE PR': '爱尔兰超',
    'RUS PR': '俄超',
    'POL D1': '波兰超',
    'BEL D1': '比甲',
    'BEL D2': '比乙',
    'AUS D1': '澳超',
    'GRE D1': '希腊超',
    'ICE PR': '冰岛超',
    'TUR D1': '土超',
    'ISL': '印度超',
    'IND D1': '印度甲',
    'BGD D1': '孟加拉超',
    # 'EGY D1': '埃及超',
    # 'INT CF': '国际友谊',
}

current_hour = time.localtime()[3]  # 获取当前的小时数，如果小于8则应该选择yesterday
nowadays = datetime.datetime.now().strftime("%Y-%m-%d")  # 获取当前日期 格式2018-01-01
yesterdy = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")  # 获取昨天日期
if current_hour < 8:    # 默认在早上八点前拉取昨天页面
    search_date = yesterdy
else:
    search_date = nowadays

completed_match_list = []

# 比赛列表 item
class match_list_Item(scrapy.Item):
    match_list = scrapy.Field()  # 已经计算得到的比赛list
    search_date = scrapy.Field()  # search_date 用来建表

class OddSpider(scrapy.Spider):
    name = 'auto_teams_analysis'
    allowed_domains = ['http://info.livescore123.com/']

    # 包装url
    start_urls = []
    url = 'http://info.livescore123.com/1x2/company.aspx?id=177&company=PinnacleSports'
    start_urls.append(url)

    # Connect to the database
    # 去拿取已经获得首发率的match_id放入列表中，不去服务器拉取该比赛球员数据
    db_name = 'auto_teams_rate'
    config = {
        'host': '127.0.0.1',
        'user': 'root',
        'password': '19940929',
        'db': db_name,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    connection = pymysql.connect(**config)
    print('连接至数据库:' + db_name)
    try:
        with connection.cursor() as cursor:
            # 设置当前表名
            tableName = 'teams_' + search_date.replace('-', '_')  # 当前查询日期为表名
            cursor.execute('SELECT * FROM %s WHERE home_rate>0 and away_rate>0' % tableName)
            for match in cursor.fetchall():
                single_match = {}
                single_match['match_id'] = match['match_id']
                single_match['match_name'] = match['match_name']
                single_match['time_score'] = match['time_score']
                single_match['home_name'] = match['home_name']
                single_match['away_name'] = match['away_name']
                single_match['home_rate'] = match['home_rate']
                single_match['away_rate'] = match['away_rate']
                single_match['average_completed_match'] = match['average_completed_match']
                completed_match_list.append(single_match)
            # connection is not autocommit by default. So you must commit to save your changes.
            cursor.close()
    finally:
        connection.close()

    # Connect to the database
    # 去拿取已经获得首发率的match_id放入列表中，不去服务器拉取该比赛球员数据
    db_name = 'auto_teams_analysis'
    config = {
        'host': '127.0.0.1',
        'user': 'root',
        'password': '19940929',
        'db': db_name,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    connection = pymysql.connect(**config)
    print('连接至数据库:' + db_name)
    try:
        with connection.cursor() as cursor:
            # 设置当前表名
            tableName = 'teams_' + search_date.replace('-', '_')  # 当前查询日期为表名
            # 建立当前队伍表
            build_table = (
                "CREATE TABLE IF NOT EXISTS "' %s '""
                "(match_id VARCHAR(20) NOT NULL PRIMARY KEY,"
                "match_name VARCHAR(50) NOT NULL,"
                "home_name VARCHAR(50) NOT NULL,"
                "away_name VARCHAR(50) NOT NULL,"
                "time_score VARCHAR(50) NOT NULL,"
                "home_rate FLOAT(8) NOT NULL,"
                "away_rate FLOAT(8) NOT NULL,"
                "average_completed_match INT(8) NOT NULL,"
                "support_direction VARCHAR(50) NOT NULL)"
            )
            cursor.execute(build_table % tableName)
            # 建表完成
            # connection is not autocommit by default. So you must commit to save your changes.
            cursor.close()
    finally:
        connection.close()
    print("已经获得首发的比赛列表:", completed_match_list)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url)

    # 分析每行信息
    def parse(self, response):
        odd_match_list = []
        need_step = False   # 标志是否要跳过
        for tr in response.xpath('//table[contains(@class,"schedule")]').xpath('tr'):
            # 如果没有tr_id说明是头部或者需要跳过则 跳过
            if len(tr.xpath('@id')) == 0 or need_step:
                need_step = False
                continue
            tr_id = tr.xpath('@id').extract()[0]
            # 如果下面成立说明是最新赔率行
            if tr_id.split('_')[0].split('tr')[-1] != '':
                single_match_tr_index = 2
            else:
                single_match_tr_index = 1
            if single_match_tr_index == 1:
                if len(tr.xpath('td')[0].xpath('text()').extract()) == 0:
                    need_step = True
                    continue
                league_name = tr.xpath('td')[0].xpath('text()').extract()[0]    # 联赛名称，是英文，需要用字典转为中文
                # 如果不在要获取的联赛列表中就跳过,要调过两个tr
                if not league_name in match_name_dict.keys():
                    need_step = True
                    continue
                start_time_year = int(tr.xpath('td')[1].xpath('script/text()').extract()[0].replace('showtime(', '').replace(')', '').split(',')[0])
                start_time_month = int(tr.xpath('td')[1].xpath('script/text()').extract()[0].replace('showtime(', '').replace(')', '').split(',')[1].split('-')[0])
                start_time_day = int(tr.xpath('td')[1].xpath('script/text()').extract()[0].replace('showtime(', '').replace(')', '').split(',')[2])
                start_time_hour = int(tr.xpath('td')[1].xpath('script/text()').extract()[0].replace('showtime(', '').replace(')', '').split(',')[3])
                start_time_minu = int(tr.xpath('td')[1].xpath('script/text()').extract()[0].replace('showtime(', '').replace(')', '').split(',')[4])
                start_time = datetime.datetime(start_time_year, start_time_month, start_time_day, start_time_hour, start_time_minu) + datetime.timedelta(hours=8)
                start_mktime = time.mktime(start_time.timetuple())
                now_mktime = time.time()
                # 如果当前时间比开始时间小-3600s,则结束遍历，不再往下查找
                if (now_mktime-start_mktime) < -3600:
                    break
                start_time_text = start_time.strftime('%Y-%m-%d %H:%M')
                home_name = tr.xpath('td')[2].xpath('a/text()').extract()[0]
                away_name = tr.xpath('td')[10].xpath('a/text()').extract()[0]
                home_original_odd = tr.xpath('td')[3].xpath('text()').extract()[0]
                draw_original_odd = tr.xpath('td')[4].xpath('text()').extract()[0]
                away_original_odd = tr.xpath('td')[5].xpath('text()').extract()[0]
                home_original_probability = tr.xpath('td')[6].xpath('text()').extract()[0]
                draw_original_probability = tr.xpath('td')[7].xpath('text()').extract()[0]
                away_original_probability = tr.xpath('td')[8].xpath('text()').extract()[0]
                original_payBack_rate = tr.xpath('td')[9].xpath('text()').extract()[0]
                single_match_dict = {}
                single_match_dict['league_name'] = match_name_dict[league_name]
                single_match_dict['start_time_text'] = start_time_text
                single_match_dict['home_name'] = home_name
                single_match_dict['away_name'] = away_name
                single_match_dict['home_original_odd'] = float(home_original_odd)
                single_match_dict['draw_original_odd'] = float(draw_original_odd)
                single_match_dict['away_original_odd'] = float(away_original_odd)
                single_match_dict['home_original_probability'] = round(float(home_original_probability.replace('%', ''))/100, 3)
                single_match_dict['draw_original_probability'] = round(float(draw_original_probability.replace('%', ''))/100, 3)
                single_match_dict['away_original_probability'] = round(float(away_original_probability.replace('%', ''))/100, 3)
                single_match_dict['original_payBack_rate'] = round(float(original_payBack_rate.replace('%', ''))/100, 3)
                odd_match_list.append(single_match_dict)
            else:
                match_index = len(odd_match_list)-1
                if len(tr.xpath('td')[0].xpath('text()').extract()) != 0:
                    try:
                        home_now_odd = tr.xpath('td')[0].xpath('text()').extract()[0]
                        draw_now_odd = tr.xpath('td')[1].xpath('text()').extract()[0]
                        away_now_odd = tr.xpath('td')[2].xpath('text()').extract()[0]
                        home_now_probability = tr.xpath('td')[3].xpath('text()').extract()[0]
                        draw_now_probability = tr.xpath('td')[4].xpath('text()').extract()[0]
                        away_now_probability = tr.xpath('td')[5].xpath('text()').extract()[0]
                        now_payBack_rate = tr.xpath('td')[6].xpath('text()').extract()[0]
                    except:
                        print('home_name:',odd_match_list[-1]['home_name'])
                        pdb.set_trace()

                    odd_match_list[match_index]['home_now_odd'] = float(home_now_odd)
                    odd_match_list[match_index]['draw_now_odd'] = float(draw_now_odd)
                    odd_match_list[match_index]['away_now_odd'] = float(away_now_odd)
                    odd_match_list[match_index]['home_now_probability'] = round(
                        float(home_now_probability.replace('%', '')) / 100, 3)
                    odd_match_list[match_index]['draw_now_probability'] = round(
                        float(draw_now_probability.replace('%', '')) / 100, 3)
                    odd_match_list[match_index]['away_now_probability'] = round(
                        float(away_now_probability.replace('%', '')) / 100, 3)
                    odd_match_list[match_index]['now_payBack_rate'] = round(
                        float(now_payBack_rate.replace('%', '')) / 100, 3)
                else:
                    home_now_odd = odd_match_list[match_index]['home_original_odd']
                    draw_now_odd = odd_match_list[match_index]['draw_original_odd']
                    away_now_odd = odd_match_list[match_index]['away_original_odd']
                    home_now_probability = odd_match_list[match_index]['home_original_probability']
                    draw_now_probability = odd_match_list[match_index]['draw_original_probability']
                    away_now_probability = odd_match_list[match_index]['away_original_probability']
                    now_payBack_rate = odd_match_list[match_index]['original_payBack_rate']
                    odd_match_list[match_index]['home_now_odd'] = home_now_odd
                    odd_match_list[match_index]['draw_now_odd'] = draw_now_odd
                    odd_match_list[match_index]['away_now_odd'] = away_now_odd
                    odd_match_list[match_index]['home_now_probability'] = home_now_probability
                    odd_match_list[match_index]['draw_now_probability'] = draw_now_probability
                    odd_match_list[match_index]['away_now_probability'] = away_now_probability
                    odd_match_list[match_index]['now_payBack_rate'] = now_payBack_rate

        # 打开chinese2english, 将之前保存的首发信息中的名称转换为英文再与当前odd列表中的信息进行模糊匹配找出那场比赛，进行计算
        with open('auto_teams_analysis/chinese2english.json', 'r', encoding='utf-8') as json_file:
            chinese2english = json.load(json_file)

        match_info_list = []    # 存取所有已经可以得到结果的比赛信息list
        for single_match in completed_match_list:
            match_id = single_match['match_id']
            match_name = single_match['match_name']
            time_score = single_match['time_score']
            average_completed_match = single_match['average_completed_match']
            if single_match['home_name'] in chinese2english.keys():
                home_name = chinese2english[single_match['home_name']]['name']
            else:
                home_name = single_match['home_name']
            if single_match['away_name'] in chinese2english.keys():
                away_name = chinese2english[single_match['away_name']]['name']
            else:
                away_name = single_match['away_name']
            home_rate = single_match['home_rate']
            away_rate = single_match['away_rate']

            # 查找对应的比赛
            try:
                patten_home_name_1 = home_name[0:3] + '.*?'
                regex_home_name_1 = re.compile(patten_home_name_1)
                patten_home_name_2 = home_name[-3:] + '.*?'
                regex_home_name_2 = re.compile(patten_home_name_2)
                patten_away_name_1 = away_name[0:3] + '.*?'
                regex_away_name_1 = re.compile(patten_away_name_1)
                patten_away_name_2 = away_name[-3:] + '.*?'
                regex_away_name_2 = re.compile(patten_away_name_2)
            except:
                pdb.set_trace()
            odd_home_name_list = [item['home_name'] for item in odd_match_list]
            odd_away_name_list = [item['away_name'] for item in odd_match_list]
            # pdb.set_trace()
            home_name_count = 0
            home_name_count_list = []
            for odd_home_name in odd_home_name_list:
                match_1 = regex_home_name_1.search(odd_home_name)
                match_2 = regex_home_name_2.search(odd_home_name)
                if match_1 or match_2:
                    # 如果前或者后匹配到一个就将其count添加到列表中与away比较，取相同的count
                    home_name_count_list.append(home_name_count)
                home_name_count += 1
            away_name_count = 0
            away_name_count_list = []
            for odd_away_name in odd_away_name_list:
                match_1 = regex_away_name_1.search(odd_away_name)
                match_2 = regex_away_name_2.search(odd_away_name)
                if match_1 or match_2:
                    # 如果前或者后匹配到一个就将其count添加到列表中与home比较，取相同的count
                    away_name_count_list.append(away_name_count)
                away_name_count += 1
            has_found = False
            fount_index = 0     # 本场比赛在odd_match_list中的index
            for home_count in home_name_count_list:
                for away_count in home_name_count_list:
                    if home_count == away_count:
                        # 如果找到相同的count就说明是这场比赛开始计算，否则continue
                        has_found = True
                        fount_index = home_count
            if not has_found:
                continue

            # 开始计算
            # 先检测是否已经存在首发，如果没有就跳过
            support_direction = ''
            if home_rate > 0 and away_rate > 0:
                if round(abs(home_rate - away_rate), 2) >= 0.25:
                    if home_rate > away_rate:
                        support_direction = '主队88%不败(1.15),77%取胜(1.3)'
                    else:
                        support_direction = '客队88%不败(1.15),77%取胜(1.3)'
                elif round(abs(home_rate - away_rate), 2) >= 0.10:
                    big_probability_direction = ''  # 1 表示主队是大概率方向，-1表示客队是大概率方向
                    if odd_match_list[fount_index]['home_now_probability'] > odd_match_list[fount_index]['away_now_probability']:
                        big_probability_direction = 1
                    else:
                        big_probability_direction = -1

                    home_probability_change = odd_match_list[fount_index]['home_now_probability'] - odd_match_list[fount_index]['home_original_probability']    # 主胜初盘到目前变化的概率
                    away_probability_change = odd_match_list[fount_index]['away_now_probability'] - odd_match_list[fount_index]['away_original_probability']    # 客胜初盘到目前变化的概率

                    change_limit = 0.027    # 限制的概率变化
                    # 只分析相同联赛的球队
                    if home_rate > away_rate:
                    # 主队首发率大于客队首发率
                        if big_probability_direction == 1:
                            if home_probability_change >= change_limit:
                                support_direction = '主队77%取胜(1.3),88%不败（1.15)'
                            elif home_probability_change <= -change_limit:
                                support_direction = '客队77%不败(1.3),下半场前及时对冲'
                            else:
                            # 没有达到限制的概率变化
                                if odd_match_list[fount_index]['home_now_probability'] > 0.85:
                                    support_direction = '主队66%胜两球(1.5),77%取胜(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.55:
                                    support_direction = '主队66%取胜(1.5),77%不败(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.30:
                                    support_direction = '主队66%不败(1.5),77%最多输一球(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.14:
                                    support_direction = '主队66%最多输一球(1.5),77%最多输两球(1.3)'
                        elif big_probability_direction == -1:
                            if away_probability_change >= change_limit:
                                support_direction = '客队77%不败(1.3),下半场前及时对冲'
                            elif away_probability_change <= -change_limit:
                                support_direction = '主队77%取胜(1.3),88%不败（1.15)'
                            else:
                                # 没有达到限制的概率变化
                                if odd_match_list[fount_index]['home_now_probability'] > 0.85:
                                    support_direction = '主队66%胜两球(1.5),77%取胜(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.55:
                                    support_direction = '主队66%取胜(1.5),77%不败(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.30:
                                    support_direction = '主队66%不败(1.5),77%最多输一球(1.3)'
                                elif odd_match_list[fount_index]['home_now_probability'] > 0.14:
                                    support_direction = '主队66%最多输一球(1.5),77%最多输两球(1.3)'
                    else:
                    # 客队首发率大于主队首发率
                        if big_probability_direction == -1:
                            if away_probability_change >= change_limit:
                                support_direction = '客队77%取胜(1.3),88%不败（1.15)'
                            elif away_probability_change <= -change_limit:
                                support_direction = '主队77%不败(1.3),下半场前及时对冲'
                            else:
                            # 没有达到限制的概率变化
                                if odd_match_list[fount_index]['away_now_probability'] > 0.85:
                                    support_direction = '客队66%胜两球(1.5),77%取胜(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.55:
                                    support_direction = '客队66%取胜(1.5),77%不败(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.30:
                                    support_direction = '客队66%不败(1.5),77%最多输一球(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.14:
                                    support_direction = '客队66%最多输一球(1.5),77%最多输两球(1.3)'
                        elif big_probability_direction == 1:
                            if home_probability_change >= change_limit:
                                support_direction = '主队77%不败(1.3),下半场前及时对冲'
                            elif home_probability_change <= -change_limit:
                                support_direction = '客队77%取胜(1.3),88%不败（1.15)'
                            else:
                                # 没有达到限制的概率变化
                                if odd_match_list[fount_index]['away_now_probability'] > 0.85:
                                    support_direction = '客队66%胜两球(1.5),77%取胜(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.55:
                                    support_direction = '客队66%取胜(1.5),77%不败(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.30:
                                    support_direction = '客队66%不败(1.5),77%最多输一球(1.3)'
                                elif odd_match_list[fount_index]['away_now_probability'] > 0.14:
                                    support_direction = '客队66%最多输一球(1.5),77%最多输两球(1.3)'
                single_match_item = {}
                single_match_item['match_id'] = match_id
                single_match_item['match_name'] = match_name
                single_match_item['time_score'] = time_score
                single_match_item['average_completed_match'] = average_completed_match
                single_match_item['home_name'] = home_name
                single_match_item['away_name'] = away_name
                single_match_item['home_rate'] = home_rate
                single_match_item['away_rate'] = away_rate
                single_match_item['support_direction'] = support_direction
                match_info_list.append(single_match_item)
            else:
                continue
        all_match_Item = match_list_Item()
        all_match_Item['match_list'] = match_info_list
        all_match_Item['search_date'] = search_date.replace('-', '_')

        yield all_match_Item











