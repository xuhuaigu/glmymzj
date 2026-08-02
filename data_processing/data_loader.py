# data_processing/data_loader.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union
import urllib.parse
import re
# ✅ 使用 oracledb 替代 cx_Oracle
import oracledb

# ✅ 指定 Instant Client 所在目录，启用 Thick 模式
try:
    oracledb.init_oracle_client(lib_dir=r"G:\mzjanzhuang\instantclient-basic-windows.x64-23.26.1.0.0\instantclient_23_0")
except Exception as e:
    st.error(f"初始化 Oracle Client 失败: {e}")

class DataLoader:
    """数据加载器"""
    """支持 MySQL, SQLite, Oracle, CSV, Excel"""
    
    def __init__(self):
        self._data = None
        self._data_source = None
        self._db_connection = None
    
    @st.cache_data
    def load_sample_data(_self, n_rows: int = 1000, random_seed: int = 42) -> pd.DataFrame:
        """加载示例数据"""
        np.random.seed(random_seed)
        
        dates = pd.date_range('2023-01-01', periods=n_rows, freq='D')
        
        df = pd.DataFrame({
            '日期': dates,
            '销售额': np.random.normal(10000, 2000, n_rows).cumsum(),
            '利润': np.random.normal(2000, 500, n_rows).cumsum(),
            '成本': np.random.normal(8000, 1500, n_rows),
            '销量': np.random.poisson(100, n_rows),
            '单价': np.random.uniform(50, 200, n_rows),
            '客户数': np.random.poisson(80, n_rows),
            '转化率': np.random.uniform(0.1, 0.4, n_rows),
            '评分': np.random.uniform(3, 5, n_rows),
            '地区': np.random.choice(['北区', '南区', '东区', '西区'], n_rows),
            '类别': np.random.choice(['A类', 'B类', 'C类', 'D类'], n_rows),
        })
        
        _self._data = df
        return df
    
    @st.cache_data
    def load_from_csv(_self, file, encoding: str = 'utf-8') -> Optional[pd.DataFrame]:
        """从CSV文件加载数据"""
        try:
            df = pd.read_csv(file, encoding=encoding)
            _self._data = df
            return df
        except Exception as e:
            st.error(f"加载CSV文件失败: {e}")
            return None
    
    @st.cache_data
    def load_from_excel(_self, file, sheet_name: Union[str, int] = 0) -> Optional[pd.DataFrame]:
        """从Excel文件加载数据"""
        try:
            df = pd.read_excel(file, sheet_name=sheet_name)
            _self._data = df
            return df
        except Exception as e:
            st.error(f"加载Excel文件失败: {e}")
            return None
    
    def _parse_config(self, config: dict, config_name: str) -> dict:
        """
        解析数据库配置，自动识别 dialect
        
        Args:
            config: 配置字典
            config_name: 配置名称
        """
        # 从配置名称或配置内容中推断 dialect
        dialect = config.get('dialect', None)
        
        # 如果配置中没有指定 dialect，根据名称推断
        if not dialect:
            if 'oracle' in config_name.lower():
                dialect = 'oracle'
            elif 'mysql' in config_name.lower():
                dialect = 'mysql'
            elif 'sqlite' in config_name.lower():
                dialect = 'sqlite'
            else:
                dialect = 'oracle'  # 默认 Oracle
        
        # 根据不同 dialect 解析配置
        if dialect == 'oracle':
            return {
                'dialect': 'oracle',
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 1521),
                'database': config.get('database', ''),
                'username': config.get('username', ''),
                'password': config.get('password', ''),
                'service_name': config.get('service_name', None),
                'sid': config.get('sid', None),
                'tns': config.get('tns', None),
                'dsn': config.get('dsn', None),
                'config_name': config_name
            }
        
        elif dialect == 'mysql':
            return {
                'dialect': 'mysql',
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 3306),
                'database': config.get('database', ''),
                'username': config.get('username', 'root'),
                'password': config.get('password', ''),
                'charset': config.get('query', {}).get('charset', 'utf8mb4'),
                'config_name': config_name
            }
        
        elif dialect == 'sqlite':
            return {
                'dialect': 'sqlite',
                'sqlite_path': config.get('sqlite_path', 'database.db'),
                'config_name': config_name
            }
        
        else:
            # 未知 dialect，返回原始配置
            config['dialect'] = dialect
            config['config_name'] = config_name
            return config
    
    def _get_database_config(self, config_name: str = None):
        """
        从 secrets.toml 获取数据库配置
        
        Args:
            config_name: 配置名称，如 'oracle_prod', 'mysql_dw' 等
                         如果为 None，则自动查找第一个可用的数据库配置
        """
        try:
            secrets = st.secrets
            
            # 1. 如果指定了配置名称，直接获取
            if config_name:
                # 检查 connections.{config_name} 格式
                if 'connections' in secrets and config_name in secrets.connections:
                    config = secrets.connections[config_name]
                    return self._parse_config(config, config_name)
                
                # 检查是否有直接匹配的键
                elif config_name in secrets:
                    config = secrets[config_name]
                    return self._parse_config(config, config_name)
                
                else:
                    st.error(f"未找到数据库配置: {config_name}")
                    return None
            
            # 2. 如果未指定名称，自动查找第一个可用的数据库配置
            # 优先查找 connections 下的配置
            if 'connections' in secrets:
                for key in secrets.connections.keys():
                    config = secrets.connections[key]
                    return self._parse_config(config, key)
            
            # 3. 兼容旧格式（直接在根级别配置）
            if 'host' in secrets and 'database' in secrets:
                return {
                    'dialect': 'mysql',
                    'host': secrets.get('host', 'localhost'),
                    'port': secrets.get('port', 3306),
                    'database': secrets.get('database', ''),
                    'username': secrets.get('user', 'root'),
                    'password': secrets.get('password', ''),
                    'charset': 'utf8mb4',
                    'config_name': 'legacy'
                }
            
            st.error("未找到任何数据库配置，请检查 .streamlit/secrets.toml")
            return None
            
        except Exception as e:
            st.error(f"读取数据库配置失败: {e}")
            return None
    
    def _get_oracle_connection_string(self, config: Dict) -> str:
        """生成 Oracle 连接字符串（使用 oracledb）"""
        username = config['username']
        password = urllib.parse.quote_plus(config['password'])
        host = config['host']
        port = config['port']
        
        # 优先使用 TNS
        if config.get('tns'):
            return f"oracle+oracledb://{username}:{password}@/?tns={config['tns']}"
        
        # 使用 SID 或 SERVICE_NAME
        if config.get('sid'):
            dsn = f"{host}:{port}/{config['sid']}"
        elif config.get('service_name'):
            dsn = f"{host}:{port}/{config['service_name']}"
        else:
            dsn = f"{host}:{port}/{config['database']}"
        
        return f"oracle+oracledb://{username}:{password}@{dsn}"
    
    @st.cache_data
    def get_database_tables(_self, config_name: str = None, schema: str = 'CQ') -> List[str]:
        """获取指定数据库中的所有表名"""
        try:
            import sqlalchemy as sa
            
            config = _self._get_database_config(config_name)
            if config is None:
                st.error("未找到数据库配置，请在 .streamlit/secrets.toml 中配置")
                return []
            
            dialect = config.get('dialect', 'mysql')
            
            # MySQL 连接
            if dialect == 'mysql':
                connection_string = (
                    f"mysql+pymysql://{config['username']}:{urllib.parse.quote_plus(config['password'])}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                    f"?charset={config['charset']}"
                )
                engine = sa.create_engine(connection_string)
                inspector = sa.inspect(engine)
                tables = inspector.get_table_names()
                engine.dispose()
                return tables
            
            # Oracle 连接（使用 oracledb）
            elif dialect == 'oracle':
                connection_string = _self._get_oracle_connection_string(config)
                engine = sa.create_engine(connection_string)
                inspector = sa.inspect(engine)
                # 修改这里：使用传入的 schema 参数，而不是用户名
                # 如果 schema 参数为空，则使用用户名作为默认值
                schema_name = schema if schema else config['username'].upper()
                tables = inspector.get_table_names(schema=schema_name)
                engine.dispose()
                return tables
            
            # SQLite 连接
            elif dialect == 'sqlite':
                import sqlite3
                sqlite_path = config.get('sqlite_path', 'database.db')
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                return tables
            
            else:
                st.error(f"不支持的数据库类型: {dialect}")
                return []
            
        except ImportError as e:
            st.error(f"缺少必要的数据库驱动: {e}\n请安装: pip install oracledb sqlalchemy pymysql")
            return []
        except Exception as e:
            st.error(f"获取数据库表失败: {e}")
            return []
    
    @st.cache_data
    def load_from_database(_self, table_name: str, limit: Optional[int] = None, config_name: str = None) -> Optional[pd.DataFrame]:
        """从数据库表加载数据
        config_name: 数据库配置名称，如果为 None，则自动查找第一个可用的数据库配置
        """
        try:
            import sqlalchemy as sa
            
            config = _self._get_database_config(config_name)
            if config is None:
                st.error("未找到数据库配置")
                return None
            
            dialect = config.get('dialect', 'mysql')
            
            # MySQL 连接
            if dialect == 'mysql':
                connection_string = (
                    f"mysql+pymysql://{config['username']}:{urllib.parse.quote_plus(config['password'])}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                    f"?charset={config['charset']}"
                )
                engine = sa.create_engine(connection_string)
                query = f"SELECT * FROM `{table_name}`"
                if limit:
                    query += f" LIMIT {limit}"
            
            # Oracle 连接（使用 oracledb）
            elif dialect == 'oracle':
                connection_string = _self._get_oracle_connection_string(config)
                engine = sa.create_engine(connection_string)
                # 去掉表名两边的双引号
                table_name_clean = table_name.strip('"')
                query = f'SELECT * FROM {table_name_clean}'
                if limit:
                    query = f'SELECT * FROM (SELECT * FROM {table_name_clean}) WHERE ROWNUM <= {limit}'
            
            # SQLite 连接
            elif dialect == 'sqlite':
                sqlite_path = config.get('sqlite_path', 'database.db')
                import sqlite3
                conn = sqlite3.connect(sqlite_path)
                query = f"SELECT * FROM {table_name}"
                if limit:
                    query += f" LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
                conn.close()
                _self._data = df
                return df
            
            else:
                st.error(f"不支持的数据库类型: {dialect}")
                return None
            
            # 执行查询
            with engine.connect() as conn:
                df = pd.read_sql_query(query, conn)
            engine.dispose()
            _self._data = df
            return df
            
        except ImportError as e:
            st.error(f"缺少必要的数据库驱动: {e}\n请安装: pip install oracledb sqlalchemy")
            return None
        except Exception as e:
            st.error(f"从数据库加载数据失败: {e}")
            return None
    
    @st.cache_data
    def execute_custom_query(_self, query: str, config_name: str = None) -> Optional[pd.DataFrame]:
        """执行自定义SQL查询"""
        try:
            import sqlalchemy as sa
            
            config = _self._get_database_config(config_name)
            if config is None:
                st.error("未找到数据库配置")
                return None
            
            dialect = config.get('dialect', 'mysql')
            
            # 如果是 Oracle，去掉表名两边的双引号
            if dialect == 'oracle' and query:
                query = re.sub(r'"([A-Z_]+)"', r'\1', query)
            
            # MySQL 连接
            if dialect == 'mysql':
                connection_string = (
                    f"mysql+pymysql://{config['username']}:{urllib.parse.quote_plus(config['password'])}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                    f"?charset={config['charset']}"
                )
                engine = sa.create_engine(connection_string)
                with engine.connect() as conn:
                    df = pd.read_sql_query(query, conn)
                engine.dispose()
                _self._data = df
                return df
            
            # Oracle 连接
            elif dialect == 'oracle':
                connection_string = _self._get_oracle_connection_string(config)
                engine = sa.create_engine(connection_string)
                with engine.connect() as conn:
                    df = pd.read_sql_query(query, conn)
                engine.dispose()
                _self._data = df
                return df
            
            # SQLite 连接
            elif dialect == 'sqlite':
                sqlite_path = config.get('sqlite_path', 'database.db')
                import sqlite3
                conn = sqlite3.connect(sqlite_path)
                df = pd.read_sql_query(query, conn)
                conn.close()
                _self._data = df
                return df
            
            else:
                st.error(f"不支持的数据库类型: {dialect}")
                return None
            
        except ImportError as e:
            st.error(f"缺少必要的数据库驱动: {e}")
            return None
        except Exception as e:
            st.error(f"执行查询失败: {e}")
            return None
    
    def get_data_info(self) -> dict:
        """获取数据信息"""
        if self._data is None:
            return {
                'shape': (0, 0),
                'rows': 0,
                'columns': 0,
                'missing_total': 0,
                'memory_usage': '0 MB'
            }
        
        df = self._data
        memory_bytes = df.memory_usage(deep=True).sum()
        
        if memory_bytes < 1024 * 1024:
            memory_str = f"{memory_bytes / 1024:.2f} KB"
        else:
            memory_str = f"{memory_bytes / 1024 / 1024:.2f} MB"
        
        return {
            'shape': df.shape,
            'rows': df.shape[0],
            'columns': df.shape[1],
            'missing_total': int(df.isnull().sum().sum()),
            'memory_usage': memory_str,
            'column_names': list(df.columns),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
        }
    
    def get_data(self):
        """获取当前数据"""
        return self._data
    
    def get_available_databases(self) -> List[str]:
        """获取所有可用的数据库配置名称"""
        try:
            secrets = st.secrets
            if 'connections' in secrets:
                return list(secrets.connections.keys())
            return []
        except:
            return []
    

    def get_full_table_schema(self, table_name: str, config_name: str = None) -> pd.DataFrame:
        """
        获取完整的表结构信息（字段名、类型、大小、是否可空、键、注释等）
        
        参数:
            table_name: 表名（支持 schema.table 格式）
            config_name: 数据库配置名称
        
        返回:
            DataFrame: 包含字段名、数据类型、长度、是否可空、键类型、注释等信息
        """
        try:
            import sqlalchemy as sa
            
            config = self._get_database_config(config_name)
            if config is None:
                st.error("未找到数据库配置")
                return None
            
            dialect = config.get('dialect', 'mysql')
            
            # 处理表名（去掉可能存在的 schema 前缀）
            clean_table_name = table_name.split('.')[-1] if '.' in table_name else table_name
            schema_name = table_name.split('.')[0] if '.' in table_name else None
            
            # 根据数据库类型构建不同的查询
            if dialect == 'oracle':
                return self._get_oracle_table_schema(clean_table_name, schema_name, config)
            elif dialect == 'mysql':
                return self._get_mysql_table_schema(clean_table_name, config)
            else:
                st.error(f"不支持的数据库类型: {dialect}")
                return None
                
        except Exception as e:
            st.error(f"获取表结构失败: {e}")
            import traceback
            st.error(traceback.format_exc())
            return None

    def _get_oracle_table_schema(self, table_name: str, schema_name: str, config: dict) -> pd.DataFrame:
        """获取 Oracle 表结构"""
        try:
            import sqlalchemy as sa
            
            # 构建连接字符串
            connection_string = self._get_oracle_connection_string(config)
            engine = sa.create_engine(connection_string)
            
            # 获取列信息
            inspector = sa.inspect(engine)
            columns = inspector.get_columns(table_name, schema=schema_name)
            
            # 获取主键
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
            pk_columns = pk_constraint.get('constrained_columns', [])
            
            # 获取外键
            fk_constraints = inspector.get_foreign_keys(table_name, schema=schema_name)
            fk_map = {}
            for fk in fk_constraints:
                for col in fk['constrained_columns']:
                    fk_map[col] = f"外键 → {fk['referred_table']}.{fk['referred_columns'][0]}"
            
            # 获取注释（Oracle 需要额外查询）
            comments = {}
            try:
                with engine.connect() as conn:
                    # 获取列注释
                    query = f"""
                    SELECT COLUMN_NAME, COMMENTS 
                    FROM USER_COL_COMMENTS 
                    WHERE TABLE_NAME = UPPER('{table_name}')
                    """
                    if schema_name:
                        query = f"""
                        SELECT COLUMN_NAME, COMMENTS 
                        FROM ALL_COL_COMMENTS 
                        WHERE OWNER = UPPER('{schema_name}')
                        AND TABLE_NAME = UPPER('{table_name}')
                        """
                    result = conn.execute(sa.text(query))
                    for row in result:
                        comments[row[0]] = row[1]
            except:
                pass
            
            # 构建结果 DataFrame
            schema_data = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                
                # 提取长度信息
                length = ''
                if hasattr(col['type'], 'length') and col['type'].length:
                    length = str(col['type'].length)
                elif hasattr(col['type'], 'precision') and col['type'].precision:
                    precision = col['type'].precision
                    scale = col['type'].scale if hasattr(col['type'], 'scale') and col['type'].scale else 0
                    length = f"{precision},{scale}" if scale > 0 else str(precision)
                
                # 键类型
                key_type = ''
                if col_name in pk_columns:
                    key_type = '主键'
                elif col_name in fk_map:
                    key_type = fk_map[col_name]
                
                schema_data.append({
                    '字段名': col_name,
                    '数据类型': col_type,
                    '长度': length,
                    '是否可空': '✅ 是' if col.get('nullable', True) else '❌ 否',
                    '键类型': key_type,
                    '注释': comments.get(col_name, ''),
                    '默认值': str(col.get('default', '')) if col.get('default') is not None else ''
                })
            
            engine.dispose()
            return pd.DataFrame(schema_data)
            
        except Exception as e:
            st.error(f"获取 Oracle 表结构失败: {e}")
            return None

    def _get_mysql_table_schema(self, table_name: str, config: dict) -> pd.DataFrame:
        """获取 MySQL 表结构"""
        try:
            import sqlalchemy as sa
            
            # 构建连接字符串
            connection_string = (
                f"mysql+pymysql://{config['username']}:{urllib.parse.quote_plus(config['password'])}"
                f"@{config['host']}:{config['port']}/{config['database']}"
                f"?charset={config['charset']}"
            )
            engine = sa.create_engine(connection_string)
            
            # 获取列信息
            inspector = sa.inspect(engine)
            columns = inspector.get_columns(table_name)
            
            # 获取主键
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_columns = pk_constraint.get('constrained_columns', [])
            
            # 获取外键
            fk_constraints = inspector.get_foreign_keys(table_name)
            fk_map = {}
            for fk in fk_constraints:
                for col in fk['constrained_columns']:
                    fk_map[col] = f"外键 → {fk['referred_table']}.{fk['referred_columns'][0]}"
            
            # 获取额外信息（自增等）
            extra_info = {}
            try:
                with engine.connect() as conn:
                    query = f"""
                    SELECT COLUMN_NAME, EXTRA 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = '{table_name}'
                    """
                    result = conn.execute(sa.text(query))
                    for row in result:
                        if row[1]:
                            extra_info[row[0]] = row[1]
            except:
                pass
            
            # 构建结果 DataFrame
            schema_data = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                
                # 提取长度信息
                length = ''
                if hasattr(col['type'], 'length') and col['type'].length:
                    length = str(col['type'].length)
                elif hasattr(col['type'], 'precision') and col['type'].precision:
                    precision = col['type'].precision
                    scale = col['type'].scale if hasattr(col['type'], 'scale') and col['type'].scale else 0
                    length = f"{precision},{scale}" if scale > 0 else str(precision)
                
                # 键类型
                key_type = ''
                if col_name in pk_columns:
                    key_type = '主键'
                elif col_name in fk_map:
                    key_type = fk_map[col_name]
                
                schema_data.append({
                    '字段名': col_name,
                    '数据类型': col_type,
                    '长度': length,
                    '是否可空': '✅ 是' if col.get('nullable', True) else '❌ 否',
                    '键类型': key_type,
                    '注释': col.get('comment', ''),
                    '默认值': str(col.get('default', '')) if col.get('default') is not None else '',
                    '额外信息': extra_info.get(col_name, '')
                })
            
            engine.dispose()
            return pd.DataFrame(schema_data)
            
        except Exception as e:
            st.error(f"获取 MySQL 表结构失败: {e}")
            return None

    def get_table_statistics(self, table_name: str, config_name: str = None) -> dict:
        """
        获取表的统计信息
        
        参数:
            table_name: 表名
            config_name: 数据库配置名称
        
        返回:
            dict: 包含行数、列数、大小等统计信息
        """
        try:
            import sqlalchemy as sa
            
            config = self._get_database_config(config_name)
            if config is None:
                return None
            
            dialect = config.get('dialect', 'mysql')
            clean_table_name = table_name.split('.')[-1] if '.' in table_name else table_name
            schema_name = table_name.split('.')[0] if '.' in table_name else None
            
            info = {}
            
            if dialect == 'mysql':
                connection_string = (
                    f"mysql+pymysql://{config['username']}:{urllib.parse.quote_plus(config['password'])}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                    f"?charset={config['charset']}"
                )
                engine = sa.create_engine(connection_string)
                
                with engine.connect() as conn:
                    # 获取行数
                    result = conn.execute(sa.text(f"SELECT COUNT(*) FROM `{clean_table_name}`"))
                    info['行数'] = result.scalar()
                    
                    # 获取列数
                    result = conn.execute(sa.text(f"""
                        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{clean_table_name}'
                    """))
                    info['列数'] = result.scalar()
                    
                    # 获取表大小
                    result = conn.execute(sa.text(f"""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = '{clean_table_name}'
                    """))
                    size_result = result.fetchone()
                    info['大小(MB)'] = size_result[0] if size_result else 0
                
                engine.dispose()
                
            elif dialect == 'oracle':
                connection_string = self._get_oracle_connection_string(config)
                engine = sa.create_engine(connection_string)
                
                with engine.connect() as conn:
                    # 获取行数
                    result = conn.execute(sa.text(f"SELECT COUNT(*) FROM {clean_table_name}"))
                    info['行数'] = result.scalar()
                    
                    # 获取列数
                    query = f"""
                    SELECT COUNT(*) FROM USER_TAB_COLUMNS 
                    WHERE TABLE_NAME = UPPER('{clean_table_name}')
                    """
                    if schema_name:
                        query = f"""
                        SELECT COUNT(*) FROM ALL_TAB_COLUMNS 
                        WHERE OWNER = UPPER('{schema_name}')
                        AND TABLE_NAME = UPPER('{clean_table_name}')
                        """
                    result = conn.execute(sa.text(query))
                    info['列数'] = result.scalar()
                    
                    # Oracle 表大小
                    info['大小(MB)'] = 'N/A'
                
                engine.dispose()
            
            return info
            
        except Exception as e:
            st.error(f"获取表统计信息失败: {e}")
            return None

    

# 创建全局实例
data_loader = DataLoader()