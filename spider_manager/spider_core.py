# spider_manager/spider_core.py
import streamlit as st
import pandas as pd
import json
import time
import re
import os
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from DrissionPage import ChromiumPage
from openpyxl import Workbook

# 尝试导入数据库模块，如果失败则使用简单存储
try:
    from .spider_db import (
        create_task, update_task_status, add_task_log, add_crawled_data,
        get_task, get_task_logs, get_task_data, get_all_tasks, delete_task
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Warning: spider_db not available, using in-memory storage")

class SpiderCore:
    """爬虫核心类 - 支持后台运行"""
    
    def __init__(self):
        self.running_tasks = {}
        self.tasks = []
    # 在 spider_core.py 的 SpiderCore 类中添加以下方法

    

    def stop_task(self, task_id: str):
        """停止正在运行的任务"""
        self._add_log(task_id, "INFO", "正在停止任务...")
        
        # 更新任务状态为停止
        self._update_task(task_id, "stopped", 
                        end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 如果有运行中的线程，标记为停止
        if task_id in self.running_tasks:
            # 设置一个标志让爬虫线程停止
            self._stop_flag = True
            
        self._add_log(task_id, "INFO", "任务已停止")

    def is_stop_requested(self) -> bool:
        """检查是否有停止请求"""
        return getattr(self, '_stop_flag', False)

    def clear_stop_flag(self):
        """清除停止标志"""
        self._stop_flag = False

    def get_category_name(self, page, url):
        """从URL中提取并获取商品类别名称"""
        try:
            page.get(url)
            time.sleep(2)
            
            title_elem = page.ele('css:title', timeout=2)
            if title_elem:
                title_text = title_elem.text.strip()
                if '最新报价' in title_text:
                    return title_text.split('最新报价')[0].strip()
        except:
            pass
        
        match = re.search(r'plist-1-(\d+)', url)
        category_id = match.group(1) if match else "unknown"
        return f"商品_{category_id}"
    
    def parse_date(self, date_str):
        """解析日期字符串，支持多种格式"""
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = date_str.strip()
        
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%m-%d',
            '%m/%d',
        ]
        
        for fmt in formats:
            try:
                if fmt in ['%m-%d', '%m/%d']:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.replace(year=datetime.now().year)
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def filter_by_date(self, row_data, target_date):
        """检查数据行是否为指定日期"""
        publish_time = row_data[8]
        if not publish_time:
            return False
        
        date_part = publish_time.split()[0] if ' ' in publish_time else publish_time
        row_date = self.parse_date(date_part)
        if not row_date:
            return False
        
        return row_date.date() == target_date.date()
    
    def crawl_category(self, base_url, category_name, target_date, task_id, max_pages=50):
        """爬取单个商品分类的指定日期数据 - 完整版"""
        max_pages = max(1, min(50, max_pages))
        
        if base_url.endswith('.html'):
            base_url_pattern = base_url.rsplit('-', 1)[0] + '-'
        else:
            base_url_pattern = base_url + '-'
        
        self._add_log(task_id, "INFO", f"开始爬取: {category_name} (目标日期: {target_date.strftime('%Y-%m-%d')})")
        self._add_log(task_id, "INFO", f"最大页数: {max_pages}")
        
        page = ChromiumPage()
        all_data = []
        current_page = 1
        found_target_date = False
        
        try:
            while current_page <= max_pages:
                 # ========== 添加停止检查 ==========
                if self.is_stop_requested():
                    self._add_log(task_id, "INFO", "收到停止信号，停止爬取当前分类")
                    break

                current_url = f"{base_url_pattern}{current_page}.html"
                self._add_log(task_id, "INFO", f"正在抓取第 {current_page} 页...")
                
                try:
                    page.get(current_url)
                    time.sleep(1.5)
                    
                    # 查找表格行
                    rows = page.eles('css:table.lp-table.mb15 tbody tr', timeout=5)
                    if not rows:
                        rows = page.eles('css:tbody tr', timeout=5)
                    
                    if not rows:
                        self._add_log(task_id, "WARNING", f"第{current_page}页未找到数据表格，停止抓取")
                        break
                    
                    page_data_count = 0
                    page_stop = False
                    
                    for row in rows:
                        try:
                            # 获取商品名称和详情链接
                            name_link = row.ele('css:.p-name a', timeout=1)
                            if name_link:
                                product_name = name_link.text.strip()
                                detail_url = name_link.attr('href') if name_link else ""
                                if detail_url and detail_url.startswith('/'):
                                    detail_url = f"https://www.100ppi.com{detail_url}"
                            else:
                                first_td = row.ele('css:td:nth-child(1)', timeout=1)
                                product_name = first_td.text.strip() if first_td else ""
                                detail_url = ""
                            
                            if not product_name or product_name == '':
                                continue
                            
                            # 获取规格
                            spec_elem = row.ele('css:td:nth-child(2)', timeout=1)
                            spec = spec_elem.text.strip() if spec_elem else ""
                            
                            # 获取品牌/产地
                            brand_elem = row.ele('css:td:nth-child(3)', timeout=1)
                            brand = brand_elem.text.strip() if brand_elem else ""
                            
                            # 获取报价
                            price_elem = row.ele('css:td:nth-child(4)', timeout=1)
                            price = price_elem.text.strip() if price_elem else ""
                            
                            # 获取报价类型
                            price_type_elem = row.ele('css:td:nth-child(5)', timeout=1)
                            price_type = price_type_elem.text.strip() if price_type_elem else ""
                            
                            # 获取交货地
                            delivery_elem = row.ele('css:td:nth-child(6)', timeout=1)
                            delivery = delivery_elem.text.strip() if delivery_elem else ""
                            
                            # 获取交易商
                            trader_elem = row.ele('css:td:nth-child(7)', timeout=1)
                            if trader_elem:
                                company_link = trader_elem.ele('css:a', timeout=1)
                                trader = company_link.text.strip() if company_link else trader_elem.text.strip()
                                trader = trader.replace('VIP', '').replace(' ', '').strip()
                            else:
                                trader = ""
                            
                            # 获取发布时间
                            time_elem = row.ele('css:td:nth-child(8)', timeout=1)
                            publish_time = time_elem.text.strip() if time_elem else ""
                            
                            row_data = [
                                category_name, product_name, spec, brand, price,
                                price_type, delivery, trader, publish_time, detail_url
                            ]
                            
                            # 检查日期是否匹配
                            if self.filter_by_date(row_data, target_date):
                                all_data.append(row_data)
                                self._add_crawled_data(task_id, row_data)
                                page_data_count += 1
                                found_target_date = True
                            else:
                                # 如果已经找到了目标日期的数据，并且当前数据的日期更早，则停止
                                if found_target_date:
                                    publish_date_part = publish_time.split()[0] if publish_time else ""
                                    if publish_date_part:
                                        row_date = self.parse_date(publish_date_part)
                                        if row_date and row_date.date() < target_date.date():
                                            page_stop = True
                                            break
                            
                        except Exception as e:
                            continue
                    
                    self._add_log(task_id, "INFO", f"第 {current_page} 页完成，获取 {page_data_count} 条{target_date.strftime('%Y-%m-%d')}的数据")
                    
                    if page_stop:
                        self._add_log(task_id, "INFO", "已遇到更早日期的数据，停止后续抓取")
                        break
                    
                    if page_data_count == 0 and found_target_date:
                        self._add_log(task_id, "INFO", "本页无目标日期数据，停止抓取")
                        break
                    
                    if page_data_count < 2 and current_page > 3:
                        self._add_log(task_id, "INFO", "连续多页数据较少，可能已到末尾")
                        break
                    
                    current_page += 1
                    
                except Exception as e:
                    self._add_log(task_id, "ERROR", f"第 {current_page} 页出错: {e}")
                    break
        
        finally:
            try:
                page.quit()
            except:
                pass
        
        self._add_log(task_id, "INFO", f"{category_name} 共抓取 {len(all_data)} 条 {target_date.strftime('%Y-%m-%d')} 的数据")
        return all_data
    
    def crawl_all_categories(self, task_id: str, target_date: datetime):
        """批量爬取多个商品分类"""
        task = self.get_task_status(task_id)
        if not task:
            return 0, None
        
        config = task.get('config', {})
        if isinstance(config, str):
            config = json.loads(config)
        
        base_urls = config.get('target_urls', self.get_default_urls())
        save_path = config.get('save_path', './spider_data')
        max_pages = config.get('max_pages_per_category', 5)
        
        os.makedirs(save_path, exist_ok=True)
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = f"商品报价_{target_date.strftime('%Y%m%d')}"
        ws.append(['商品类别', '商品名称', '规格', '品牌/产地', '报价', 
                   '报价类型', '交货地', '交易商', '发布时间', '详情链接'])
        
        total_records = 0
        total_urls = len(base_urls)
        
        self._update_task(task_id, "running", start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         total_categories=total_urls, processed_categories=0)
        self._add_log(task_id, "INFO", f"开始爬取任务，共{total_urls}个商品分类，目标日期：{target_date.strftime('%Y-%m-%d')}")
        
        for idx, url in enumerate(base_urls, 1):
            # ========== 添加停止检查 ==========
            if self.is_stop_requested():
                self._add_log(task_id, "INFO", "收到停止信号，正在终止任务...")
                break
            # 获取分类名称
            temp_page = None
            try:
                temp_page = ChromiumPage()
                category_name = self.get_category_name(temp_page, url)
            except Exception:
                match = re.search(r'plist-1-(\d+)', url)
                category_name = f"商品_{match.group(1) if match else 'unknown'}"
            finally:
                if temp_page:
                    try:
                        temp_page.quit()
                    except:
                        pass
            
            # 爬取该分类的数据
            try:
                self._add_log(task_id, "INFO", f"进度: [{idx}/{total_urls}] 正在爬取: {category_name}")
                
                category_data = self.crawl_category(url, category_name, target_date, task_id, max_pages)
                
                # 写入Excel
                for row_data in category_data:
                    ws.append(row_data)
                    total_records += 1
                
                # 更新进度
                self._update_task(task_id, "running", 
                                 processed_categories=idx,
                                 total_records=total_records,
                                 current_category=category_name,
                                 progress=int(idx / total_urls * 100))
                
                self._add_log(task_id, "INFO", f"✅ {category_name} 完成，获取{len(category_data)}条数据，累计{total_records}条")
                
            except Exception as e:
                self._add_log(task_id, "ERROR", f"❌ {category_name} 爬取失败: {str(e)}")
                continue
            
            time.sleep(2)
        
        # 设置列宽
        column_widths = {'A': 18, 'B': 15, 'C': 30, 'D': 15, 'E': 12, 
                         'F': 12, 'G': 20, 'H': 25, 'I': 15, 'J': 35}
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # 保存文件
        filename = f'商品报价_{target_date.strftime("%Y%m%d")}_{datetime.now().strftime("%H%M%S")}.xlsx'
        file_path = os.path.join(save_path, filename)
        wb.save(file_path)
        
        # 完成任务
        self._update_task(task_id, "completed", 
                         end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         file_path=file_path,
                         total_records=total_records,
                         progress=100)
        
        self._add_log(task_id, "SUCCESS", f"🎉 任务完成！共获取{total_records}条数据，保存至：{file_path}")
        
        return total_records, file_path
    
    def create_and_start_task(self, name: str, target_date: datetime, config: Dict) -> str:
        """创建并启动任务"""
        self.clear_stop_flag() 
        task_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:4]
        
        task = {
            'id': task_id,
            'name': name,
            'target_date': target_date.strftime('%Y-%m-%d'),
            'status': 'pending',
            'total_records': 0,
            'progress': 0,
            'current_category': '',
            'processed_categories': 0,
            'total_categories': len(config.get('target_urls', [])),
            'file_path': None,
            'error_msg': None,
            'start_time': None,
            'end_time': None,
            'config': config,
            'logs': [],
            'data': []
        }
        
        if DB_AVAILABLE:
            create_task(task_id, name, target_date, config)
        else:
            self.tasks.append(task)
        
        self._add_log(task_id, "INFO", f"任务「{name}」已创建，目标日期：{target_date.strftime('%Y-%m-%d')}")
        
        # 异步启动
        self.start_task_async(task_id, target_date)
        
        return task_id
    
    def start_task_async(self, task_id: str, target_date: datetime):
        """异步启动爬虫任务"""
        def run():
            try:
                self.crawl_all_categories(task_id, target_date)
            except Exception as e:
                self._update_task(task_id, "failed", error_msg=str(e))
                self._add_log(task_id, "ERROR", f"任务失败: {str(e)}")
            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
        
        thread = threading.Thread(target=run, daemon=True)
        self.running_tasks[task_id] = thread
        thread.start()
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        if DB_AVAILABLE:
            return get_task(task_id)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    return task
            return None
    
    def get_task_logs(self, task_id: str, limit=200) -> List:
        """获取任务日志"""
        if DB_AVAILABLE:
            return get_task_logs(task_id, limit)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    return task.get('logs', [])[-limit:]
            return []
    
    def get_task_data(self, task_id: str, limit=1000) -> List:
        """获取任务数据"""
        if DB_AVAILABLE:
            return get_task_data(task_id, limit)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    return task.get('data', [])[-limit:]
            return []
    
    def get_all_tasks(self, limit=50) -> List:
        """获取所有任务"""
        if DB_AVAILABLE:
            return get_all_tasks(limit)
        else:
            return self.tasks[-limit:]
    
    def delete_task(self, task_id: str):
        """删除任务"""
        if DB_AVAILABLE:
            delete_task(task_id)
        else:
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
    
    def _add_log(self, task_id: str, level: str, message: str):
        """添加日志"""
        log = {
            'task_id': task_id,
            'level': level,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if DB_AVAILABLE:
            add_task_log(task_id, level, message)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    if 'logs' not in task:
                        task['logs'] = []
                    task['logs'].append(log)
                    break
    
    def _add_crawled_data(self, task_id: str, row_data: List):
        """添加爬取的数据"""
        data_row = {
            'task_id': task_id,
            'category_name': row_data[0],
            'product_name': row_data[1],
            'spec': row_data[2],
            'brand': row_data[3],
            'price': row_data[4],
            'price_type': row_data[5],
            'delivery': row_data[6],
            'trader': row_data[7],
            'publish_time': row_data[8],
            'detail_url': row_data[9],
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if DB_AVAILABLE:
            add_crawled_data(task_id, row_data)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    if 'data' not in task:
                        task['data'] = []
                    task['data'].append(data_row)
                    break
    
    def _update_task(self, task_id: str, status: str, **kwargs):
        """更新任务状态"""
        updates = kwargs
        updates['status'] = status
        
        if DB_AVAILABLE:
            update_task_status(task_id, status, **kwargs)
        else:
            for task in self.tasks:
                if task['id'] == task_id:
                    for key, value in updates.items():
                        task[key] = value
                    break
    
    def get_default_urls(self) -> List[str]:
        """获取默认的商品URL列表"""
        return [
            "https://www.100ppi.com/mprice/plist-1-86-1.html",
            "https://www.100ppi.com/mprice/plist-1-1090-1.html",
            "https://www.100ppi.com/mprice/plist-1-3107-1.html",
            "https://www.100ppi.com/mprice/plist-1-83-1.html",
            "https://www.100ppi.com/mprice/plist-1-81-1.html",
            "https://www.100ppi.com/mprice/plist-1-837-1.html",
            "https://www.100ppi.com/mprice/plist-1-2309-1.html",
            "https://www.100ppi.com/mprice/plist-1-9071-1.html",
            "https://www.100ppi.com/mprice/plist-1-490-1.html",
            "https://www.100ppi.com/mprice/plist-1-11234-1.html",
            "https://www.100ppi.com/mprice/plist-1-493-1.html",
            "https://www.100ppi.com/mprice/plist-1-1932-1.html",
            "https://www.100ppi.com/mprice/plist-1-14866-1.html",
            "https://www.100ppi.com/mprice/plist-1-1274-1.html",
            "https://www.100ppi.com/mprice/plist-1-82-1.html",
            "https://www.100ppi.com/mprice/plist-1-6654-1.html",
            "https://www.100ppi.com/mprice/plist-1-5922-1.html",
            "https://www.100ppi.com/mprice/plist-1-8285-1.html",
            "https://www.100ppi.com/mprice/plist-1-485-1.html",
            "https://www.100ppi.com/mprice/plist-1-8113-1.html",
            "https://www.100ppi.com/mprice/plist-1-492-1.html",
            "https://www.100ppi.com/mprice/plist-1-2311-1.html",
            "https://www.100ppi.com/mprice/plist-1-2610-1.html",
            "https://www.100ppi.com/mprice/plist-1-1087-1.html",
            "https://www.100ppi.com/mprice/plist-1-1048-1.html"
        ]
    def get_tasks(self, limit=50) -> List:
        """获取所有任务"""
        return self.get_all_tasks(limit)
# 创建全局实例
spider_core = SpiderCore()