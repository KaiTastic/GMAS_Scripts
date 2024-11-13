
import os
import re
import zipfile
import shutil
import argparse
from attr import dataclass, field
from lxml import etree
from datetime import date, datetime, timedelta
from matplotlib.pyplot import cla
from shapely import points
import dataclasses



#-----------------------初始设置-----------------------#
# 工作文件夹
workspace = r"D:\RouteDesigen"
# 当前的微信聊天记录文件夹
# 当前的微信聊天记录文件夹
currentWechatDic_str = r"D:\Users\lenovo\Documents\WeChat Files\WeChat Files\bringsmile\FileStorage\File"
# 设置需要统计的图幅的最小和最大序号
minSequenceValue = 1
maxSequenceValue = 22
# 设置文件向前回溯查找的终止日期，格式为"YYYYMMDD"
lookUpBacktoDate_str = "20240901"
#-----------------------初始设置-----------------------#


args = parse_args()
date_str = args.date


dailyReportExcelFileName= date_str + "点统计.xlsx"
# 100K图幅名称信息等
_100kSheetNamesFile = os.path.join(workspace, "100K_sheet_names_271_name_V3_after_GEOSA_edit.xlsx")

# 图标文件
icon_file = os.path.join(workspace, "Layer0_Symbol_Square.png")



#返回当前目录下所有含多个特定字符串(不区分大小写)列表的文件全路径
def list_fullpath_of_files_with_keywords(directory: str, keywords: list) -> list:
    matches = []
    for root, _, files in os.walk(directory):
        for file in files:
            if all(keyword.lower() in file.lower() for keyword in keywords):
                matches.append(os.path.join(root, file))
    return matches

def find_files_with_max_number(directory) -> dict:
    files_dict = {}
    # 遍历目录中的所有文件
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            base_name = re.sub(r'\(\d+\)', '', filename)
            number = get_number_in_parentheses(filename)
            file_path = os.path.join(root, filename)
            if base_name not in files_dict:
                files_dict[base_name] = (file_path, number)
            else:
                existing_file, existing_number = files_dict[base_name]
                if number > existing_number:
                    files_dict[base_name] = (file_path, number)
    # 删除括号中数字为-1的文件
    files_dict = {base_name: (file_path, number) for base_name, (file_path, number) in files_dict.items() if number != -1}
    # 输出包含相同基础文件名中括号内数字最大的文件
    return files_dict


@dataclass
class KMLFile:
    points = {}
    routes = []
    pointsCount = 0
    routesCount = 0
    errors = []

    def __post_init__(self, kml_content):
        self.getpoints(kml_content)
        self.getroutes(kml_content)

    def getpoints(self, kml_content):
        kml_content = kml_file.read()
        root = etree.fromstring(kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        # 通过Point元素提取点要素，Point元素下的name元素为OBSID，coordinates元素为经纬度
        # 通过name元素提取OBSID，通过coordinates元素提取经纬度，只有可能name元素为空或不符合命名规范，coordinates元素一定存在
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
            if point is not None:
                name = placemark.find('.//{http://www.opengis.net/kml/2.2}name')
                if name is not None and name.text:
                    obspid_pattern = re.compile(r'\d{5}[A-Za-z]\d{3}')
                    if obspid_pattern.match(name.text):
                        obspid = name.text
                        longitude = point.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.split(',')[0]
                        latitude = point.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.split(',')[1]
                        self.pointsDict[obspid] = {'longitude': longitude, 'latitude': latitude}
                    else:
                        error = f"KMZ文件 {self.filename} 中的点要素{name.text}格式不正确(不符合OBSID命名格式格式)"
                        self.errors.append(error)
                        print(error)
        # 通过Description元素提取点要素，Description元素下的内容可能包含OBSID、经度和纬度3个要素
        # 通过Description元素提取OBSID、经度和纬度，只有可能OBSID、经度或纬度均可能为空
        for description in root.findall('.//{http://www.opengis.net/kml/2.2}description'):
            if description is not None and description.text:
                obspid_pattern = re.compile(r'<td>(\d{5}[A-Za-z]\d{3})</td>')
                longitude_pattern = re.compile(r'<td>Longitude</td>\s*<td>(-?\d+\.\d+)</td>')
                latitude_pattern = re.compile(r'<td>Latitude</td>\s*<td>(-?\d+\.\d+)</td>')
                obspid_match = obspid_pattern.search(description.text)
                longitude_match = longitude_pattern.search(description.text)
                latitude_match = latitude_pattern.search(description.text)
                obspid = obspid_match.group(1) if obspid_match else None
                longitude = float(longitude_match.group(1)) if longitude_match else None
                latitude = float(latitude_match.group(1)) if latitude_match else None
            # if obspid == None or longitude == None or latitude == None:
            #     print(f"KMZ文件 {self.path} 中的点要素没有OBSID{obspid}或经度{longitude}或纬度{latitude}")
                if obspid and longitude and latitude:
                    if not obspid in self.pointsDict:
                        self.pointsDict[obspid] = { 'longitude': longitude, 'latitude': latitude}
            # 如果OBSID、经度和纬度中有一个为空，则记录日志
                if obspid and not longitude and not latitude:
                    error = f"KMZ文件 {self.filename} 中的点要素{obspid}没有经度或纬度"
                    self.errors.append(error)
                    print(error)
        for obspid, coords in self.pointsDict.items():
            if coords['longitude'] == None or coords['latitude'] == None:
                # 将缺少有效信息的点要素删除
                del self.pointsDict[obspid]
                error = f"KMZ文件 {self.filename} 中的点要素{obspid}缺少经度或纬度"
                self.errors.append(error)
                print(error)
        self.pointsCount = len(self.pointsDict)
        return self
    def getroutes(self, kml_content):
        root = etree.fromstring(kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        # 查找所有的Placemark元素下的LineString元素
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            linestring = placemark.find('.//{http://www.opengis.net/kml/2.2}LineString')
            if linestring is not None:
                coordinates = linestring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
                if coordinates is not None:
                    self.routes.append(coordinates.text.strip())
        self.routesCount = len(self.routes)
        return self
    
    # 实现加法操作：两个文件相加，得到一个新的文件
    def __add__(self, other: 'KMLFile') -> 'KMLFile':
        if not isinstance(other, KMLFile):
            raise TypeError("Operands must be of type 'KMLFile'")
        # 创建新的KMLFile对象
        new_file = KMLFile()
        # 合并点要素（相同的键进行了覆盖）
        new_file.points = {**self.points, **other.points}
        new_file.pointsCount = len(new_file.points)
        # 合并线要素（列表相加并去重）
        new_file.routes = list(set(self.routes + other.routes))
        new_file.routesCount = len(new_file.routes)
        return new_file

    # 实现减法操作：两个点相减，得到一个新的点
    def __sub__(self, other: 'KMLFile') -> 'KMLFile':
        if not isinstance(other, KMLFile):
            raise TypeError("文件类型必须为KML")
        # 验证一个字典的键是否是另一个字典键的子集
        if not (self.points.keys() <= other.points.keys() or other.points.keys() <= self.points.keys()):
            raise ValueError("KML文件中的点要素不是另一个的子集")
        # 线要素不做处理
        # if not (set(self.routes) <= set(other.routes) or set(other.routes) <= set(self.routes)):
        #     raise ValueError("KML文件中的线要素不是另一个的子集")
        #         # 创建新的KMLFile对象
        new_file = KMLFile()
        # 计算点要素的差异
        new_file.points = {key: value for key, value in self.points.items() if key not in other.points}
        new_file.points.update({key: value for key, value in other.points.items() if key not in self.points})
        # 线要素不做处理
        # new_file.pointsCount = len(new_file.points)
        # # 计算线要素的差异并去重
        # new_file.routes = list(set(self.routes).symmetric_difference(set(other.routes)))
        # new_file.routesCount = len(new_file.routes)
        # return new_file
        


class DailyFile(object):

    def __init__(self, mapsheetFileName: str, date_str: str):

        self.mapsheetFileName = mapsheetFileName
        self.date =  datetime.strptime(date_str, "%Y%m%d")
        self.filename = None
        self.filepath = None
        self.romanName = None
        self.latinName = None
        self.date = None
        self.previousDate = None
        self.nextDate = None
        self.hashvalue = None


    def __export_to_kmz(self, kmz_file_path):
        # 在输出目录下创建临时目录
        temp_dir = os.path.join(kmz_file_path, "temp_kmz")
        os.makedirs(temp_dir, exist_ok=True)
        files_dir = os.path.join(temp_dir, 'files')
        os.makedirs(files_dir, exist_ok=True)
        # 创建临时KML文件
        temp_kml_file = os.path.join(kmz_file_path, "temp_combined.kml")
        # 根节点
        document = etree.Element("Document")
        # 添加线样式
        style = etree.SubElement(document, "Style", id="lineStyle")
        line_style = etree.SubElement(style, "LineStyle")
        color = etree.SubElement(line_style, "color")
        color.text = "ff000000"  # 黑色，格式为 AABBGGRR
        width = etree.SubElement(line_style, "width")
        width.text = "1"  # 线宽度
        # 添加线数据
        for i, coordinates in enumerate(self.routes):
            placemark = etree.SubElement(document, "Placemark")
            style_url = etree.SubElement(placemark, "styleUrl")
            style_url.text = "#lineStyle"
            name = etree.SubElement(placemark, "name")
            name.text = f"Route {i+1}"
            linestring = etree.SubElement(placemark, "LineString")
            coord_elem = etree.SubElement(linestring, "coordinates")
            coord_elem.text = coordinates
        # 添加点样式
        style = etree.SubElement(document, "Style", id="pointStyle")
        icon_style = etree.SubElement(style, "IconStyle")
        icon = etree.SubElement(icon_style, "Icon")
        href = etree.SubElement(icon, "href")
        href.text = "files/Layer0_Symbol_Square.png"  # 使用自定义图标的 URL
        # 添加点要素
        for obspid, coords in self.points.items():
            placemark = etree.SubElement(document, "Placemark")
            style_url = etree.SubElement(placemark, "styleUrl")
            style_url.text = "#pointStyle"
            name = etree.SubElement(placemark, "name")
            name.text = obspid
            point = etree.SubElement(placemark, "Point")
            coordinates = etree.SubElement(point, "coordinates")
            coordinates.text = f"{coords['longitude']},{coords['latitude']}"
        # 保存KML文件
        tree = etree.ElementTree(document)
        tree.write(temp_kml_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        # 将PNG文件移动到files文件夹中
        shutil.copy(icon_file, files_dir)
        # 压缩为KMZ文件
        with zipfile.ZipFile(output_kmz_file, 'w', zipfile.ZIP_DEFLATED) as kmz:
        # 将doc.kml文件添加到KMZ文件中
            kmz.write(temp_kml_file, 'doc.kml')
        # 将files文件夹中的PNG文件添加到KMZ文件中
            for root, _, files in os.walk(files_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    kmz.write(file_path, arcname)
        # 删除临时目录
        shutil.rmtree(temp_dir)
        # 删除临时KML文件
        os.remove(temp_kml_file)
        print(f"KMZ文件已保存到: {output_kmz_file}")
        return self

    def __getPreviousDayFile(self):
        date = self.date
        while date > datetime.strptime(lookUpBacktoDate_str, "%Y%m%d"):
            date -= timedelta(days=1)
            search_date_str = date.strftime("%Y%m%d")
            # file_path = os.path.join(workspace, date_str, "Finished points", f"{self.mapsheetFileName}_finished_points_and_tracks_{date_str}.kmz")
            # if os.path.exists(file_path):
            # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
            searchedFile_list = list_fullpath_of_files_with_keywords(currentWechatDic_str, [search_date_str, self.mapsheetFileName, "finished_points_and_tracks"]) 
            if searchedFile_list:
                latestFile = max(searchedFile_list, key=os.path.getctime)
                print(f"找到前一天的文件: {latestFile}")
                
            
            





        


        return self
    


        




file = DailyFile(r'D:\RouteDesigen\202411\20241102\Finished points\Ad_Dawadami_finished_points_and_tracks_20241102.kmz')


print(file.filename)

file.dailyIncreas

print(file.date)

file.points

print(file.pointsCount)
print(file.pointsDict)