"""
ArcGIS Pro的ArcPy模块路径
C:\Users\caokai\AppData\Local\ESRI\conda\envs\arcgispro301-py39
"""
"""
调用ArcGIS Pro的ArcPy模块，导出ArcGIS Pro布局为PDF文件
Python 3.9
1. 将shp文件作为图层添加到地图中，修改图层的符号样式，存储为.aprx文件
2. 将布局中的标题修改为指定的文本，日期更新为当天日期
3. 导出ArcGIS Pro布局为PDF文件
"""
import arcpy
import os


def export_layout_to_pdf(aprx_path: str, layout_name: str, output_pdf_path: str):
    """
    导出 ArcGIS Pro 布局为 PDF 文件。

    参数:
    aprx_path (str): ArcGIS Pro 项目文件 (.aprx) 的路径
    layout_name (str): 布局的名称
    output_pdf_path (str): 输出 PDF 文件的路径
    """
    # 打开 ArcGIS Pro 项目
    aprx = arcpy.mp.ArcGISProject(aprx_path)

    # 获取布局对象
    layout = aprx.listLayouts(layout_name)[0]

    # 导出布局为 PDF 文件
    layout.exportToPDF(output_pdf_path)
    print(f"布局已导出为 PDF 文件: {output_pdf_path}")

# 示例调用
aprx_path = r"D:\RouteDesigen\Finished observation points of Group1\Observation_Points_20241028_20241103.aprx"
layout_name = "Layout"
output_pdf_path = r"D:\RouteDesigen\Finished observation points of Group1\Observation_Points_20241028_20241103.pdf"

export_layout_to_pdf(aprx_path, layout_name, output_pdf_path)


print(arcpy.__version__)

print(arcpy.GetInstallInfo())