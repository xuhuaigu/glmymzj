# spider_zhuwang/corn_spider.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os
import glob
from openpyxl.utils import get_column_letter

# 获取当前文件所在目录
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
# 默认保存目录
DEFAULT_SAVE_DIR = os.path.join(_PROJECT_ROOT, 'data_save', 'yangzhuwang_doupo')

class CornPriceSpider:
    """
    豆粕价格数据爬虫类
    用于爬取中国养猪网豆粕价格数据并保存到Excel
    支持省级数据和全国数据两种格式
    """
    
    # 默认保存目录
    DEFAULT_SAVE_DIR = DEFAULT_SAVE_DIR
    
    def __init__(self, creator='mzj', save_dir=None):
        """
        初始化爬虫
        
        Args:
            creator: 创建人，默认为'mzj'
            save_dir: 保存目录，默认为 DEFAULT_SAVE_DIR
        """
        self.creator = creator
        self.save_dir = save_dir or self.DEFAULT_SAVE_DIR
        
        # 确保保存目录存在
        os.makedirs(self.save_dir, exist_ok=True)
        print(f"📁 豆粕数据保存目录: {self.save_dir}")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.data = []
        self.df = None
        self.source_urls = []
        self.data_types = []
        self.province_names = []
    
    def get_excel_files(self):
        """获取目录下所有豆粕价格Excel文件"""
        pattern = os.path.join(self.save_dir, "豆粕价格_*.xlsx")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)
        return files
    
    def detect_data_type(self, url):
        """检测URL对应的数据类型（省级或全国）"""
        try:
            print(f"正在检测URL类型: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            h3_tag = soup.find('h3')
            if h3_tag:
                title_text = h3_tag.text.strip()
                print(f"检测到标题: {title_text}")
                
                if '全国' in title_text:
                    print("判断为: 全国数据")
                    return 'national', '全国'
                
                # 匹配省级数据格式
                match = re.search(r'(\d{4}年\d{2}月\d{2}日)([\u4e00-\u9fa5]+?)(?:省|自治区|市|全国)', title_text)
                if match:
                    province_name = match.group(2)
                    print(f"判断为: 省级数据, 省份={province_name}")
                    return 'province', province_name
                
                # 尝试提取省份
                match = re.search(r'([\u4e00-\u9fa5]{2,})', title_text)
                if match:
                    province_name = match.group(1)
                    print(f"判断为: 省级数据, 省份={province_name}")
                    return 'province', province_name
            else:
                print("未找到h3标签，尝试通过表格结构判断...")
                table = soup.find('table', class_='tabzj')
                if table:
                    thead = table.find('thead')
                    if thead:
                        tr = thead.find('tr')
                        if tr:
                            th_count = len(tr.find_all('th'))
                            if th_count == 6:
                                print("通过表格结构判断为: 全国数据")
                                return 'national', '全国'
                            elif th_count == 5:
                                print("通过表格结构判断为: 省级数据")
                                rows = table.find_all('tr')
                                for row in rows:
                                    if row.find('td') and 'colspan' in str(row):
                                        title_text = row.find('td').text.strip()
                                        match = re.search(r'^([\u4e00-\u9fa5]+)', title_text)
                                        if match:
                                            province_name = match.group(1)
                                            return 'province', province_name
                                return 'province', '未知省份'
            
            print("无法判断数据类型，默认作为省级数据")
            return 'province', '未知省份'
                
        except Exception as e:
            print(f"检测URL类型失败: {e}")
            return 'province', '未知省份'
    
    def fetch_data_auto(self, url):
        """自动检测并爬取数据"""
        data_type, province_name = self.detect_data_type(url)
        
        if data_type == 'national':
            data = self.fetch_national_data(url)
        else:
            data = self.fetch_province_data(url, province_name)
        
        return data, data_type, province_name
    
    def fetch_province_data(self, url, province_name=None):
        """爬取省级豆粕价格数据"""
        print(f"正在爬取省级数据: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='tabzj')
            if not table:
                print("未找到数据表格")
                return []
            
            data_list = []
            rows = table.find_all('tr')
            
            # 提取省份和日期
            if not province_name:
                province_name, date_text = self._extract_province_title_info(rows, soup)
            else:
                _, date_text = self._extract_province_title_info(rows, soup)
            
            # 遍历数据行
            for row in rows:
                cells = row.find_all('td')
                
                # 跳过空行或说明行
                if not cells or len(cells) < 5:
                    continue
                
                # 跳过colspan行（标题行）
                if cells[0].get('colspan') == '5':
                    continue
                
                # 解析数据行
                try:
                    city = cells[0].text.strip()
                    price_today = cells[1].text.strip()
                    price_yesterday = cells[2].text.strip()
                    change_today = cells[3].text.strip()
                    change_week = cells[4].text.strip()
                    
                    # 跳过空数据行
                    if not city or not price_today:
                        continue
                    
                    row_data = {
                        '省份': province_name,
                        '地级市': city,
                        '日期': date_text,
                        '今日价格': price_today,
                        '昨日价格': price_yesterday,
                        '较昨日': change_today,
                        '较上周': change_week
                    }
                    data_list.append(row_data)
                    
                except Exception as e:
                    print(f"  解析行失败: {e}")
                    continue
            
            print(f"✓ 成功爬取 {len(data_list)} 条省级数据")
            return data_list
            
        except Exception as e:
            print(f"解析数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_national_data(self, url):
        """爬取全国豆粕价格数据"""
        print(f"正在爬取全国数据: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 从h3提取日期
            date_text = self._extract_national_date_from_h3(soup)
            
            table = soup.find('table', class_='tabzj')
            if not table:
                print("未找到数据表格")
                return []
            
            data_list = []
            rows = table.find_all('tr')
            current_region = ""
            
            for row in rows:
                cells = row.find_all('td')
                
                if not cells:
                    continue
                
                # 跳过说明行
                if cells[0].get('colspan') and cells[0].get('colspan') == '6':
                    continue
                
                # 6列数据：区域 + 省份 + 价格信息
                if len(cells) == 6:
                    # 检查是否为区域行（有rowspan）
                    if cells[0].get('rowspan'):
                        current_region = cells[0].text.strip()
                        province = cells[1].text.strip()
                        price_today = cells[2].text.strip()
                        price_yesterday = cells[3].text.strip()
                        change_today = cells[4].text.strip()
                        change_week = cells[5].text.strip()
                    else:
                        # 普通数据行
                        province = cells[0].text.strip()
                        price_today = cells[1].text.strip()
                        price_yesterday = cells[2].text.strip()
                        change_today = cells[3].text.strip()
                        change_week = cells[4].text.strip()
                        # 使用之前的区域
                    
                    row_data = {
                        '省份': province,
                        '地级市': current_region,
                        '日期': date_text,
                        '今日价格': price_today,
                        '昨日价格': price_yesterday,
                        '较昨日': change_today,
                        '较上周': change_week
                    }
                    data_list.append(row_data)
                    
                # 5列数据：无区域列
                elif len(cells) == 5 and current_region:
                    province = cells[0].text.strip()
                    price_today = cells[1].text.strip()
                    price_yesterday = cells[2].text.strip()
                    change_today = cells[3].text.strip()
                    change_week = cells[4].text.strip()
                    
                    row_data = {
                        '省份': province,
                        '地级市': current_region,
                        '日期': date_text,
                        '今日价格': price_today,
                        '昨日价格': price_yesterday,
                        '较昨日': change_today,
                        '较上周': change_week
                    }
                    data_list.append(row_data)
            
            print(f"✓ 成功爬取 {len(data_list)} 条全国数据")
            return data_list
            
        except Exception as e:
            print(f"解析数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_national_date_from_h3(self, soup):
        """从h3标签提取全国数据的日期"""
        h3_tag = soup.find('h3')
        if h3_tag:
            title_text = h3_tag.text.strip()
            match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', title_text)
            if match:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        # 从表格中提取日期
        table = soup.find('table', class_='tabzj')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                ths = row.find_all('th')
                for th in ths:
                    text = th.text.strip()
                    match = re.search(r'(\d{2}-\d{2})', text)
                    if match:
                        return f"2026-{match.group(1)}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_province_title_info(self, rows, soup=None):
        """从省级表格提取省份和日期信息"""
        province = ""
        date_text = ""
        
        # 从h3提取
        if soup:
            h3_tag = soup.find('h3')
            if h3_tag:
                title_text = h3_tag.text.strip()
                match = re.search(r'(\d{4}年\d{2}月\d{2}日)([\u4e00-\u9fa5]+?)(?:省|自治区|市|全国)', title_text)
                if match:
                    province = match.group(2)
                    date_str = match.group(1)
                    date_match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', date_str)
                    if date_match:
                        date_text = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    return province, date_text
        
        # 从表格标题提取
        for row in rows:
            if row.find('td') and 'colspan' in str(row):
                title_text = row.find('td').text.strip()
                
                match = re.search(r'^([\u4e00-\u9fa5]+)', title_text)
                if match and not province:
                    province = match.group(1)
                
                match = re.search(r'(\d{4}-\d{2}-\d{2})', title_text)
                if match and not date_text:
                    date_text = match.group(1)
                
                if province and date_text:
                    break
        
        return province, date_text
    
    def _fetch_multiple_urls(self, urls):
        """爬取多个URL的数据并合并"""
        all_data = []
        self.source_urls = []
        self.data_types = []
        self.province_names = []
        
        for url_info in urls:
            if isinstance(url_info, dict):
                url = url_info['url']
                data_type = url_info.get('type', 'auto')
            else:
                url = url_info
                data_type = 'auto'
            
            self.source_urls.append(url)
            
            if data_type == 'province':
                data = self.fetch_province_data(url)
                self.data_types.append('province')
                if data:
                    province = data[0].get('省份', '未知省份')
                    self.province_names.append(province)
            elif data_type == 'national':
                data = self.fetch_national_data(url)
                self.data_types.append('national')
                self.province_names.append('全国')
            else:
                data, data_type, province_name = self.fetch_data_auto(url)
                self.data_types.append(data_type)
                self.province_names.append(province_name)
            
            if data:
                all_data.extend(data)
            else:
                print(f"警告: URL {url} 没有获取到数据")
        
        self.data = all_data
        print(f"\n总计爬取 {len(all_data)} 条数据")
        return all_data
    
    def extract_urls_from_list_page(self, url, max_pages=1):
        """从列表页提取所有详情页的URL"""
        all_detail_urls = []
        
        for page in range(1, max_pages + 1):
            if page == 1:
                current_url = url
            else:
                current_url = re.sub(r'list-68-\d+\.html', f'list-68-{page}.html', url)
            
            print(f"正在提取第 {page} 页: {current_url}")
            
            try:
                response = requests.get(current_url, headers=self.headers, timeout=30)
                response.encoding = 'utf-8'
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                li_tags = soup.find_all('li')
                page_urls = []
                
                for li in li_tags:
                    p_tag = li.find('p', class_='zxleft31')
                    if p_tag:
                        a_tag = p_tag.find('a')
                        if a_tag and a_tag.get('href'):
                            detail_url = a_tag['href']
                            if detail_url.startswith('http'):
                                page_urls.append(detail_url)
                            else:
                                page_urls.append('https://hangqing.zhuwang.com.cn' + detail_url)
                
                print(f"  第 {page} 页提取到 {len(page_urls)} 个链接")
                all_detail_urls.extend(page_urls)
                
            except Exception as e:
                print(f"  请求第 {page} 页失败: {e}")
                continue
        
        all_detail_urls = list(set(all_detail_urls))
        print(f"\n总共提取到 {len(all_detail_urls)} 个唯一详情页URL")
        
        return all_detail_urls
    
    def to_dataframe(self, data_source=None, merge_file=None):
        """将数据转换为DataFrame"""
        if data_source is not None:
            data = data_source
        else:
            data = self.data
            
        if not data:
            print("没有数据可转换")
            return None
        
        new_df = pd.DataFrame(data)
        new_df['创建人'] = self.creator
        new_df['创建时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        columns_order = ['省份', '地级市', '日期', '今日价格', '昨日价格', 
                        '较昨日', '较上周', '创建人', '创建时间']
        available_columns = [col for col in columns_order if col in new_df.columns]
        new_df = new_df[available_columns]
        
        if merge_file and os.path.exists(merge_file):
            print(f"\n正在与已有文件合并: {merge_file}")
            self.df = self.merge_with_existing_data(data, merge_file)
        else:
            if merge_file:
                print(f"\n文件 {merge_file} 不存在，将创建新文件")
            new_df['数据状态'] = '保留'
            if '日期' in new_df.columns:
                new_df['日期'] = pd.to_datetime(new_df['日期'])
                new_df = new_df.sort_values('日期', ascending=False)
                new_df['日期'] = new_df['日期'].dt.strftime('%Y-%m-%d')
            self.df = new_df
        
        return self.df
    
    def merge_with_existing_data(self, new_data, excel_file_path):
        """
        将新数据与已有Excel文件合并
        
        逻辑：
        1. 读取已有文件A（Sheet: 豆粕价格）
        2. 新爬取数据B
        3. 合并去重后生成C
        4. 输出三个Sheet：A原数据、B新增数据、C合并去重数据
        5. 去重依据：【省份、地级市、日期、今日价格、昨日价格、较昨日、较上周】
        """
        try:
            import pandas as pd
            from datetime import datetime
            import os
            
            # 1. 读取已有数据A（Sheet: 豆粕价格）
            xls = pd.ExcelFile(excel_file_path)
            
            # 优先读取"豆粕价格"Sheet
            if '豆粕价格' in xls.sheet_names:
                df_a = pd.read_excel(excel_file_path, sheet_name='豆粕价格')
                print(f"📖 已读取现有数据A: {len(df_a)} 条记录 (Sheet: 豆粕价格)")
            else:
                # 如果不存在，读取第一个Sheet
                df_a = pd.read_excel(excel_file_path, sheet_name=0)
                print(f"📖 已读取现有数据A: {len(df_a)} 条记录 (Sheet: {xls.sheet_names[0]})")
            
            # 2. 创建新数据B的DataFrame
            df_b = pd.DataFrame(new_data)
            print(f"📥 新爬取数据B: {len(df_b)} 条记录")
            
            # 3. 统一列名，确保所有列都存在
            columns_order = ['省份', '地级市', '日期', '今日价格', '昨日价格', 
                            '较昨日', '较上周', '创建人', '创建时间']
            for col in columns_order:
                if col not in df_a.columns:
                    df_a[col] = ''
                if col not in df_b.columns:
                    df_b[col] = ''
            
            # 4. 确保日期格式一致
            if '日期' in df_b.columns:
                df_b['日期'] = pd.to_datetime(df_b['日期'], errors='coerce')
            if '日期' in df_a.columns:
                df_a['日期'] = pd.to_datetime(df_a['日期'], errors='coerce')
            
            # 5. 确保创建时间格式一致
            if '创建时间' in df_b.columns:
                df_b['创建时间'] = pd.to_datetime(df_b['创建时间'], errors='coerce')
            if '创建时间' in df_a.columns:
                df_a['创建时间'] = pd.to_datetime(df_a['创建时间'], errors='coerce')
            
            # 6. 合并A和B
            df_combined = pd.concat([df_a, df_b], ignore_index=True)
            print(f"📊 合并后总记录数: {len(df_combined)} 条")
            
            # 7. 去重依据字段（不包含创建人、创建时间）
            duplicate_cols = ['省份', '地级市', '日期', '今日价格', '昨日价格', '较昨日', '较上周']
            
            # 去重：保留第一次出现的记录（即A中的数据优先）
            df_c = df_combined.drop_duplicates(subset=duplicate_cols, keep='first')
            
            # 8. 统计结果
            duplicate_count = len(df_combined) - len(df_c)
            print(f"✅ 合并完成!")
            print(f"   - A原数据: {len(df_a)} 条")
            print(f"   - B新增数据: {len(df_b)} 条")
            print(f"   - C合并去重后: {len(df_c)} 条")
            print(f"   - 去除重复: {duplicate_count} 条")
            
            # 9. 生成输出文件名
            base_name = os.path.splitext(os.path.basename(excel_file_path))[0]
            output_dir = os.path.dirname(excel_file_path)
            output_file = os.path.join(output_dir, f"{base_name}_合并结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            # 10. 写入Excel，三个Sheet
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Sheet1: A原数据
                df_a.to_excel(writer, sheet_name='A原数据', index=False)
                # Sheet2: B新增数据
                df_b.to_excel(writer, sheet_name='B新增数据', index=False)
                # Sheet3: C合并去重数据
                df_c.to_excel(writer, sheet_name='C合并去重数据', index=False)
            
            print(f"   - 输出文件: {output_file}")
            
            return output_file, df_a, df_b, df_c
            
        except Exception as e:
            print(f"❌ 合并数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None
    
    def save_to_excel(self, filename=None, merge_file=None):
        """保存数据到Excel文件，包含多个Sheet"""
        if merge_file and os.path.exists(merge_file):
            save_filename = merge_file
            print(f"将数据合并到已有文件: {save_filename}")
        else:
            if filename is None:
                filename = f"豆粕价格_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if os.path.dirname(filename):
                if not filename.startswith(self.save_dir):
                    filename = os.path.basename(filename)
                    save_filename = os.path.join(self.save_dir, filename)
                else:
                    save_filename = filename
            else:
                save_filename = os.path.join(self.save_dir, filename)
            
            if merge_file:
                print(f"文件 {merge_file} 不存在，创建新文件: {save_filename}")
        
        os.makedirs(self.save_dir, exist_ok=True)
        
        if not save_filename.endswith('.xlsx'):
            save_filename += '.xlsx'
        
        if self.df is None:
            if not self.data:
                print("没有数据可保存")
                return False
            self.to_dataframe(merge_file=merge_file)
        
        if self.df is None or len(self.df) == 0:
            print("没有数据可保存")
            return False
        
        try:
            with pd.ExcelWriter(save_filename, engine='openpyxl') as writer:
                # Sheet1: 全部数据
                self.df.to_excel(writer, sheet_name='全部数据', index=False)
                
                # Sheet2: 保留数据
                keep_df = self.df[self.df['数据状态'] == '保留'].copy() if '数据状态' in self.df.columns else self.df.copy()
                if not keep_df.empty:
                    keep_df.to_excel(writer, sheet_name='保留_最新数据', index=False)
                
                # Sheet3: 历史数据
                history_df = self.df[self.df['数据状态'] == '历史'].copy() if '数据状态' in self.df.columns else pd.DataFrame()
                if not history_df.empty:
                    history_df.to_excel(writer, sheet_name='历史_需归档', index=False)
                
                # Sheet4: 统计信息
                stats_data = self._get_stats_data()
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='统计信息', index=False)
                
                self._adjust_column_width(writer, '全部数据')
                if not keep_df.empty:
                    self._adjust_column_width(writer, '保留_最新数据')
                if not history_df.empty:
                    self._adjust_column_width(writer, '历史_需归档')
            
            print(f"\n✓ 数据已成功保存到: {save_filename}")
            print(f"✓ 共保存 {len(self.df)} 条记录")
            return True
            
        except Exception as e:
            print(f"保存Excel文件失败: {e}")
            return False
    
    def _get_stats_data(self):
        """获取统计信息数据"""
        if self.df is None:
            return {'统计项': ['无数据'], '值': ['0']}
        
        stats = {
            '统计项': [
                '总记录数',
                '保留记录数',
                '历史记录数',
                '省份数量',
                '日期范围',
                '创建人',
                '创建时间'
            ],
            '值': [
                str(len(self.df)),
                str(len(self.df[self.df['数据状态'] == '保留']) if '数据状态' in self.df.columns else len(self.df)),
                str(len(self.df[self.df['数据状态'] == '历史']) if '数据状态' in self.df.columns else 0),
                str(self.df['省份'].nunique() if '省份' in self.df.columns else 0),
                f"{self.df['日期'].min()} ~ {self.df['日期'].max()}" if '日期' in self.df.columns and not self.df.empty else 'N/A',
                self.creator,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        return stats
    
    def _adjust_column_width(self, writer, sheet_name):
        """调整Excel列宽"""
        worksheet = writer.sheets[sheet_name]
        for column in self.df.columns:
            column_width = max(self.df[column].astype(str).map(len).max(), len(column)) + 4
            col_idx = self.df.columns.get_loc(column)
            worksheet.column_dimensions[get_column_letter(col_idx + 1)].width = min(column_width, 30)
    
    def get_latest_file(self):
        """获取最新的豆粕价格文件"""
        files = self.get_excel_files()
        if not files:
            return None
        return files[0]
    
    def get_all_files(self):
        """获取所有豆粕价格文件"""
        return self.get_excel_files()
    
    def run_from_list_page(self, list_url, max_pages=1, filename=None, merge_file=None):
        """从列表页爬取所有详情页数据并合并保存（主入口方法）"""
        print("=" * 60)
        print("豆粕价格数据爬虫 - 从列表页批量爬取")
        print("=" * 60)
        print(f"列表页URL: {list_url}")
        print(f"最大页数: {max_pages}")
        print(f"创建人: {self.creator}")
        print(f"📁 保存目录: {self.save_dir}")
        if merge_file:
            print(f"合并文件: {merge_file}")
        print("-" * 60)
        
        detail_urls = self.extract_urls_from_list_page(list_url, max_pages)
        
        if not detail_urls:
            print("✗ 未提取到任何详情页URL")
            return False
        
        print(f"\n开始爬取 {len(detail_urls)} 个详情页...")
        print("-" * 60)
        
        self._fetch_multiple_urls(detail_urls)
        
        if not self.data:
            print("✗ 没有爬取到任何数据")
            return False
        
        self.to_dataframe(merge_file=merge_file)
        
        if merge_file and os.path.exists(merge_file):
            success = self.save_to_excel(merge_file=merge_file)
        else:
            if filename is None:
                filename = f"豆粕价格_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if not os.path.dirname(filename):
                filename = os.path.join(self.save_dir, filename)
            success = self.save_to_excel(filename=filename)
        
        if success:
            print("\n" + "=" * 60)
            print("爬取完成！")
            print("=" * 60)
        else:
            print("\n✗ 保存失败")
        
        return success

