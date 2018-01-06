import pymysql.cursors
import datetime
import json
import pdb

search_date = '2018_01_06'

# 从auto_teams_rate数据库中抓取最新比分替换auto_teams_analysis
# Connect to the database
analysis_db_name = 'auto_teams_analysis'
analysis_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '19940929',
    'db': analysis_db_name,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
connection = pymysql.connect(**analysis_config)
print('连接至数据库' + analysis_db_name)
try:
    with connection.cursor() as cursor:
        tableName = 'teams_' + search_date
        cursor.execute(
            'SELECT match_id FROM %s' % tableName)
        analysis_match_list = cursor.fetchall()

    # connection is not autocommit by default. So you must commit to save your changes.
    cursor.close()
    if not connection.commit():
        connection.rollback()

finally:
    connection.close()

rate_db_name = 'auto_teams_rate'
rate_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '19940929',
    'db': rate_db_name,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
connection = pymysql.connect(**rate_config)
print('连接至数据库' + rate_db_name)
update_match_list = []
try:
    with connection.cursor() as cursor:
        for single_match in analysis_match_list:
            cursor.execute(
                'SELECT time_score FROM %s WHERE match_id="%s"' % (tableName, single_match['match_id']))
            single_match_list = cursor.fetchall()
            single_match_dict = {}
            single_match_dict['match_id'] = single_match['match_id']
            single_match_dict['time_score'] = single_match_list[0]['time_score']
            update_match_list.append(single_match_dict)
    # connection is not autocommit by default. So you must commit to save your changes.
    cursor.close()
    if not connection.commit():
        connection.rollback()
finally:
    connection.close()

connection = pymysql.connect(**analysis_config)
print('连接至数据库' + analysis_db_name)
try:
    with connection.cursor() as cursor:
        tableName = 'teams_' + search_date
        for match in update_match_list:
            update_sql = (
                'UPDATE %s SET time_score="%s" WHERE match_id="%s"'
            )
            print('update信息')
            cursor.execute(update_sql % (
                tableName, match['time_score'], match['match_id']))
    # connection is not autocommit by default. So you must commit to save your changes.
    cursor.close()
    if not connection.commit():
        connection.rollback()

finally:
    connection.close()