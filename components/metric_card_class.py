# components/metric_card_class.py
import streamlit as st


class MetricCard:
    """自定义指标卡片组件（左右分布）"""
    
    def __init__(self, label: str, icon: str, current_val: float, 
                 prev_val: float, last_year_val: float, 
                 unit: str = "%", decimal: int = 1, border: bool = True):
        self.label = label
        self.icon = icon
        self.current_val = current_val
        self.prev_val = prev_val
        self.last_year_val = last_year_val
        self.unit = unit # 单位
        self.decimal = decimal
        self.border = border
    
    def render(self, col):
        """在指定的列中渲染卡片"""
        with col:
            delta_mom = self.current_val - self.prev_val
            delta_yoy = self.current_val - self.last_year_val
            
            mom_color = "#52c41a" if delta_mom >= 0 else "#ff4d4f"
            yoy_color = "#52c41a" if delta_yoy >= 0 else "#ff4d4f"
            
            format_str = f"{{:.{self.decimal}f}}"
            
            # 带正负号
            mom_str = f"{'+' if delta_mom >= 0 else '-'}{format_str.format(abs(delta_mom))}"
            yoy_str = f"{'+' if delta_yoy >= 0 else '-'}{format_str.format(abs(delta_yoy))}"
            # 带箭头
            mom_jiantou = f"{'↑' if delta_mom > 0 else '↓' if delta_mom < 0 else '→'}"
            yoy_jiantou = f"{'↑' if delta_yoy > 0 else '↓' if delta_yoy < 0 else '→'}"

            st.markdown(f"""
            <div style="
                border: {'1px solid #e0e0e0' if self.border else 'none'};
                border-radius: 8px;
                padding: 16px 20px;
                background: white;
            ">
                <div style="color: #666; font-size: 14px;">{self.icon} {self.label}</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 32px; font-weight: bold; color: #1a1a1a;">{format_str.format(self.current_val)}</span>
                        <span style="font-size: 26px; font-weight: bold; color: #1a1a1a;">{self.unit}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {mom_color}; font-size: 14px;">
                            环比：<span style="font-weight: bold;">{mom_str}{self.unit}{mom_jiantou}</span>
                        </div>
                        <div style="color: {yoy_color}; font-size: 14px;">
                            同比：<span style="font-weight: bold;">{yoy_str}{self.unit}{yoy_jiantou}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


class MetricCardDown:
    """
    自定义指标卡片组件类（上下分布）
    
    使用示例:
        card = MetricCardDown(
            label="成活率",
            icon="🐖",
            current_val=96.0,
            prev_val=95.8,
            last_year_val=95.0,
            unit="%",
            decimal=1
        )
        card.render(col1)
    """
    
    def __init__(
        self,
        label: str,
        icon: str,
        current_val: float,
        prev_val: float = None, # type: ignore
        last_year_val: float = None, # type: ignore
        unit: str = "%",
        decimal: int = 1,
        border: bool = True,
        mom_label: str = "较上月",
        yoy_label: str = "较去年"
    ):
        self.label = label
        self.icon = icon
        self.current_val = current_val
        self.prev_val = prev_val if prev_val is not None else current_val
        self.last_year_val = last_year_val if last_year_val is not None else current_val
        self.unit = unit
        self.decimal = decimal
        self.border = border
        self.mom_label = mom_label
        self.yoy_label = yoy_label
        
        self.delta_mom = self.current_val - self.prev_val
        self.delta_yoy = self.current_val - self.last_year_val
        
        self.mom_color = "#52c41a" if self.delta_mom >= 0 else "#ff4d4f"
        self.yoy_color = "#52c41a" if self.delta_yoy >= 0 else "#ff4d4f"
        
        self.format_str = f"{{:.{self.decimal}f}}"
    
    def render(self, col):
        """在指定的列中渲染卡片"""
        with col:
            border_style = "border: 1px solid #e0e0e0;" if self.border else ""
            
            # 带正负号
            mom_str = f"{'+' if self.delta_mom >= 0 else '-'}{self.format_str.format(abs(self.delta_mom))}"
            yoy_str = f"{'+' if self.delta_yoy >= 0 else '-'}{self.format_str.format(abs(self.delta_yoy))}"
            
            st.markdown(f"""
            <div style="
                {border_style}
                border-radius: 8px;
                padding: 16px 20px;
                background: white;
            ">
                <div style="color: #666; font-size: 14px;">{self.icon} {self.label}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1a1a1a;">
                    {self.format_str.format(self.current_val)}{self.unit}
                </div>
                <div style="color: {self.mom_color}; font-size: 16px; margin-bottom: 8px;">
                    {mom_str}{self.unit} {self.mom_label}
                </div>
                <div style="display: flex; gap: 20px; border-top: 1px solid #f0f0f0; padding-top: 8px;">
                    <div>
                        <span style="color: #999; font-size: 12px;">📊 环比（{self.mom_label}）</span><br>
                        <span style="color: {self.mom_color}; font-size: 16px; font-weight: bold;">
                            {mom_str}{self.unit}
                        </span>
                    </div>
                    <div>
                        <span style="color: #999; font-size: 12px;">📈 同比（{self.yoy_label}）</span><br>
                        <span style="color: {self.yoy_color}; font-size: 16px; font-weight: bold;">
                            {yoy_str}{self.unit}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_html(self):
        """仅返回 HTML 字符串（不自动渲染）"""
        border_style = "border: 1px solid #e0e0e0;" if self.border else ""
        
        mom_str = f"{'+' if self.delta_mom >= 0 else '-'}{self.format_str.format(abs(self.delta_mom))}"
        yoy_str = f"{'+' if self.delta_yoy >= 0 else '-'}{self.format_str.format(abs(self.delta_yoy))}"
        
        return f"""
        <div style="
            {border_style}
            border-radius: 8px;
            padding: 16px 20px;
            background: white;
        ">
            <div style="color: #666; font-size: 14px;">{self.icon} {self.label}</div>
            <div style="font-size: 32px; font-weight: bold; color: #1a1a1a;">
                {self.format_str.format(self.current_val)}{self.unit}
            </div>
            <div style="color: {self.mom_color}; font-size: 16px; margin-bottom: 8px;">
                {mom_str}{self.unit} {self.mom_label}
            </div>
            <div style="display: flex; gap: 20px; border-top: 1px solid #f0f0f0; padding-top: 8px;">
                <div>
                    <span style="color: #999; font-size: 12px;">📊 环比（{self.mom_label}）</span><br>
                    <span style="color: {self.mom_color}; font-size: 16px; font-weight: bold;">
                        {mom_str}{self.unit}
                    </span>
                </div>
                <div>
                    <span style="color: #999; font-size: 12px;">📈 同比（{self.yoy_label}）</span><br>
                    <span style="color: {self.yoy_color}; font-size: 16px; font-weight: bold;">
                        {yoy_str}{self.unit}
                    </span>
                </div>
            </div>
        </div>
        """
    
    def get_stats(self) -> dict:
        return {
            'label': self.label,
            'current': self.current_val,
            'prev': self.prev_val,
            'last_year': self.last_year_val,
            'delta_mom': self.delta_mom,
            'delta_yoy': self.delta_yoy,
            'unit': self.unit
        }


class MetricCardDownGroup:
    """批量管理多个指标卡片的类"""
    
    def __init__(self):
        self.cards = []
    
    def add_card(
        self,
        label: str,
        icon: str,
        current_val: float,
        prev_val: float = None, # type: ignore
        last_year_val: float = None, # type: ignore
        unit: str = "%",
        decimal: int = 1,
        border: bool = True
    ):
        card = MetricCardDown(
            label=label,
            icon=icon,
            current_val=current_val,
            prev_val=prev_val,
            last_year_val=last_year_val,
            unit=unit,
            decimal=decimal,
            border=border
        )
        self.cards.append(card)
        return self
    
    def render(self, cols: int = 5):
        if not self.cards:
            return
        
        row_count = (len(self.cards) + cols - 1) // cols
        
        for i in range(row_count):
            row_cols = st.columns(cols)
            for j in range(cols):
                idx = i * cols + j
                if idx < len(self.cards):
                    self.cards[idx].render(row_cols[j])
    
    def get_all_stats(self) -> list:
        return [card.get_stats() for card in self.cards]

"""
# 批量创建卡片
group = MetricCardDownGroup()

group.add_card(
    label="成活率",
    icon="🐖",
    current_val=current['成活率'],
    prev_val=df.iloc[-2]['成活率'] if len(df) > 1 else current['成活率'],
    last_year_val=df.iloc[-13]['成活率'] if len(df) > 12 else current['成活率'],
    unit="%",
    decimal=1
).add_card(
    label="料肉比",
    icon="📊",
    current_val=current['料肉比'],
    prev_val=df.iloc[-2]['料肉比'] if len(df) > 1 else current['料肉比'],
    last_year_val=df.iloc[-13]['料肉比'] if len(df) > 12 else current['料肉比'],
    unit="",
    decimal=2
).add_card(
    label="PSY",
    icon="👶",
    current_val=current['PSY'],
    prev_val=df.iloc[-2]['PSY'] if len(df) > 1 else current['PSY'],
    last_year_val=df.iloc[-13]['PSY'] if len(df) > 12 else current['PSY'],
    unit="",
    decimal=1
).add_card(
    label="日增重",
    icon="📏",
    current_val=current['日增重'],
    prev_val=df.iloc[-2]['日增重'] if len(df) > 1 else current['日增重'],
    last_year_val=df.iloc[-13]['日增重'] if len(df) > 12 else current['日增重'],
    unit="g",
    decimal=0
).add_card(
    label="头均成本",
    icon="💰",
    current_val=current['头均成本'],
    prev_val=df.iloc[-2]['头均成本'] if len(df) > 1 else current['头均成本'],
    last_year_val=df.iloc[-13]['头均成本'] if len(df) > 12 else current['头均成本'],
    unit="元",
    decimal=1
)

# 一行5个渲染
group.render(cols=5)
"""

# 牧原指标体系
class MetricCardMYSystem:
    """自定义指标卡片组件（左右分布）"""
    
    def __init__(self, label: str, icon: str, current_val: float, 
                 prev_val: float, last_year_val: float, target: float = None, # type: ignore
                 score_type: str = "越小越好",
                 unit: str = "%", decimal: int = 1, border: bool = True, background_color: str = None): # type: ignore
        self.label = label # 指标卡名称
        self.icon = icon # 指标卡图标
        self.current_val = current_val # 当前值
        self.prev_val = prev_val # 上个月值
        self.last_year_val = last_year_val # 上一年值
        self.target = target # 目标值
        self.unit = unit # 单位
        self.decimal = decimal # 保留小数位数，控制所有数值
        self.border = border # 是否显示边框：默认显示边框
        self.background_color = background_color # 背景颜色，默认白色
        self.score_type = score_type # 越大越好，越小越好，越接近目标值越好，默认越小越好
    
    def render(self, col):
        """在指定的列中渲染卡片"""
        with col:
            delta_mom = (self.current_val - self.prev_val) / self.prev_val * 100
            delta_yoy = (self.current_val - self.last_year_val) / self.last_year_val * 100
            
            mom_color = "#52c41a" if delta_mom >= 0 else "#ff4d4f"
            yoy_color = "#52c41a" if delta_yoy >= 0 else "#ff4d4f"
            
            format_str = f"{{:.{self.decimal}f}}"
            
            # 带正负号
            mom_str = f"{'+' if delta_mom >= 0 else '-'}{format_str.format(abs(delta_mom))}"
            yoy_str = f"{'+' if delta_yoy >= 0 else '-'}{format_str.format(abs(delta_yoy))}"
            # 带箭头
            mom_jiantou = f"{'↑' if delta_mom > 0 else '↓' if delta_mom < 0 else '→'}"
            yoy_jiantou = f"{'↑' if delta_yoy > 0 else '↓' if delta_yoy < 0 else '→'}"

            if self.background_color is None: # 
                if self.score_type == "越大越好":
                    self.background_color = "#72fc9b" if self.current_val >= self.target else "#b8837f"
                elif self.score_type == "越小越好":
                    self.background_color = "#72fc9b" if self.current_val <= self.target else "#b8837f"
                else:
                    self.background_color = "#ffffff"
            else: # 传递了背景颜色的时候，使用传递的颜色
                self.background_color = self.background_color

            st.markdown(f"""
            <div style="
                border: {'1px solid ' + self.background_color if self.border else 'none'};
                border-radius: 8px;
                padding: 16px 20px; 
                background: white;
            ">
                <div style="color: #666; font-size: 14px;">{self.icon} {self.label}</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 32px; font-weight: bold; color: #1a1a1a;">{format_str.format(self.current_val)}</span>
                        <span style="font-size: 16px; font-weight: bold; color: #1a1a1a;">{self.unit}</span>
                    </div>
                    <div style="text-align: left;">
                        <div style="color: #000000; font-size: 14px; padding-bottom: 4px; border-bottom: 1px dashed #808080;">
                            目标：<span style="font-weight: bold; color: #000000;font-size: 16px;">{format_str.format(self.target)}</span>
                        </div>
                        <div style="color: {mom_color}; font-size: 14px; padding-top: 4px;">
                            环比：<span style="font-weight: bold;">{mom_str}%{mom_jiantou}</span>
                        </div>
                        <div style="color: {yoy_color}; font-size: 14px;">
                            同比：<span style="font-weight: bold;">{yoy_str}%{yoy_jiantou}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)