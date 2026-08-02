# components/navigation_cards.py
import streamlit as st
from typing import List, Dict, Optional, Callable

class NavigationCards:
    """
    导航卡片组件类
    用于创建可点击的导航卡片网格，支持跳转到指定页面
    
    使用示例:
        cards = NavigationCards()
        cards.add_card("数据概览", "📊", "查看数据总览与统计", "data_analysis/1_data_overview.py")
        cards.add_card("数据可视化", "📈", "图表与可视化分析", "data_analysis/2_data_visualization.py")
        cards.render(cols=4)
    """
    
    def __init__(self, title: str = None, subtitle: str = None):
        """
        初始化导航卡片组件
        
        Args:
            title: 页面标题（可选）
            subtitle: 页面副标题（可选）
        """
        self.cards: List[Dict] = []
        self.title = title
        self.subtitle = subtitle
        self._header_rendered = False  # ✅ 新增：标记标题是否已渲染
        
        # 颜色方案映射
        self.color_schemes = {
            'green': 'background: linear-gradient(135deg, #f6ffed, #e8f5e9);',
            'orange': 'background: linear-gradient(135deg, #fff7e6, #fff1d6);',
            'blue': 'background: linear-gradient(135deg, #e8f4fd, #d6e8f7);',
            'purple': 'background: linear-gradient(135deg, #f9f0ff, #efdbff);',
            'red': 'background: linear-gradient(135deg, #fff1f0, #ffd6d6);',
            'gray': 'background: linear-gradient(135deg, #f5f5f5, #e8e8e8);',
            'white': 'background: white;'
        }
    
    def add_card(
        self,
        title: str,
        icon: str,
        description: str,
        page_path: str,
        color_scheme: str = 'white',
        button_text: str = None
    ) -> 'NavigationCards':
        """
        添加一个导航卡片
        
        Args:
            title: 卡片标题
            icon: Emoji 图标
            description: 卡片描述文字
            page_path: 目标页面文件路径
            color_scheme: 颜色方案 ('green', 'orange', 'blue', 'purple', 'red', 'gray', 'white')
            button_text: 按钮文字（默认使用 "进入 {icon} {title}"）
        
        Returns:
            self (支持链式调用)
        """
        self.cards.append({
            'title': title,
            'icon': icon,
            'description': description,
            'page_path': page_path,
            'color_scheme': color_scheme,
            'button_text': button_text or f"进入 {icon} {title}"
        })
        return self
    
    def add_cards_from_list(self, card_list: List[Dict]) -> 'NavigationCards':
        """
        从列表批量添加卡片
        
        Args:
            card_list: 卡片字典列表，每个字典需包含 title, icon, description, page_path
        
        Returns:
            self (支持链式调用)
        """
        for card in card_list:
            self.add_card(
                title=card['title'],
                icon=card['icon'],
                description=card.get('description', ''),
                page_path=card['page_path'],
                color_scheme=card.get('color_scheme', 'white'),
                button_text=card.get('button_text', None)
            )
        return self
    
    def _get_background(self, color_scheme: str) -> str:
        """获取背景样式"""
        return self.color_schemes.get(color_scheme, 'background: blue;')
    
    def render_header(self, title: str = None, subtitle: str = None):
        """
        ✅ 新增：独立渲染标题（只调用一次）
        
        Args:
            title: 页面标题（如果不传则使用初始化时的标题）
            subtitle: 页面副标题（如果不传则使用初始化时的副标题）
        """
        if self._header_rendered:
            return  # 已经渲染过，不再重复渲染
        
        display_title = title or self.title
        display_subtitle = subtitle or self.subtitle
        
        if display_title:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px 0 10px 0;">
                <h1 style="font-size: 36px; color: #1a1a1a;">{display_title}</h1>
                {f'<p style="color: #888; font-size: 16px;">{display_subtitle}</p>' if display_subtitle else ''}
            </div>
            """, unsafe_allow_html=True)
            st.divider()
            self._header_rendered = True
    
    def render_section_title(self, section_title: str):
        """
        ✅ 新增：渲染分类标题（每个分组调用一次）
        
        Args:
            section_title: 分类标题，如 "📊 数据分析"
        """
        st.markdown(f"""
        <div style="
            font-size: 20px;
            font-weight: bold;
            color: #1a1a1a;
            margin: 20px 0 10px 0;
            padding-left: 12px;
            border-left: 4px solid #2E7D32;
        ">
            {section_title}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_card(self, card: Dict, col, card_width: str = "100%"):
        """渲染单个卡片"""
        with col:
            bg_style = self._get_background(card['color_scheme'])
            
            # 卡片样式 - 添加 width 和 max-width 控制
            st.markdown(f"""
            <div style="
                border: 1px solid #e8e8e8;
                border-radius: 12px;
                padding: 20px 16px;
                text-align: center;
                {bg_style}
                width: {card_width};
                max-width: {card_width};
                height: 140px;
                margin: 0 auto;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                transition: all 0.3s;
            ">
                <div style="font-size: 40px; line-height: 1.2;">{card['icon']}</div>
                <div style="font-size: 16px; font-weight: bold; color: #1a1a1a; margin-top: 8px;">{card['title']}</div>
                <div style="font-size: 12px; color: #999; margin-top: 4px;">{card['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 按钮
            if st.button(
                card['button_text'],
                key=f"nav_btn_{hash(card['page_path'])}_{len(self.cards)}", # 使用哈希值作为 key，避免重复
                # use_container_width=False
                width='stretch',
                
            ):
                self._navigate_to(card['page_path'])

 
    
    def _navigate_to(self, page_path: str):
        """跳转到指定页面"""
        try:
            st.switch_page(page_path)
        except Exception:
            st.query_params["page"] = page_path
            st.rerun()
    
    def render(self, cols: int = 4, section_title: str = None, auto_header: bool = True, card_width: str = "100%"):
        """
        渲染所有导航卡片
        
        Args:
            cols: 每行显示的卡片数量
            section_title: 分类标题（可选），如 "📊 数据分析"
            auto_header: 是否自动渲染标题（如果标题未渲染过）
            card_width: 卡片宽度，支持 "100%", "95%", "90%", "85%", "80%", "300px", "auto" 等
                        推荐值: "100%" (默认), "95%", "90%", "85%", "80%"
        """
        if not self.cards:
            st.warning("没有导航卡片，请先使用 add_card() 添加卡片")
            return
        
        # ✅ 如果启用自动标题且标题未渲染，则渲染标题
        if auto_header and not self._header_rendered and self.title:
            self.render_header()
        
        # ✅ 如果有分类标题，先渲染
        if section_title:
            self.render_section_title(section_title)
        
        # 渲染卡片网格
        for i in range(0, len(self.cards), cols):
            row_cols = st.columns(cols)
            for j, col in enumerate(row_cols):
                idx = i + j
                if idx < len(self.cards):
                    self._render_card(self.cards[idx], col, card_width)
    
    def clear(self):
        """
        ✅ 新增：清空卡片列表（用于不同分组）
        
        Returns:
            self (支持链式调用)
        """
        self.cards = []
        return self
    
    def render_sidebar(self, brand_icon: str = "🐮", brand_name: str = "桂柳牧业"):
        """在侧边栏渲染品牌信息"""
        st.sidebar.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f6ffed, #e8f5e9);
            border-radius: 12px;
            padding: 20px 16px;
            border: 1px solid #b7eb8f;
            text-align: center;
        ">
            <div style="font-size: 32px;">{brand_icon}</div>
            <div style="font-size: 16px; font-weight: bold; color: #2E7D32;">{brand_name}</div>
            <div style="font-size: 13px; color: #666; margin-top: 4px;">欢迎回来！</div>
            <hr style="margin: 12px 0; border-color: #d9d9d9;">
            <div style="font-size: 12px; color: #999;">点击上方按钮进入对应模块</div>
        </div>
        """, unsafe_allow_html=True)


class SimpleCards:
    """
    简化版导航卡片（更轻量，适合快速使用）
    
    使用示例:
        cards = SimpleCards()
        cards.add("数据概览", "📊", "查看数据总览", "data_analysis/1_data_overview.py")
        cards.render()
    """
    
    def __init__(self):
        self.data: List[tuple] = []
    
    def add(self, title: str, icon: str, desc: str, path: str) -> 'SimpleCards':
        """添加卡片 (元组格式)"""
        self.data.append((title, icon, desc, path))
        return self
    
    def render(self, cols: int = 4, card_width: str = "100%"):
        """渲染卡片
        
        Args:
            cols: 每行显示的卡片数量
            card_width: 卡片宽度，支持 "100%", "95%", "90%", "85%", "80%", "300px", "auto" 等
        """
        for i in range(0, len(self.data), cols):
            row_cols = st.columns(cols)
            for j, col in enumerate(row_cols):
                idx = i + j
                if idx < len(self.data):
                    title, icon, desc, path = self.data[idx]
                    with col:
                        st.markdown(f"""
                        <div style="
                            border: 1px solid #e8e8e8;
                            border-radius: 12px;
                            padding: 20px 16px;
                            text-align: center;
                            background: white;
                            width: {card_width};
                            max-width: {card_width};
                            height: 140px;
                            margin: 0 auto;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                        ">
                            <div style="font-size: 40px;">{icon}</div>
                            <div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">{title}</div>
                            <div style="font-size: 12px; color: #999;">{desc}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"进入 {icon} {title}", key=f"simple_{idx}", use_container_width=True):
                            try:
                                st.switch_page(path)
                            except Exception:
                                st.query_params["page"] = path
                                st.rerun()