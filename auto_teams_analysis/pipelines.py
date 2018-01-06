# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# 需要更改的参数
current_season = '17t18'

import pymysql.cursors
import datetime
import json
import pdb

nowadays = datetime.datetime.now().strftime('%Y_%m_%d')
nowatime = datetime.datetime.now().strftime('%Y_%m_%d_%H%M')

class AutoTeamsAnalysisPipeline(object):
    def process_item(self, item, spider):
        if spider.name == 'auto_teams_analysis':
        # 这里写爬虫 odds_spider 的逻辑
            match_list = item['match_list']
            # 获取查询日期
            search_date = item['search_date']
            # Connect to the database
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
            print('连接至数据库' + db_name)
            try:
                with connection.cursor() as cursor:
                    tableName = 'teams_' + search_date  # 表名
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
                    # pdb.set_trace()
                    for single_match in match_list:
                        cursor.execute('SELECT match_id FROM %s WHERE match_id="%s"' % (tableName, single_match['match_id']))
                        table_row_len = len(cursor.fetchall())
                        print('analysis 表中存在查询数据的数目：:', table_row_len)
                        insert_sql = (
                                "INSERT INTO " + tableName + " VALUES "
                                                             "('%s', '%s', '%s', '%s', '%s', '%f', '%f','%d', '%s')"
                        )
                        try:
                            if table_row_len < 1:
                                print('insert数据库')
                                cursor.execute(insert_sql % (
                                    single_match['match_id'], single_match['match_name'], single_match['home_name'], single_match['away_name'],
                                    single_match['time_score'],
                                    single_match['home_rate'], single_match['away_rate'],
                                    single_match['average_completed_match'],
                                    single_match['support_direction']))
                            else:
                                update_sql = (
                                    'UPDATE %s SET time_score="%s",support_direction="%s" WHERE match_id="%s"'
                                )
                                print('update信息')
                                cursor.execute(update_sql % (
                                    tableName, single_match['time_score'], single_match['support_direction'], single_match['match_id']))
                        except Exception as e:
                            print("数据库执行失败 ", e)

                    # 从auto_teams_rate数据库中抓取最新比分替换auto_teams_analysis
                    # tableName = 'auto_teams_analysis.teams_' + search_date
                    # cursor.execute(
                    #     'SELECT match_id FROM %s' % tableName)
                    # for single_match_id in cursor.fetchall():
                    #     cursor.execute(
                    #         'SELECT match_id,time_score FROM %s WHERE match_id="%s"' % (tableName, single_match_id['match_id']))
                    #     cursor.fetchall()
                    #     pdb.set_trace()


                # connection is not autocommit by default. So you must commit to save your changes.
                cursor.close()
                if not connection.commit():
                    connection.rollback()

            finally:
                connection.close()

        return item
