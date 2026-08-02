import requests
from bs4 import BeautifulSoup
import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class MaltodextrinScraper:
    """
    农副产品报价爬虫类
    从 https://www.100ppi.com 爬取各类农副产品报价数据
    """
    
    def __init__(self, 
                 base_url: str = 'https://www.100ppi.com',
                 delay: float = 1.5,
                 timeout: int = 10,
                 user_agent: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            base_url: 网站基础URL
            delay: 请求间隔（秒）
            timeout: 请求超时（秒）
            user_agent: 自定义User-Agent
        """
        self.base_url = base_url
        self.delay = delay
        self.timeout = timeout
        self.data = []
        self.last_error = None
        
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.100ppi.com/',
        }
        
        # ✅ 所有分类列表
        self.categories = ['能源', '有色', '钢铁', '化工', '橡塑', '纺织', '建材', '农副']
    
    def _build_full_url(self, href: str) -> str:
        """
        将相对路径转换为完整URL
        
        Args:
            href: 相对路径（如 plist-1-1090-1.html）
            
        Returns:
            完整URL（如 https://www.100ppi.com/mprice/plist-1-1090-1.html）
        """
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return self.base_url + href
        else:
            if href.startswith('plist-'):
                return self.base_url + '/mprice/' + href
            else:
                return self.base_url + '/' + href
    
    def extract_links(self, category_url: str = '/mprice/') -> List[Tuple[str, str]]:
        """
        从农副分类页面提取所有产品链接（已废弃，请使用 extract_all_links）
        
        Args:
            category_url: 分类页面URL，默认为 /mprice/
            
        Returns:
            产品列表，每个元素为 (产品名称, 完整URL)
        """
        return self.extract_all_links()
    
    def extract_all_links(self, categories: Optional[List[str]] = None) -> Dict[str, List[Tuple[str, str]]]:
        """
        从所有分类页面提取所有产品链接
        
        Args:
            categories: 要提取的分类列表，默认为所有分类
            
        Returns:
            分类字典，键为分类名称，值为该分类下的产品列表 [(产品名称, 完整URL)]
        """
        if categories is None:
            categories = self.categories
        
        all_results = {}
        total_categories = len(categories)
        
        print(f'开始提取 {total_categories} 个分类的产品链接...')
        
        for idx, category in enumerate(categories, 1):
            print(f'[{idx}/{total_categories}] 正在提取 "{category}" 分类...')
            links = self._extract_category_links(category)
            all_results[category] = links
            print(f'  ✅ 找到 {len(links)} 个产品')
            
            # 分类之间增加延迟
            if idx < total_categories:
                time.sleep(0.5)
        
        return all_results
    
    def _extract_category_links(self, category_name: str) -> List[Tuple[str, str]]:
        """
        提取单个分类的产品链接
        
        Args:
            category_name: 分类名称（如 '农副'）
            
        Returns:
            产品列表 [(产品名称, 完整URL)]
        """
        url = self.base_url + '/mprice/'
        product_links = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                self.last_error = f'请求失败，状态码: {response.status_code}'
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找包含指定分类的li
            for li in soup.find_all('li'):
                b_tag = li.find('b')
                if b_tag and category_name in b_tag.get_text():
                    tylist = li.find('div', class_='tylist1')
                    if tylist:
                        for a_tag in tylist.find_all('a', href=True):
                            name = a_tag.get_text().strip()
                            href = a_tag['href']
                            if name and href:
                                full_url = self._build_full_url(href)
                                product_links.append((name, full_url))
                    break
            
            # 如果没找到，使用备用方法
            if not product_links:
                product_links = self._extract_links_fallback(category_name)
            
            return product_links
            
        except Exception as e:
            print(f'提取 "{category_name}" 链接失败: {e}')
            return []
    
    def _extract_links_fallback(self, category_name: str) -> List[Tuple[str, str]]:
        """
        备用提取方法：在页面中搜索包含分类名称的链接
        """
        url = self.base_url + '/mprice/'
        product_links = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 搜索所有包含 plist-1- 的链接
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if 'plist-1-' in href:
                    name = a_tag.get_text().strip()
                    if name and name not in [p[0] for p in product_links]:
                        full_url = self._build_full_url(href)
                        product_links.append((name, full_url))
            
            return product_links
            
        except Exception as e:
            print(f'备用提取失败: {e}')
            return []
    
    def get_all_product_names(self, categories: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        获取所有分类下的产品名称列表
        
        Args:
            categories: 要提取的分类列表，默认为所有分类
            
        Returns:
            分类字典，键为分类名称，值为该分类下的产品名称列表
        """
        results = self.extract_all_links(categories)
        return {category: [name for name, _ in links] for category, links in results.items()}
    
    def get_all_product_urls(self, categories: Optional[List[str]] = None) -> Dict[str, List[Tuple[str, str]]]:
        """
        获取所有分类下的产品链接（完整URL）
        
        Args:
            categories: 要提取的分类列表，默认为所有分类
            
        Returns:
            分类字典，键为分类名称，值为该分类下的产品列表 [(产品名称, 完整URL)]
        """
        return self.extract_all_links(categories)
    
    def _parse_page(self, html_content: str) -> List[Dict[str, str]]:
        """解析单页HTML，提取表格数据"""
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='lp-table')
        if not table:
            return []
        
        rows = table.find_all('tr')
        data_list = []
        
        for row in rows[1:]:  # 跳过表头
            cells = row.find_all('td')
            if len(cells) < 8:
                continue
            
            # 商品名称
            product_name_tag = cells[0].find('a')
            product_name = product_name_tag.text.strip() if product_name_tag else ''
            
            # 规格
            spec = cells[1].text.strip()
            
            # 品牌/产地
            brand = cells[2].text.strip()
            
            # 报价
            price = cells[3].text.strip()
            
            # 报价类型
            price_type = cells[4].text.strip()
            
            # 交货地
            delivery_place = cells[5].text.strip()
            
            # 交易商
            trader_tag = cells[6].find('a')
            trader = trader_tag.text.strip() if trader_tag else cells[6].text.strip()
            
            # 发布时间
            pub_time = cells[7].text.strip()

            if price:
                # 以"元"为分割
                if '元' in price:
                    parts = price.split('元', 1)
                    price_value = parts[0].strip()  # "3600"
                    price_unit = '元' + parts[1].strip() if len(parts) > 1 else '元'  # "元/吨"
                else:
                    # 如果没有"元"，尝试其他常见分割
                    import re
                    match = re.match(r'^([\d.]+)\s*(.+)$', price)
                    if match:
                        price_value = match.group(1)
                        price_unit = match.group(2)
                    else:
                        price_value = price
                        price_unit = ""

            data_list.append({
                '商品名称': product_name,
                '规格': spec,
                '品牌/产地': brand,
                # '报价': price,
                '报价数值': price_value,   # ✅ 改为报价数值
                '报价单位': price_unit,     # ✅ 改为报价单位
                '报价类型': price_type,
                '交货地': delivery_place,
                '交易商': trader,
                '发布时间': pub_time
            })
        
        return data_list
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """获取单页HTML（直接使用完整URL）"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                return response.text
            else:
                self.last_error = f'状态码: {response.status_code}'
                return None
                
        except requests.RequestException as e:
            self.last_error = str(e)
            return None
    
    def scrape(self, 
               product_url: str,
               max_pages: int = 10,
               start_page: int = 1, 
               progress_callback=None) -> 'MaltodextrinScraper':
        """
        执行爬取
        
        Args:
            product_url: 产品列表页完整URL（如 https://www.100ppi.com/mprice/plist-1-1090-1.html）
            max_pages: 最大页数
            start_page: 起始页码
            progress_callback: 进度回调函数，接收 (当前页, 总页数, 当前页数据条数)
            
        Returns:
            self，支持链式调用
        """
        self.data = []
        total_pages = max_pages
        
        # 处理URL，提取基础路径
        if '-1.html' in product_url:
            base_path = product_url.replace('-1.html', '')
        else:
            base_path = product_url
        
        for idx, page in enumerate(range(start_page, start_page + max_pages), 1):
            # 构建分页URL
            if page == 1:
                page_url = product_url
            else:
                if '-1.html' in product_url:
                    page_url = product_url.replace('-1.html', f'-{page}.html')
                else:
                    page_url = f"{base_path}-{page}.html"
            
            html = self._fetch_page(page_url)
            page_data = []
            if html:
                page_data = self._parse_page(html)
                self.data.extend(page_data)
            
            # 调用进度回调
            if progress_callback:
                progress_callback(idx, total_pages, len(page_data))
            
            if page < start_page + max_pages - 1:
                time.sleep(self.delay)
        
        return self
    
    def scrape_multiple(self, 
                        product_urls: List[Tuple[str, str]],
                        max_pages: int = 10,
                        start_page: int = 1,
                        progress_callback=None) -> 'MaltodextrinScraper':
        """
        爬取多个物料
        
        Args:
            product_urls: 产品列表 [(产品名称, 完整URL)]
            max_pages: 每个物料的最大页数
            start_page: 起始页码
            progress_callback: 进度回调函数，接收 (当前物料索引, 总物料数, 当前物料名称, 当前页数据条数)
            
        Returns:
            self，支持链式调用
        """
        self.data = []
        total_products = len(product_urls)
        
        for idx, (product_name, product_url) in enumerate(product_urls, 1):
            # 爬取当前物料
            scraper = MaltodextrinScraper(base_url=self.base_url, delay=self.delay, timeout=self.timeout)
            scraper.scrape(
                product_url=product_url,
                max_pages=max_pages,
                start_page=start_page
            )
            raw_data = scraper.get_data()
            
            if raw_data:
                # 添加物料名称字段
                for row in raw_data:
                    row['物料名称'] = product_name
                self.data.extend(raw_data)
            
            # 调用进度回调
            if progress_callback:
                progress_callback(idx, total_products, product_name, len(raw_data))
            
            if idx < total_products:
                time.sleep(self.delay)
        
        return self
    
    def get_data(self) -> List[Dict[str, str]]:
        """获取已爬取的数据"""
        return self.data
    
    def get_count(self) -> int:
        """获取数据条数"""
        return len(self.data)
    
    def get_last_error(self) -> Optional[str]:
        """获取最后一次错误信息"""
        return self.last_error
    
    def clear(self) -> 'MaltodextrinScraper':
        """清空数据"""
        self.data = []
        self.last_error = None
        return self
    
    def to_csv(self, filename: Optional[str] = None, encoding: str = 'utf-8-sig') -> str:
        """保存为CSV文件"""
        if not self.data:
            print('没有数据可保存')
            return ''
        
        if filename is None:
            filename = f'报价数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=self.data[0].keys())
            writer.writeheader()
            writer.writerows(self.data)
        
        return filename
    
    def to_json(self, filename: Optional[str] = None) -> str:
        """保存为JSON文件"""
        if not self.data:
            print('没有数据可保存')
            return ''
        
        if filename is None:
            filename = f'报价数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def filter_by(self, **kwargs) -> List[Dict[str, str]]:
        """按条件过滤数据"""
        if not self.data:
            return []
        
        result = self.data.copy()
        for key, value in kwargs.items():
            result = [item for item in result if item.get(key) == value]
        return result
    
    def get_summary(self) -> Dict:
        """获取数据摘要"""
        if not self.data:
            return {'总条数': 0}
        
        summary = {
            '总条数': len(self.data),
            '字段': list(self.data[0].keys()),
        }
        
        # 统计交货地分布（前10）
        places = {}
        for item in self.data:
            place = item.get('交货地', '未知')
            places[place] = places.get(place, 0) + 1
        
        sorted_places = sorted(places.items(), key=lambda x: x[1], reverse=True)[:10]
        summary['交货地分布'] = dict(sorted_places)
        
        # 统计物料分布
        if '物料名称' in self.data[0]:
            products = {}
            for item in self.data:
                name = item.get('物料名称', '未知')
                products[name] = products.get(name, 0) + 1
            summary['物料分布'] = dict(sorted(products.items(), key=lambda x: x[1], reverse=True))
        
        return summary

    def merge_excel_files(self, file_a: str, file_b: str, output_file: str = None) -> str:
        """
        合并两个Excel文件的数据
        
        Args:
            file_a: 第一个Excel文件路径（原数据）
            file_b: 第二个Excel文件路径（新增数据）
            output_file: 输出文件路径，默认自动生成
            
        Returns:
            输出文件路径
        """
        import pandas as pd
        from datetime import datetime
        import os
        
        # 读取两个Excel文件
        df_a = pd.read_excel(file_a)
        df_b = pd.read_excel(file_b)
        
        # 确定去重依据的字段（排除创建人和创建时间）
        exclude_cols = ['创建人', '创建时间']
        duplicate_cols = [col for col in df_a.columns if col not in exclude_cols]
        
        # 合并两个DataFrame
        df_combined = pd.concat([df_a, df_b], ignore_index=True)
        
        # 去重（不根据创建人和创建时间）
        df_unique = df_combined.drop_duplicates(subset=duplicate_cols, keep='first')
        
        # 生成输出文件名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(file_a))[0]
            output_file = f"{base_name}_合并结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 写入Excel，三个sheet
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_a.to_excel(writer, sheet_name='原数据', index=False)
            df_b.to_excel(writer, sheet_name='新增数据', index=False)
            df_unique.to_excel(writer, sheet_name='合并去重数据', index=False)
        
        # 返回统计信息
        print(f"✅ 合并完成！")
        print(f"   📁 原数据：{len(df_a)} 条")
        print(f"   📁 新增数据：{len(df_b)} 条")
        print(f"   📁 合并去重后：{len(df_unique)} 条")
        print(f"   📁 去除重复：{len(df_combined) - len(df_unique)} 条")
        print(f"   📁 输出文件：{output_file}")
        
        return output_file