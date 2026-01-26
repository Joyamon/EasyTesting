import pymysql
import pandas as pd
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager
from typing import Dict, Any, List
import threading

# 全局连接池字典，按配置存储不同的连接池
_connection_pools: Dict[str, PooledDB] = {}
_pool_lock = threading.Lock()


def create_pool_key(**kwargs) -> str:
    """生成连接池的唯一键"""
    # 移除可能变化的参数
    pool_kwargs = kwargs.copy()
    pool_kwargs.pop('cursorclass', None)
    pool_kwargs.pop('autocommit', None)

    # 按字母顺序排序确保一致性
    sorted_items = sorted(pool_kwargs.items())
    return str(sorted_items)


def get_or_create_pool(**kwargs) -> PooledDB:
    """获取或创建连接池"""
    pool_key = create_pool_key(**kwargs)

    with _pool_lock:
        if pool_key not in _connection_pools:
            # 设置连接池参数
            pool_kwargs = {
                'creator': pymysql,
                'mincached': 2,  # 启动时开启的空连接数量
                'maxcached': 5,  # 连接池最大空闲连接数
                'maxshared': 3,  # 最大共享连接数
                'maxconnections': 20,  # 最大连接数
                'blocking': True,  # 连接数达到最大时是否阻塞等待
                'maxusage': 100,  # 单个连接最多重复使用次数
                'setsession': [],  # 开始会话前执行的命令列表
                'ping': 1,  # 检查连接是否可用的频率 (0=从不, 1=查询时, 2=创建时, 4=执行时, 7=总是)
                'host': kwargs.get('host', 'localhost'),
                'port': kwargs.get('port', 3306),
                'user': kwargs.get('user', 'root'),
                'password': kwargs.get('password', ''),
                'database': kwargs.get('database', ''),
                'charset': kwargs.get('charset', 'utf8mb4'),
                'cursorclass': kwargs.get('cursorclass', pymysql.cursors.DictCursor),
                'autocommit': kwargs.get('autocommit', True)
            }

            # 移除None值
            pool_kwargs = {k: v for k, v in pool_kwargs.items() if v is not None}

            # 创建连接池
            pool = PooledDB(**pool_kwargs)
            _connection_pools[pool_key] = pool

    return _connection_pools[pool_key]


@contextmanager
def get_connection_from_pool(**kwargs):
    """从连接池获取连接的上下文管理器"""
    pool = get_or_create_pool(**kwargs)
    connection = pool.connection()

    try:
        yield connection
    finally:
        connection.close()  # 实际是归还连接到池中


def connect_mysql(sql: str, *args, **kwargs) -> pd.DataFrame:
    """
    连接数据库（使用连接池优化）
    :param sql: SQL语句
    :param args: SQL参数
    :param kwargs: 数据库连接参数
    :return: DataFrame结果
    """
    try:
        with get_connection_from_pool(**kwargs) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args if args else None)

                if cursor.description:  # 有返回结果（SELECT等）
                    results = cursor.fetchall()

                    # 处理不同类型的游标
                    if isinstance(cursor, pymysql.cursors.DictCursor):
                        # 字典游标直接转换为DataFrame
                        df = pd.DataFrame(results)
                    else:
                        # 普通游标需要获取列名
                        columns = [i[0] for i in cursor.description]
                        df = pd.DataFrame(results, columns=columns)
                else:
                    # 无返回结果（INSERT、UPDATE、DELETE等）
                    conn.commit()
                    df = pd.DataFrame({'影响行数': [cursor.rowcount]})

                return df

    except Exception as e:
        # 可以添加日志记录
        print(f"Database error: {e}")
        raise


# 批量查询版本（提高性能）
def batch_connect_mysql(queries: List[Dict[str, Any]], **kwargs) -> Dict[str, pd.DataFrame]:
    """
    批量执行多个查询
    :param queries: 查询列表，每个元素为包含'sql'和'args'的字典
    :param kwargs: 数据库连接参数
    :return: 包含所有查询结果的字典
    """
    results = {}

    with get_connection_from_pool(**kwargs) as conn:
        for query in queries:
            sql = query.get('sql')
            args = query.get('args', ())
            name = query.get('name', f'query_{len(results)}')

            with conn.cursor() as cursor:
                cursor.execute(sql, args)

                if cursor.description:
                    results_list = cursor.fetchall()

                    if isinstance(cursor, pymysql.cursors.DictCursor):
                        df = pd.DataFrame(results_list)
                    else:
                        columns = [i[0] for i in cursor.description]
                        df = pd.DataFrame(results_list, columns=columns)
                else:
                    conn.commit()
                    df = pd.DataFrame({'影响行数': [cursor.rowcount]})

                results[name] = df

    return results


# 带事务支持的版本
def connect_mysql_transaction(sql: str, *args, **kwargs) -> pd.DataFrame:
    """
    带事务支持的数据库连接
    :param sql: SQL语句
    :param args: SQL参数
    :param kwargs: 数据库连接参数
    :return: DataFrame结果
    """
    with get_connection_from_pool(**kwargs) as conn:
        try:
            # 开始事务
            conn.begin()

            with conn.cursor() as cursor:
                cursor.execute(sql, args if args else None)

                if cursor.description:
                    results = cursor.fetchall()

                    if isinstance(cursor, pymysql.cursors.DictCursor):
                        df = pd.DataFrame(results)
                    else:
                        columns = [i[0] for i in cursor.description]
                        df = pd.DataFrame(results, columns=columns)
                else:
                    df = pd.DataFrame({'影响行数': [cursor.rowcount]})

            # 提交事务
            conn.commit()
            return df

        except Exception as e:
            # 回滚事务
            conn.rollback()
            print(f"回滚错误: {e}")
            raise


