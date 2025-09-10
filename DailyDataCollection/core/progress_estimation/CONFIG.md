# GMAS 图幅估算配置示例

## Excel数据文件配置

要使用图幅估算功能，需要确保Excel数据文件配置正确。

### 1. Excel文件位置

默认情况下，系统会在以下位置查找Excel文件：
- 配置文件中指定的路径 (`reports.statistics.daily_details_file`)
- 默认路径：`{workspace}/Daily_statistics_details_for_Group_3.2.xlsx`

### 2. Excel文件格式要求

Excel文件应包含以下结构：

#### 工作表名称
- 主数据工作表：`总表`

#### 必需列
- `Team No.`: 团队编号 (如：Team 1, Team 2)
- `Sheet No.`: 图幅编号 (如：H48E001001, H48E002002)
- `Sheet Name`: 图幅名称 (可选)
- `Person in Charge`: 负责人 (可选)
- `Adjusted \nNum`: 调整后目标数量
- 日期列：以日期格式命名的列，包含每日完成的观测点数

#### 数据格式
- 行：每行代表一个团队
- 列：日期列包含该团队在该日期完成的点数
- 数值：非负整数，空值视为0

### 3. 配置文件设置

在 `config/settings.yaml` 中添加或修改：

```yaml
reports:
  statistics:
    daily_details_file: "路径/到/你的/Excel文件.xlsx"
```

### 4. 使用方法

#### 方法1：双击运行批处理文件
```
运行图幅估算.bat
```

#### 方法2：运行Python脚本
```bash
python run_estimation.py
```

#### 方法3：在代码中调用
```python
from core.progress_estimation import MapsheetEstimationRunner

# 创建运行器
runner = MapsheetEstimationRunner()

# 运行估算
results = runner.run_mapsheet_estimations(
    days_back=30,        # 使用最近30天数据
    confidence_level=0.8  # 80%置信度
)
```

### 5. 估算方法说明

系统支持4种估算方法：

1. **简单平均法** (`simple_average`)
   - 基于历史平均日完成速度
   - 适用于稳定的工作节奏
   
2. **加权平均法** (`weighted_average`)
   - 近期数据权重更高
   - 适用于有趋势变化的项目
   
3. **线性回归法** (`linear_regression`)
   - 基于累计进度的线性趋势
   - 适用于有明确趋势的项目
   
4. **蒙特卡洛模拟法** (`monte_carlo`)
   - 考虑工作日/周末差异的随机模拟
   - 适用于需要考虑不确定性的复杂项目

### 6. 输出结果

程序会生成以下文件：

#### 主要报告
- `mapsheet_estimations_YYYYMMDD_HHMMSS.json`: 详细估算结果（JSON格式）
- `summary_report_YYYYMMDD_HHMMSS.json`: 汇总报告（JSON格式）
- `readable_report_YYYYMMDD_HHMMSS.txt`: 人类可读报告
- `estimation_report_YYYYMMDD_HHMMSS.xlsx`: Excel格式报告

#### 图表文件
- `mapsheet_XXX/`: 每个图幅的详细图表文件夹
- `progress_dashboard_YYYYMMDD.png`: 进度仪表板图表

### 7. 常见问题

#### Q: 找不到Excel文件
A: 检查文件路径配置，确保文件存在且有读取权限

#### Q: 估算结果不准确
A: 检查历史数据质量，建议至少有7天的活跃数据

#### Q: 某些图幅无法估算
A: 可能是该图幅历史数据不足或质量较差

#### Q: 程序运行出错
A: 检查Python环境和依赖包是否正确安装

### 8. 依赖包要求

确保已安装以下Python包：
```bash
pip install pandas openpyxl matplotlib numpy lxml
```
