# -*- coding: utf-8 -*-

import sys
import os
import re
import numpy as np
import pyqtgraph as pg

from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt, QUrl, QTimer, QDateTime, QTime, QDate
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QProgressBar,
    QFrame,
    QTableWidgetItem,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

import config
#import resources_rc
from Ui_login import Ui_login
from Ui_mainwindow import Ui_MainWindow
from Ui_math import Ui_Form_math
#from Ui_xinxi import Ui_Form_xinxi

#---登录窗口类---
class winForm(QMainWindow, Ui_login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  

        #---登陆按钮事件---
        self.pushButton.clicked.connect(self.save_data)

    #---保存数据到全局变量并跳转主界面---
    def save_data(self):
        uid = self.lineEdit.text()
        pwd = self.lineEdit_2.text()    

        if not uid or not pwd:
            QMessageBox.warning(self, "错误", "请填写所有信息！")
            return

        config.vid = uid
        config.vpassword = pwd
        
        # 调试打印
        print(f"当前全局变量:ID={config.vid}, Password={config.vpassword}")
        self.jump2main()

    def jump2main(self):
            self.mw = mainWin()
            self.mw.show()
            self.close()  

#---主窗口类---
class mainWin(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pushButton.clicked.connect(self.jump2math)

    def jump2math(self):
        self.math = mathWin()
        self.math.show()
        self.close()

class StatRowWidget(QWidget):
    def __init__(self, name, count, percent, color):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(15)

        self.label_name = QLabel(name)
        self.label_name.setFixedWidth(130)
        self.label_name.setStyleSheet("color: black;")

        self.label_count = QLabel(str(count))
        self.label_count.setFixedWidth(40)
        self.label_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_count.setStyleSheet("color: white;")

        self.progress = QProgressBar()
        self.progress.setValue(int(percent))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(12)

        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #334155;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)

        self.label_percent = QLabel(f"{percent:.2f}%")
        self.label_percent.setFixedWidth(60)
        self.label_percent.setStyleSheet("color: #94a3b8;")

        layout.addWidget(self.label_name)
        layout.addWidget(self.label_count)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.label_percent)

#---数据统计窗口---
class mathWin(QWidget, Ui_Form_math):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.jump2main)

        self.refresh_chart_4_monthly()
        self.refresh_chart_3_monthly()
        self.refresh_chart_2_weekly()
        self.refresh_chart_1_daily()

        # 设置按钮组的 ID
        self.buttonGroup.setId(self.pushButton_1, 0)  # 对应 index 0 -> 1天
        self.buttonGroup.setId(self.pushButton_2, 1)  # 对应 index 1 -> 7天
        self.buttonGroup.setId(self.pushButton_3, 2)  # 对应 index 2 -> 30天
        self.buttonGroup.setId(self.pushButton_4, 3)  # 对应 index 3 -> 365天
        self.buttonGroup.idClicked.connect(self.update_view)

        # 初始化表格数据
        self.init_table_data()

        self.refresh_stats_data(1)    # 近 1 天
        self.refresh_stats_data(7)    # 近 7 天
        self.refresh_stats_data(30)   # 近 30 天
        self.refresh_stats_data(365)  # 近 365 天

    def update_view(self, index):
        # 定义时间范围列表
        days_list = [1, 7, 30, 365]
        self.stackedWidget.setCurrentIndex(index)
        days = days_list[index]

        # 调用 refresh_stats_data 方法
        self.refresh_stats_data(days)

    #---初始化表格数据---
    def init_table_data(self):
        data_rows = [
            # [违禁品类型, 具体类别, 数量, 单位, 最后检测时间]
            ["武器", "枪支", "14", "件", "2026-01-20"],
            ["武器", "子弹", "5", "件", "2026-01-21"],
            ["武器", "管制刀具", "1", "件", "2026-01-21"],
            ["武器", "指虎", "1", "件", "2026-01-22"],
            ["易燃物品", "易燃液体", "2", "升", "2026-01-20"],
            ["电子产品", "笔记本电脑", "52", "台", "2026-01-25"],
            ["电子产品", "平板电脑", "1", "台", "2026-01-25"],
            ["其他违禁品", "其他", "3", "件", "2026-01-22"]
        ]
        for i in range(1, 5):  
            table = getattr(self, f"tableWidget_{i}", None)  # 动态获取表格控件
            if table is None:
                print(f"表格控件 tableWidget_{i} 不存在")
                continue
            table.setRowCount(len(data_rows))  # 设置行数
            for row_idx, row_data in enumerate(data_rows):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    # 设置文字居中
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row_idx, col_idx, item)
       

    def refresh_stats_data(self, days):
        # 1. 定义分类映射表 (保持不变)
        category_map = {
            "gun": "武器", "bullet": "武器", "knife": "武器", "brasskunckles": "武器", 
            "electrocutor": "武器", "handcuffs": "武器",
            "wrench": "工具与生活器械", "tongs": "工具与生活器械", "scissors": "工具与生活器械", 
            "umbrella": "工具与生活器械", "lighter": "工具与生活器械",
            "phone": "电子产品", "laptop": "电子产品", "tabletPC": "电子产品", "portablecharger": "电子产品",
            "plasticbottle": "杂项与风险品", "fireworks": "杂项与风险品", "pressure": "杂项与风险品"
        }
        
        # --- 新增：具体名称的中英文转换表 ---
        name_cn_map = {
            "gun": "枪支", "bullet": "子弹", "knife": "刀具", "brasskunckles": "指虎",
            "electrocutor": "电击器", "handcuffs": "手铐", "wrench": "扳手", "tongs": "钳子",
            "scissors": "剪刀", "umbrella": "雨伞", "lighter": "打火机", "phone": "手机",
            "laptop": "笔记本电脑", "tabletPC": "平板电脑", "portablecharger": "充电宝",
            "plasticbottle": "塑料瓶", "fireworks": "烟花爆竹", "pressure": "压力罐"
        }
        
        # 2. 计算日期过滤阈值 (保持不变)
        threshold_date_str = QDateTime.currentDateTime().addDays(-days).toString("yyyyMMdd")
        threshold_date = int(threshold_date_str)

        # 3. 动态定位目标表格 (保持不变)
        days_list = [1, 7, 30, 365]
        try:
            tab_idx = days_list.index(days) + 1
            target_table = getattr(self, f"tableWidget_{tab_idx}")
        except (ValueError, AttributeError):
            target_table = self.tableWidget_1

        # 4. 读取与统计 (保持不变)
        data_path = "./labeltest" 
        if not os.path.exists(data_path): return
        
        stats_results = {}
        for filename in os.listdir(data_path):
            match = re.search(r'^\d+_(.*?)_[\d\.]+_(\d{8})_\d+\.png', filename)
            if match:
                item_name_en = match.group(1) # 获取英文名用于逻辑判断
                item_date_str = match.group(2)
                item_date_int = int(item_date_str)

                if item_date_int >= threshold_date:
                    display_date = f"{item_date_str[:4]}-{item_date_str[4:6]}-{item_date_str[6:]}"
                    big_cat = category_map.get(item_name_en, "其他违禁品")
                    
                    if item_name_en not in stats_results:
                        stats_results[item_name_en] = {
                            "type": big_cat, 
                            "count": 1, 
                            "last_date": display_date
                        }
                    else:
                        stats_results[item_name_en]["count"] += 1
                        if display_date > stats_results[item_name_en]["last_date"]:
                            stats_results[item_name_en]["last_date"] = display_date

        # 5. 填充目标表格 (关键修改点：转换名称)
        target_table.setRowCount(0) 
        for row_idx, (en_name, info) in enumerate(stats_results.items()):
            target_table.insertRow(row_idx)
            
            # --- 核心：在这里将英文 en_name 转为中文 ---
            cn_name = name_cn_map.get(en_name, en_name) # 如果找不到对应的中文，显示原英文名
            
            row_data = [info["type"], cn_name, str(info["count"]), "件", info["last_date"]]
            
            for col_idx, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col_idx == 0 and text == "武器":
                    item.setForeground(Qt.GlobalColor.red)
                target_table.setItem(row_idx, col_idx, item)

        stats_for_panel = {}

        for en_name, info in stats_results.items():
            cn_name = name_cn_map.get(en_name, en_name)
            stats_for_panel[cn_name] = info["count"]

        # 根据 days 选择对应容器
        days_map = {
            1: self.chart_11,
            7: self.chart_21,
            30: self.chart_31,
            365: self.chart_41
        }

        container = days_map.get(days)
        if container:
            self.build_percent_panel(container, stats_for_panel)

    def refresh_chart_4_monthly(self):
        # 1. 初始化过去 12 个月的数据容器
        monthly_stats = {}
        x_labels = []
        current_date = QDate.currentDate()

        # 生成 12 个月的键值对，例如 "202505": 0
        for i in range(11, -1, -1):
            d = current_date.addMonths(-i)
            month_key = d.toString("yyyyMM")
            monthly_stats[month_key] = 0
            x_labels.append(d.toString("yy-MM")) # 坐标轴显示标签

        # 2. 读取文件夹并按月汇总
        data_path = "./labeltest"
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                # 匹配日期部分的前 6 位 (YYYYMM)
                match = re.search(r'_(\d{6})\d{2}_', filename)
                if match:
                    f_month = match.group(1)
                    if f_month in monthly_stats:
                        monthly_stats[f_month] += 1

        # 3. 准备绘图数据
        sorted_months = sorted(monthly_stats.keys())
        y_values = [monthly_stats[m] for m in sorted_months]
        x_indices = np.arange(len(y_values))

        # 4. 配置 chart_4 样式
        self.chart_4.clear()
        self.chart_4.setStyleSheet("""
            PlotWidget {
                background: transparent;
                border: 1px solid rgb(75, 127, 232);
                border-radius: 30px;
            }
        """)
        self.chart_4.setBackground(None)
        self.chart_4.getPlotItem().getViewBox().setBackgroundColor(None)
        self.chart_4.setAutoFillBackground(False)

        self.chart_4.setTitle("月度违禁品拦截趋势 (12个月)", color='#475569', size='14pt')

        # 设置画笔：深蓝色线，带圆形数据点
        pen = pg.mkPen(color='#3B82F6', width=3)
        self.chart_4.plot(x_indices, y_values, 
                        pen=pen, 
                        symbol='o', 
                        symbolSize=10, 
                        symbolBrush='#60A5FA')
        text_color = '#475569'
        self.chart_4.getAxis('left').setTextPen(text_color)
        self.chart_4.getAxis('bottom').setTextPen(text_color)

        # 5. 设置坐标轴刻度标签
        xticks = [(i, label) for i, label in enumerate(x_labels)]
        self.chart_4.getAxis('bottom').setTicks([xticks])
        
        # 显示网格和标签
        self.chart_4.showGrid(x=True, y=True)
        self.chart_4.getAxis('left').setPen(pg.mkPen('#475569'))
        self.chart_4.getAxis('bottom').setPen(pg.mkPen('#475569'))
        self.chart_4.setLabel('left', '拦截数量', units='件')
        self.chart_4.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)


    def refresh_chart_3_monthly(self):
        # 1. 初始化近 30 天的数据容器
        daily_stats = {}
        x_labels = []
        current_date = QDate.currentDate()

        # 生成 30 个日期的键值对，例如 "20260120": 0
        for i in range(29, -1, -1):
            d = current_date.addDays(-i)
            date_key = d.toString("yyyyMMdd")
            daily_stats[date_key] = 0
            # 坐标轴显示标签，如 "01-20"
            x_labels.append(d.toString("MM-dd"))

        # 2. 读取文件夹并按日汇总
        data_path = "./labeltest"
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                # 匹配日期部分（假设文件名末尾是 8 位日期）
                match = re.search(r'_(\d{8})_', filename)
                if match:
                    f_date = match.group(1)
                    if f_date in daily_stats:
                        daily_stats[f_date] += 1

        # 3. 准备绘图数据
        sorted_keys = sorted(daily_stats.keys())
        y_values = [daily_stats[k] for k in sorted_keys]
        x_indices = np.arange(len(y_values))

        # 4. 配置 chart_3 样式 (完全对标 chart_4)
        self.chart_3.clear()
        self.chart_3.setStyleSheet("""
            PlotWidget {
                background: transparent;
                border: 1px solid rgb(75, 127, 232);
                border-radius: 30px;
            }
        """)
        self.chart_3.setBackground(None)
        self.chart_3.getPlotItem().getViewBox().setBackgroundColor(None)
        self.chart_3.setAutoFillBackground(False)
        
        self.chart_3.setTitle("近 30 天违禁品拦截趋势", color='#475569', size='14pt')

        # 使用与 chart_4 一致的深蓝色线和圆形数据点
        pen = pg.mkPen(color='#3B82F6', width=3)
        self.chart_3.plot(x_indices, y_values, 
                        pen=pen, 
                        symbol='o', 
                        symbolSize=10, 
                        symbolBrush='#60A5FA')
        text_color = '#475569'
        self.chart_3.getAxis('left').setTextPen(text_color)
        self.chart_3.getAxis('bottom').setTextPen(text_color)
        # 5. 设置坐标轴刻度标签
        # 为了美观，每隔 5 天显示一个刻度
        xticks = []
        for i, label in enumerate(x_labels):
            if i % 5 == 0 or i == len(x_labels) - 1:
                xticks.append((i, label))
        
        self.chart_3.getAxis('bottom').setTicks([xticks])
        
        # 显示网格和标签
        self.chart_3.showGrid(x=True, y=True)
        self.chart_3.getAxis('left').setPen(pg.mkPen('#475569'))
        self.chart_3.getAxis('bottom').setPen(pg.mkPen('#475569'))
        self.chart_3.setLabel('left', '拦截数量', units='件')

    def refresh_chart_2_weekly(self):
        daily_stats = {}
        x_labels = []
        current_date = QDate.currentDate()

        for i in range(6, -1, -1):
            d = current_date.addDays(-i)
            date_key = d.toString("yyyyMMdd")
            daily_stats[date_key] = 0
            x_labels.append(d.toString("MM-dd"))

        data_path = "./labeltest"
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                match = re.search(r'_(\d{8})_', filename)
                if match:
                    f_date = match.group(1)
                    if f_date in daily_stats:
                        daily_stats[f_date] += 1

        y_values = [daily_stats[k] for k in sorted(daily_stats.keys())]
        x_indices = np.arange(len(y_values))

        self.chart_2.clear()
        self.chart_2.setStyleSheet("""
            PlotWidget {
                background: transparent;
                border: 1px solid rgb(75, 127, 232);
                border-radius: 30px;
            }
        """)
        self.chart_2.setBackground(None)
        self.chart_2.getPlotItem().getViewBox().setBackgroundColor(None)
        self.chart_2.setAutoFillBackground(False)

        self.chart_2.setTitle("近 7 天违禁品拦截趋势", color='#475569', size='14pt')
        pen = pg.mkPen(color='#3B82F6', width=3)
        text_color = '#475569'
        self.chart_2.plot(x_indices, y_values, pen=pen, symbol='o', symbolSize=10, symbolBrush=(0, 153, 255))
        
        xticks = [(i, label) for i, label in enumerate(x_labels)]
        self.chart_2.getAxis('bottom').setTicks([xticks])
        self.chart_2.showGrid(x=True, y=True)
        self.chart_2.getAxis('left').setPen(pg.mkPen(text_color))
        self.chart_2.getAxis('bottom').setPen(pg.mkPen(text_color))
        self.chart_2.setLabel('left', '拦截数量', units='件')

    def refresh_chart_1_daily(self):
        # 1. 准备 24 小时的数据容器 (从 23 小时前到当前小时)
        hour_stats = {}
        x_labels = []
        current_dt = QDateTime.currentDateTime()

        for i in range(23, -1, -1):
            dt = current_dt.addSecs(-i * 3600)
            time_key = dt.toString("yyyyMMddhh") # 匹配到小时
            hour_stats[time_key] = 0
            x_labels.append(dt.toString("hh:00"))

        # 2. 读取并汇总 (假设你的文件名包含时间，或者通过文件修改时间判断)
        # 这里为了演示，我们假设文件名逻辑依然是 _YYYYMMDD.txt，
        # 如果要精确到小时，需要获取文件的 os.path.getmtime
        data_path = "./labeltest"
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                file_full_path = os.path.join(data_path, filename)
                # 获取文件的最后修改时间并转为 YYYYMMDDhh 格式
                mtime = os.path.getmtime(file_full_path)
                f_hour = QDateTime.fromMSecsSinceEpoch(int(mtime * 1000)).toString("yyyyMMddhh")
                
                if f_hour in hour_stats:
                    hour_stats[f_hour] += 1

        y_values = [hour_stats[k] for k in sorted(hour_stats.keys())]
        x_indices = np.arange(len(y_values))

        # 3. 绘图 (风格一致)
        self.chart_1.clear()
        self.chart_1.setStyleSheet("""
            PlotWidget {
                background: transparent;
                border: 1px solid rgb(75, 127, 232);
                border-radius: 30px;
            }
        """)
        self.chart_1.setBackground(None)
        self.chart_1.getPlotItem().getViewBox().setBackgroundColor(None)
        self.chart_1.setAutoFillBackground(False)
        text_color = '#475569'
        self.chart_1.setTitle("近 24 小时拦截趋势", color='#475569', size='14pt')
        
        pen = pg.mkPen(color='#3B82F6', width=3)
        self.chart_1.plot(x_indices, y_values, pen=pen, symbol='o', symbolSize=10, symbolBrush='#60A5FA')
        
        # 每隔 4 小时显示一个标签
        xticks = [(i, label) for i, label in enumerate(x_labels) if i % 4 == 0]
        self.chart_1.getAxis('bottom').setTicks([xticks])
        self.chart_1.showGrid(x=True, y=True)
        self.chart_1.getAxis('left').setPen(pg.mkPen(text_color))
        self.chart_1.getAxis('bottom').setPen(pg.mkPen(text_color))
        self.chart_1.setLabel('left', '拦截数量', units='件')

    def build_percent_panel(self, container_widget, stats_dict):
        container_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 初始化布局（只创建一次）
        if not container_widget.layout():
            layout = QVBoxLayout(container_widget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(8)
            container_widget.setLayout(layout)
            container_widget.setStyleSheet("""
            container_widget {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgb(75, 127, 232);
                border-radius: 30px;
                }
                """)
        else:
            layout = container_widget.layout()

        # 清空旧内容
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total = sum(stats_dict.values())
        if total == 0:
            return

        # 按数量排序
        sorted_items = sorted(stats_dict.items(),
                            key=lambda x: x[1],
                            reverse=True)

        colors = ["#3B82F6", "#EF4444", "#F59E0B",
                "#8B5CF6", "#10B981", "#EC4899"]

        for i, (name, count) in enumerate(sorted_items):
            percent = count / total * 100
            row = StatRowWidget(
                name,
                count,
                percent,
                colors[i % len(colors)]
            )
            layout.addWidget(row)

        layout.addStretch()

    def jump2main(self):
        self.mw = mainWin()
        self.mw.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = winForm()
    win.show()
    sys.exit(app.exec())
