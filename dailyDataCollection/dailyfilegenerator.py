import os
import re
import zipfile
import shutil
import hashlib
import xmlschema
import logging
import time
import pandas as pd
from attr import dataclass
from lxml import etree
from datetime import datetime, timedelta
from config import *
from abc import ABC, abstractmethod
from osgeo import ogr, osr
from datetime import datetime, timedelta
from openpyxl.styles import *
from openpyxl import Workbook, load_workbook


# 100K图幅名称信息等
SHEET_NAMES_FILE = os.path.join(WORKSPACE, 'resource', 'private', SHEET_NAMES_LUT_100K)
# 图标文件
ICON = os.path.join(WORKSPACE, 'resource', ICON_FILE)

# KML文件的XSD模式，分别为2.2和2.3版本
KML_SCHEMA_22 = os.path.join(WORKSPACE, 'resource', 'kml_xsd', '220', 'ogckml22.xsd')
KML_SCHEMA_23 = os.path.join(WORKSPACE, 'resource', 'kml_xsd', '230', 'ogckml23.xsd')


#返回当前目录下所有含多个特定字符串(不区分大小写)列表的文件全路径
def list_fullpath_of_files_with_keywords(directory: str, keywords: list) -> list:
    matches = []
    for root, _, files in os.walk(directory):
        for file in files:
            if all(keyword.lower() in file.lower() for keyword in keywords):
                matches.append(os.path.join(root, file))
    return matches

def find_files_with_max_number(directory: str) -> dict:
    """
    从指定目录中查找包含相同基础文件名的文件，并返回括号中数字最大的文件
    """
    files_dict = {}
    # 遍历目录中的所有文件
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # 去掉括号中的数字，例如：'file(1).txt' 返回 'file.txt'
            base_name = re.sub(r'\(\d+\)', '', filename)
            # 在文件名中查找括号内的数字。正则表达式 `r'\((\d+)\)'` 匹配括号内的一个或多个数字，并返回一个 `Match` 对象。如果没有找到匹配项，则返回 `None`
            match = re.search(r'\((\d+)\)', filename)
            # 从 `Match` 对象中提取括号内的数字，并将其转换为整数。如果找到了匹配项，则使用 `int(match.group(1))` 提取括号内的数字；否则，返回 -1
            # 提取括号中的数字，例如：'file(1).txt' 返回 1，'file.txt' 返回 -1
            number = int(match.group(1)) if match else -1        
            file_path = os.path.join(root, filename)
            # 如果文件名不在字典中，则将其添加到字典中
            if base_name not in files_dict:
                files_dict[base_name] = (file_path, number)
            # 如果文件名在字典中，则比较括号中的数字，保留数字最大的文件
            else:
                existing_file, existing_number = files_dict[base_name]
                if number > existing_number:
                    files_dict[base_name] = (file_path, number)
    # 清除括号中数字为-1的文件
    files_dict = {base_name: (file_path, number) for base_name, (file_path, number) in files_dict.items() if number != -1}
    # 输出包含相同基础文件名中括号内数字最大的文件
    return files_dict


class FileIO(ABC):

    def __init__(self, filepath):
        self.filepath = filepath

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self, content):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def update(self, content):
        pass

class GeneralIO(FileIO):

    def __init__(self, filepath, mode='r', encoding = 'utf-8'):
        super().__init__(filepath)
        self.data = None
        self.mode = mode
        self.encoding = encoding

    def read(self, method='r', encoding='utf-8'):
        if os.path.exists(self.filepath) and os.path.isfile(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as file:
                return file.read()

    def write(self, content):
        if os.path.exists(self.filepath) and os.path.isfile(self.filepath):
            with open(self.filepath, 'w', encoding='utf-8') as file:
                file.write(content)

    def delete(self):
        if os.path.exists(self.filepath) and os.path.isfile(self.filepath):
            os.remove(self.filepath)
        else:
            print(f"File delete fail: file \'{self.filepath}\' do not exist")
            raise FileNotFoundError(f"File \'{self.filepath}\' do not exist")
        
    def update(self, content):
        pass

    def __enter__(self):
        # 打开文件
        self.data = open(self.filepath, self.mode, self.encoding)
        return self.data
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.data:
            self.data.close()
        return False


class FileAttributes(object):
    def __init__(self, filepath):
        if not (os.path.exists(filepath) and os.path.isfile(filepath)):
            print(f"File \'{filepath}\' do not exist")
            exception = FileNotFoundError(f"File \'{filepath}\' do not exist")
            raise exception
        else:
            self.filepath = filepath
        # Basic file attributes
        self.filename = os.path.basename(filepath)
        self.file_dir = os.path.dirname(filepath)
        self.size = os.path.getsize(filepath)
        self.creation_time = time.ctime(os.path.getctime(filepath))
        self.modification_time = time.ctime(os.path.getmtime(filepath))
        self.access_time = time.ctime(os.path.getatime(filepath))
        self.file_type = self.__get_file_type()
        # hash value
        self._hashMD5 = None
        self._hashSHA265 = None

    def __get_file_type(self):
        return os.path.splitext(self.filename)[1]
    
    def __str__(self):
        return f"File Name: \t\t{self.filename}\n" \
               f"File Path: \t\t{self.filepath}\n" \
               f"File Size: \t\t{self.size} bytes\n" \
               f"Creation Time: \t\t{self.creation_time}\n" \
               f"Modification Time: \t{self.modification_time}\n" \
               f"Access Time: \t\t{self.access_time}\n" \
               f"File type: \t\t{self.file_type}\n"\
               f"MD5: \t\t\t{self.hashMD5}\n" \
               f"SHA265: \t\t{self.hashSHA265}"
    
    @property
    def hashMD5(self):
        if self._hashMD5 is None:
            self._hashMD5 = hashlib.md5(self._data).hexdigest()
        return self._hashMD5
    
    @property
    def hashSHA265(self):
        if self._hashSHA265 is None:
            self._hashSHA265 = hashlib.sha256(self._data).hexdigest()
        return self._hashSHA265




@dataclass
class KMLData:

    OSPID_PATTERN = r'\d{5}[A-Za-z]\d{3}'
    LONGITUDE_PATTERN = r'<td>Longitude</td>\s*<td>(-?\d+\.\d+)</td>'
    LATITUDE_PATTERN = r'<td>Latitude</td>\s*<td>(-?\d+\.\d+)</td>'

    points: dict = {}
    pointsCount: int = 0
    routes: list = []
    routesCount: int = 0
    errorMsg = []

    def __post_init__(self, kml_content):
        self.__getPoints(kml_content)
        self.__getRoutes(kml_content)

    def __getPoints(self, kml_content: str) -> None: 
        """
        __getPoints 从KML文件中提取点要素，包括OBSID、经度和纬度
        _extended_summary_
        :param kml_content: KML文件内容
        """
        kml_content = kml_content.read()
        root = etree.fromstring(kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        # Step 1: 通过Point元素提取点要素，Point元素下的name元素为OBSID，coordinates元素为经纬度，name元素可能为空或不符合命名规范，coordinates元素一定存在
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
            if point is not None:
                name = placemark.find('.//{http://www.opengis.net/kml/2.2}name')
                if name is not None and name.text:
                    obspid_pattern = re.compile(KMLData.OSPID_PATTERN)
                    if obspid_pattern.match(name.text):
                        obspid = name.text
                        coordinates = point.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.split(',')
                        longitude, latitude = coordinates[0], coordinates[1]
                        self.points[obspid] = {'longitude': longitude, 'latitude': latitude}
                    else:
                        error = f"点要素{name.text}格式不符合OBSID命名格式"
                        self.errorMsg.append(error)
                        print(error)
        # Step 2: 通过Description元素提取点要素，Description元素下的内容可能包含OBSID、经度和纬度3个要素，OBSID、经度或纬度均可能为空
        for description in root.findall('.//{http://www.opengis.net/kml/2.2}description'):
            if description is not None and description.text:
                obspidPattern = re.compile(KMLData.OSPID_PATTERN)
                longitudePattern = re.compile(KMLData.LONGITUDE_PATTERN)
                latitudePattern = re.compile(KMLData.LATITUDE_PATTERN)
                obspid_match = obspidPattern.search(description.text)
                longitude_match = longitudePattern.search(description.text)
                latitude_match = latitudePattern.search(description.text)
                obspid = obspid_match.group(1) if obspid_match else None
                longitude = float(longitude_match.group(1)) if longitude_match else None
                latitude = float(latitude_match.group(1)) if latitude_match else None
            # if obspid == None or longitude == None or latitude == None:
            #     print(f"点要素没有OBSID{obspid}或经度{longitude}或纬度{latitude}")
                if obspid and longitude and latitude:
                    if not obspid in self.points:
                        self.points[obspid] = { 'longitude': longitude, 'latitude': latitude}
                # 如果OBSID、经度和纬度中有一个为空，则记录日志
                if obspid and not longitude and not latitude:
                    error = f"点要素{obspid}缺少经度或纬度"
                    self.errorMsg.append(error)
                    print(error)
        # Step 3: 删除缺少经度或纬度的点要素
        # for obspid, coords in self.points.items():
        #     if coords['longitude'] == None or coords['latitude'] == None:
        #         del self.points[obspid]
        #         error = f"点要素{obspid}缺少经度或纬度"
        #         self.errorMsg.append(error)
        #         print(error)
        self.pointsCount = len(self.points)

    def __getRoutes(self, kml_content: str) -> None:
        # 查找所有的Placemark元素下的LineString元素下的coordinates元素，提取线要素
        root = etree.fromstring(kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            linestring = placemark.find('.//{http://www.opengis.net/kml/2.2}LineString')
            if linestring is not None:
                coordinates = linestring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
                if coordinates is not None:
                    self.routes.append(coordinates.text.strip())
        self.routesCount = len(self.routes)
    
    def __add__(self: 'KMLData', other: 'KMLData') -> 'KMLData':
        """用加法操作实现两个文件数据合并，得到一个新的字典"""
        if not isinstance(other, KMLData):
            raise TypeError("Operands must be of type 'KMLData'")
        # 创建新的KMLData对象
        new_file = KMLData()
        # 合并点要素（相同的键进行了覆盖）
        new_file.points = {**self.points, **other.points}
        new_file.pointsCount = len(new_file.points)
        # 合并线要素（列表相加并去重）
        new_file.routes = list(set(self.routes + other.routes))
        new_file.routesCount = len(new_file.routes)
        return new_file

    def __sub__(self, other: 'KMLData') -> 'KMLData':
        """用减法操作实现两个文件数据的差异，得到一个新的字典"""
        if not isinstance(other, KMLData):
            raise TypeError("文件类型必须为KML")
        # 验证一个字典的键是否是另一个字典键的子集
        if not (self.points.keys() <= other.points.keys() or other.points.keys() <= self.points.keys()):
            raise ValueError("KML文件中的点要素不是另一个的子集")
        if not (set(self.routes) <= set(other.routes) or set(other.routes) <= set(self.routes)):
            raise ValueError("KML文件中的线要素不是另一个的子集")
                # 创建新的KMLFile对象
        new_file = KMLData()
        # 计算点要素的差异
        new_file.points = {key: value for key, value in self.points.items() if key not in other.points}
        new_file.points.update({key: value for key, value in other.points.items() if key not in self.points})
        new_file.pointsCount = len(new_file.points)
        # 计算线要素的差异并去重
        new_file.routes = list(set(self.routes).symmetric_difference(set(other.routes)))
        new_file.routesCount = len(new_file.routes)
        return new_file


class KMZFile(FileAttributes, FileIO):

    SCHEMA_22 = KML_SCHEMA_22
    SCHEMA_23 = KML_SCHEMA_23

    
    def __init__(self, kmz_path: str = None):
        super().__init__(kmz_path)

        self.kml_content = None
        self.placemarks: KMLData = None
        self.resources: dict = {}

        if kmz_path is not None:
            self.read(kmz_path)

    def __validateKMZ(self, defaultSchema = "schema22") -> bool:
        """
        验证KMZ文件是否符合KML的XSD模式
        """
        if defaultSchema == "schema22":
            schema = xmlschema.XMLSchema(KMZFile.SCHEMA_22) 
        elif defaultSchema == "schema23":
            schema = xmlschema.XMLSchema(KMZFile.SCHEMA_22)
        else:
            return print("无效的输入参数")
        
        if self.kml_content is None:
            return print("KML内容为空")
        else:
            try:
                schema.validate(self.kml_content)
                logging.info("XML文件与XSD验证通过")
                return True
            except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
                logging.error("XML文件与XSD验证不符")
                # logging.error(f"{kml_content}XML文件与XSD验证不符")
                # logging.error(f"XML文件与XSD验证不符: {e}")
                return False
    
    def read(self, kmz_path: str, validate = False, defaultSchema = "schema22"):
        """ 解压 KMZ 文件并提取 KML 内容 """
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            # 查找 KML 文件
            kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
            if kml_files:
                kml_file = kml_files[0]
                # 读取 KML 文件内容
                with kmz.open(kml_file) as kml:
                    self.kml_content = kml.read()
                    self.placemarks = KMLData(self.kml_content)
                if validate:
                    self.__validateKMZ(defaultSchema)
            else:
                raise ValueError("KMZ文件中没有找到 KML文件")

    def write(self, output_path):
        """ 将 KML 数据写入 KMZ 文件 """
        if self.placemarks is None:
            raise ValueError("KMLData is empty")
        # 创建输出目录
        if os.path.exists(output_path) and os.path.isfile(output_path):
            # 验证output_path是否已.kmz结尾
            if not output_path.endswith('.kmz'):
                raise ValueError("Output file must be a KMZ file")
        # 在输出目录下创建临时目录
        temp_dir = os.path.join(output_path, "temp_kmz")
        os.makedirs(temp_dir, exist_ok=True)
        files_dir = os.path.join(temp_dir, 'files')
        os.makedirs(files_dir, exist_ok=True)
        # 创建临时KML文件
        temp_kml_file = os.path.join(output_path, "temp_combined.kml")
        # 创建输出KMZ文件
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
        shutil.copy(ICON, files_dir)
        # 压缩为KMZ文件
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as kmz:
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
        print(f"KMZ文件已保存到: {output_path}")
        return self
    
    def delete(self):
        return super().delete()
    
    def update(self, content):
        return super().update(content)
    
    def toShpfile(self, output_path):

        # 创建 SHP 文件驱动
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        if os.path.exists(output_path):
            shp_driver.DeleteDataSource(output_path)
        shp_ds = shp_driver.CreateDataSource(output_path)
        if shp_ds is None:
            raise RuntimeError("Failed to create SHP file")

        # 创建 SHP 图层
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # WGS84
        shp_layer = shp_ds.CreateLayer('points', srs, ogr.wkbPoint)

        # 创建字段
        field_name = ogr.FieldDefn('Name', ogr.OFTString)
        field_name.SetWidth(24)
        shp_layer.CreateField(field_name)

        field_longitude = ogr.FieldDefn('Longitude', ogr.OFTReal)
        shp_layer.CreateField(field_longitude)

        field_latitude = ogr.FieldDefn('Latitude', ogr.OFTReal)
        shp_layer.CreateField(field_latitude)

        # 创建要素并添加到图层
        for obspid, coords in self.placemarks.points.items():
            feature = ogr.Feature(shp_layer.GetLayerDefn())
            feature.SetField('Name', obspid)
            feature.SetField('Longitude', float(coords['longitude']))
            feature.SetField('Latitude', float(coords['latitude']))

            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(coords['longitude']), float(coords['latitude']))
            feature.SetGeometry(point)

            shp_layer.CreateFeature(feature)
            feature = None  # 清理要素

        # 清理
        shp_ds = None
        print(f"点要素已成功生成 SHP 文件: {output_path}")

    
    def __str__(self):
        super().__str__()
    
    def __add__(self, other: 'KMZFile') -> 'KMZFile':
        if not isinstance(other, KMZFile):
            raise TypeError("Operands must be of type 'KMZFile'")
        new_file = KMZFile()
        new_file.placemarks = self.placemarks + other.placemarks
        return new_file
    
    def __sub__(self, other: 'KMZFile') -> 'KMZFile':
        if not isinstance(other, KMZFile):
            raise TypeError("Operands must be of type 'KMZFile'")
        new_file = KMZFile()
        new_file.placemarks = self.placemarks - other.placemarks
        return new_file
    


class lineStyle(object):
    def __init__(self, color, width):
        self.color = color
        self.width = width

class pointStyle(object):
    def __init__(self, icon):
        self.icon = icon

        
class XMLWrapper(object):

    def __init__(self, tag_name, **attributes):
        """初始化标签的名称和可选属性"""
        self.tag_name = tag_name
        self.attributes = attributes
        self.children = []  # 用于存储子元素（支持嵌套）
        self.text = None  # 标签的文本内容

    def add_child(self, child, HTMLTag):
        """向当前标签添加子元素"""
        if isinstance(child, HTMLTag):
            self.children.append(child)
        else:
            raise ValueError("Child must be an instance of HTMLTag")

    def set_text(self, text):
        """设置标签的文本内容"""
        self.text = text

    def render_attributes(self):
        """生成标签的属性字符串"""
        if not self.attributes:
            return ""
        attributes = [f'{key}="{value}"' for key, value in self.attributes.items()]
        return " " + " ".join(attributes)

    def render(self, indent=0):
        """生成完整的 HTML 标签，包括嵌套的子标签和文本"""
        # 创建标签的开始标签
        indent_space = " " * indent
        opening_tag = f"{indent_space}<{self.tag_name}{self.render_attributes()}>"

        # 如果没有子标签或文本，直接输出开始标签和结束标签
        if not self.children and not self.text:
            return f"{opening_tag}</{self.tag_name}>"

        # 否则，添加子标签和文本内容
        closing_tag = f"</{self.tag_name}>"
        inner_content = ""

        if self.text:
            inner_content += self.text
        if self.children:
            for child in self.children:
                inner_content += "\n" + child.render(indent + 2)

        return f"{opening_tag}\n{inner_content}\n{indent_space}{closing_tag}"

    def __str__(self):
        """输出该标签的 HTML"""
        return self.render(indent=0)


class DateIterator(object):
    def __init__(self, start_date: str, direction: str = 'forward'):
        """
        __init__
            初始化迭代器，start_date为起始日期，direction为迭代方向
        args:
            start_date: 起始日期，格式为 'YYYYMMDD'
            direction: 迭代方向，可选值为 'forward' 或 'backward'
                        'forward': 从起始日期开始向后迭代，即向前（下一天）迭代
                        'backward': 从起始日期开始向前迭代，即向后（上一天）迭代
        """
        # 将字符串日期转换为 datetime 对象
        self.date = datetime.strptime(start_date, "%Y%m%d")
        self.direction = direction  # 'forward' 为下一天，'backward' 为前一天

    def __iter__(self):
        """返回迭代器自身"""
        return self

    def __next__(self):
        """根据迭代方向返回下一个日期"""
        if self.direction == 'forward':
            self.date += timedelta(days=1)
        elif self.direction == 'backward':
            self.date -= timedelta(days=1)
        else:
            raise ValueError("Invalid direction. Use 'forward' or 'backward'.")

        # 返回当前日期并格式化为字符串
        return self.date.strftime("%Y%m%d")

    def switch_direction(self):
        """切换迭代方向"""
        if self.direction == 'forward':
            self.direction = 'backward'
        else:
            self.direction = 'forward'

    def reset(self, new_start_date: str):
        """重置为新的起始日期"""
        self.date = datetime.strptime(new_start_date, "%Y%m%d")



class MapsheetDailyFile(object):

    mapsheet_info: dict = {}

    def __init__(self, mapsheetFileName: str, date: 'DateType'):

        self.mapsheetFileName:str = mapsheetFileName
        self.sequence: int = None
        self.romanName: str = self.__class__.mapsheet_info[self.sequence]['Roman Name']
        self.latinName: str = self.__class__.mapsheet_info[self.sequence]['Latin Name']

        self.currentDate: 'DateType' = date
        self.currentfilename = None
        self.currentfilepath = None
        self.currentPlacemarks: KMLData = None

        self.previousDate: 'DateType' =  None
        self.previousfilename = None
        self.previousfilepath = None
        self.previousPlacemarks: KMLData = None

        self.nextDate: 'DateType' =  None
        self.nextfilename = None
        self.nextfilepath = None

        self.dailyincreaseNum: int = None
        self.dailyincreasePlacemarks: KMLData = None

    def mapsheetValue(self, roman_name):
        """
        根据 Roman Name 从 mapsheet_info 字典中获取 Sequence 并赋值给实例变量 self.sequence
        """
        for sequence, info in self.__class__.mapsheet_info.items():
            if info['Roman Name'] == roman_name:
                self.sequence = sequence
                break
        else:
            print(f"Roman Name {roman_name} not found in mapsheet_info")

        """
        根据 sequence 从 mapsheet_info 字典中获取 Roman Name 并赋值给实例变量 self.romanName
        """
        if self.sequence in self.__class__.mapsheet_info:
            self.romanName = self.__class__.mapsheet_info[self.sequence]['Roman Name']
        else:
            print(f"Sequence {self.sequence} not found in mapsheet_info")
        if self.sequence in self.__class__.mapsheet_info:
            self.latinName = self.__class__.mapsheet_info[self.sequence]['Latin Name']
        else:
            print(f"Sequence {self.sequence} not found in mapsheet_info")

    @classmethod
    def MapInfo(cls):
        """
        从100K图幅名称信息表中获取图幅的罗马名称和拉丁名称
        """
        df = pd.read_excel(SHEET_NAMES_FILE, sheet_name="Sheet1", header=0, index_col=0)
        # 获取数据帧：筛选出 'Sequence' 列值在 SEQUENCE_MIN 和 SEQUENCE_MAX 之间的行
        filtered_df = df[ (df['Sequence'] >= SEQUENCE_MIN) & (df['Sequence'] <= SEQUENCE_MAX)]
        # # 按照 'Sequence' 列值从小到大排序
        sorted_df = filtered_df.sort_values(by='Sequence')
        # # 获取图幅名称、罗马名称和拉丁名称，并存储为字典
        # 构建以 'Sequence' 为键的字典
        cls.mapsheet_info = {
            row['Sequence']: {
                'Roman Name': row['Roman Name'],
                'Latin Name': row['Latin Name'],
                'File Name': row['File Name']
            }
            for _, row in sorted_df.iterrows()
        }

    @classmethod
    def getCurrentDateFile(cls, self):
        """
        __getCurrentDateFile 获取当天的文件，文件名格式为图幅名称+finished_points_and_tracks+日期+.kmz

        _extended_summary_ 一般情况下，当天的文件是最新的文件，因此优先查找当天的文件，但微信中可能会有多个文件，后缀名为(1),(2)...等，因此需要进一步处理
                            处理方式为：()中的数字最大的文件为当天最新的文件，或者时间最新的文件为当天最新的文件？？？

        :return: _description_
        :rtype: _type_
        """
        file_path = os.path.join(WORKSPACE, self.currentDate.yymmdd_str, "Finished points", f"{self.mapsheetFileName}_finished_points_and_tracks_{self.currentDate.yymmdd_str}.kmz")
        if os.path.exists(file_path):
            # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
            Monthdate = DateIterator(self.currentDate.yymmdd_str, 'backward')
            folder = os.path.join(WECHAT_FOLDER, self.currentDate.yyyy_mm_str)
            searchedFile_list = list_fullpath_of_files_with_keywords(WECHAT_FOLDER, [self.currentDate.strftime("%Y%m%d"), self.mapsheetFileName, "finished_points_and_tracks"]) 
            if searchedFile_list:
                self.currentfilepath = max(searchedFile_list, key=os.path.getctime)
                self.currentfilename = os.path.basename(self.currentfilepath)
                self.currentPlacemarks = KMZFile(self.currentfilepath).placemarks
                print(f"找到当天的文件: {self.currentfilename}")
        return self
    
    @classmethod
    def findPreviousFinished(cls, self):
        """
        __findPreviousFinished _summary_

        _extended_summary_

        :return: _description_
        :rtype: _type_
        """
        date = self.currentDate
        while date > datetime.strptime(TRACEBACK_DATE, "%Y%m%d"):
            date -= timedelta(days=1)
            search_date_str = date.strftime("%Y%m%d")
            # file_path = os.path.join(WORKSPACE, date_str, "Finished points", f"{self.mapsheetFileName}_finished_points_and_tracks_{date_str}.kmz")
            # if os.path.exists(file_path):
            # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
            searchedFile_list = list_fullpath_of_files_with_keywords(WECHAT_FOLDER, [search_date_str, self.mapsheetFileName, "finished_points_and_tracks"]) 
            if searchedFile_list:
                latestFile = max(searchedFile_list, key=os.path.getctime)
                print(f"找到前一天的文件: {latestFile}")
                self.previousDate = date
                self.previousfilename = os.path.basename(latestFile)
                self.previousfilepath = latestFile
                self.previousPlacemarks = KMZFile(latestFile).placemarks
        return self
    
    @classmethod
    def findNextPlan(cls, self):
        """
        findNextPlan 通常是查找第二天天的计划文件：
                     或周五-周六休息，周四会查找周六/周日的计划文件，因此为了冗余日期，TRACEFORWARD_DAYS = 5，即向前查找5天，找到最近的一个计划文件
        """
        date = self.currentDate
        endDate = datetime.strptime(self.currentDate, "%Y%m%d") + timedelta(days=TRACEFORWARD_DAYS)
        while date < endDate:
            date += timedelta(days=1)
            search_date_str = date.strftime("%Y%m%d")
            # file_path = os.path.join(WORKSPACE, date_str, "Finished points", f"{self.mapsheetFileName}_finished_points_and_tracks_{date_str}.kmz")
            # if os.path.exists(file_path):
            # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
            searchedFile_list = list_fullpath_of_files_with_keywords(WECHAT_FOLDER, [search_date_str, self.mapsheetFileName, "plan_tracks"]) 
            if searchedFile_list:
                latestFile = max(searchedFile_list, key=os.path.getctime)
                print(f"找到工作计划: {latestFile}")
            else:
                print(f"{TRACEFORWARD_DAYS}内无工作计划")
        return self
    

    
class CurrentDateFiles(object):
    """
    """
    def __init__(self, currentFiles: dict):
        self.currentDateFiles: dict = currentFiles

    def __contains__(self, key):
        return key in self.currentDateFiles
    
    def toExcel(self):
        pass

    def toShpfile(self):
        # 合并当天的所有文件，生成一个shp文件
        pass

    def totalPoints(self):
        # 计算当天所有文件的点要素总数
        pass

    def totalRoutes(self):
        # 计算当天所有文件的线要素总数
        pass

    def totalFiles(self):
        pass

    
class ExcelHandler(object):

    def get_columns_in_range(df, minSequenceValue, maxSequenceValue) -> list:
        # 根据列“Sequence”的值大小，输出指定值区间的相应“Roman Name”
        filtered_df = df[ (df['Sequence'] >= minSequenceValue) & (df['Sequence'] <= maxSequenceValue) ]
        # 按照 'Sequence' 列值从小到大排序
        sorted_df = filtered_df.sort_values(by='Sequence')
        return (sorted_df['Roman Name'].tolist(), sorted_df['File Name'].tolist())

    def create_daily_statistics_excel(date_str: str, romanNames: list, excel_filename: str):
        """_summary_

        Args:
            date_str (str): 日期字符串，格式为“YYYY/MM/DD”
            excel_filename (str): Excel文件路径
            minSequenceValue (int): 最小填图序列号
            maxSequenceValue (int): 最大填图序列号

        Returns:
            _type_: 无
        """
        excel_filename = currentDate + "点统计.xlsx"

        # 计算输出表格的行数和列数
        maxTableRows, maxTableColumns = len(romanNames) + 4, 4
        # 每日统计点文件的表头（前三行）
        daily_stat_header1 = ['Date', date_str]
        daily_stat_header2 = ['Map sheet name',
                            'Regular observation points finished',
                            'Field points on revised route'
                            ]
        daily_stat_header3 = ['', '', 'Added observation points',
                            'Added Structure points, photo points, mineralization points'
                            ]
        # 每日统计点文件的合计行（最后一行）
        daily_stat_footer = ['Today', '', '', '']

        # 创建一个新的 Excel 文件
        try:
            book = load_workbook(excel_filename)
        except FileNotFoundError:
            book = Workbook()

        sheet = book.active
        sheet.title = "Daily Statistics"
        # 写入表头到前三行
        for col_num, value in enumerate(daily_stat_header1, start=1):
            sheet.cell(row=1, column=col_num, value=value)
        for col_num, value in enumerate(daily_stat_header2, start=1):
            sheet.cell(row=2, column=col_num, value=value)
        for col_num, value in enumerate(daily_stat_header3, start=1):
            sheet.cell(row=3, column=col_num, value=value)
        # 写入表尾到最后一行
        for col_num, value in enumerate(daily_stat_footer, start=1):
            sheet.cell(row=maxTableRows, column=col_num, value=value)
        # 从第四行起，写入图幅罗马名称
        for i, value in enumerate(romanNames, start=4):
            sheet.cell(row=i, column=1, value=value)

        # 设置字体样式
        # 设置表头字体样式
        font_header = Font(
            name='Calibri',
            size=12,
            bold=True,
            italic=False,
            vertAlign=None,
            underline='none',
            strike=False,
            color='00000000'
        )
        # 设置正文字体样式
        font = Font(
            name='Calibri',
            size=11,
            bold=False,
            italic=False,
            vertAlign=None,
            underline='none',
            strike=False,
            color='00000000'
        )

        border = Border(
            left=Side(border_style='thin', color='FF000000'),
            right=Side(border_style='thin', color='FF000000'),
            top=Side(border_style='thin', color='FF000000'),
            bottom=Side(border_style='thin', color='FF000000'),
            diagonal=Side(border_style='thin', color='FF000000'),
            diagonal_direction=0,
            outline=Side(border_style='thin', color='FF000000'),
            vertical=Side(border_style='thin', color='FF000000'),
            horizontal=Side(border_style='thin', color='FF000000')
        )

        # 将字体样式应用到指定单元格
        # 前三行字体为表头字体
        for row in range(1, 4):
            for col in range(1, maxTableColumns + 1):
                cell = sheet.cell(row, column=col)
                cell.font = font_header
        # 最后一行字体为表头字体
        for col in range(1, maxTableColumns + 1):
            cell = sheet.cell(maxTableRows, column=col)
            cell.font = font_header
        # 其他字体为正文字体
        for row in range(4, maxTableRows):
            for col in range(1, maxTableColumns + 1):
                cell = sheet.cell(maxTableRows-1, column=col)
                cell.font = font

        # 将单元格格式应用到指定单元格
        for row in range(maxTableRows):
            for col in range(maxTableColumns):
                cell = sheet.cell(row=row+1, column=col+1)
                cell.border = border

        # 设置多列的宽度，adjusted_width是单元格宽度，比最大长度多2
        for column in sheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except Exception:
                    pass
            adjusted_width = (max_length + 2)  # 设置单元格宽度，比最大长度多2
            sheet.column_dimensions[column[0].column_letter].width = adjusted_width

        # 创建一个居中对齐的对象
        center_aligned = Alignment(horizontal='center', vertical='center')
        # 将居中对齐应用到指定单元格
        for row in sheet['A1:D3']:  # 修改这个范围以适应你的需要
            for cell in row:
                cell.alignment = center_aligned
        for row in range(4, maxTableRows):
            for col in range(2, maxTableColumns):
                cell = sheet.cell(row, column=col)
                cell.alignment = center_aligned
        for row in range(maxTableRows + 1):
            for col in range(1, maxTableColumns + 1):
                cell = sheet.cell(row+1, column=col)
                cell.alignment = center_aligned

        # 设置合计行的公式
        sheet.cell(row=maxTableRows, column=2).value = f"=SUM(B4:B{maxTableRows-1})"
        sheet.cell(row=maxTableRows, column=3).value = f"=SUM(C4:C{maxTableRows-1})"
        sheet.cell(row=maxTableRows, column=4).value = f"=SUM(D4:D{maxTableRows-1})"

        sheet.merge_cells('B1:D1')
        sheet.merge_cells('C2:D2')
        sheet.merge_cells('A2:A3')
        sheet.merge_cells('B2:B3')

        # 保存工作簿
        book.save(excel_filename)
        return print(f"创建每日统计点 {excel_filename} 空表成功。")

    
    
class DataSubmition(object):
    """
    根据COLLECTION_WEEKDAYS列表，在每周的某一天：
    1. 输出shp文件
    2. 在制图工程文件夹下创建目录，并拷贝截止当天的shp
    3. 拷贝一周前的shp文件（或kmz文件）
    4. 生成一周新增的shp文件
    5. 调用ArcPy，生成一周报告
    """
    SHP_EXTENSIONS = ['.shp', '.shx', '.dbf', '.prj']

    def __init__(self, date: 'DateType', points_dict: dict):

        self.date = date
        self.pointDict: dict = points_dict

    def __pointDictValidation(self):
        """
        检查点要素字典的有效性
        """
        pass

    def toShp(self):
        output_shp_file = os.path.join(WORKSPACE, self.date.yymm_str, self.date.yyyymmdd_str, f"GMAS_points_until_{self.date.yyyymmdd_str}.shp")
        # 清理shp文件和zip文件：如果hp文件和zip文件已存在，则删除
        if os.path.exists(output_shp_file.replace('.shp', '.zip')):
            os.remove(output_shp_file.replace('.shp', '.zip'))
            logger.info(f"已删除旧的ZIP文件: {output_shp_file.replace('.shp', '.zip')}")
        if os.path.exists(output_shp_file):
            for ext in DataSubmition.SHP_EXTENSIONS:
                os.remove(output_shp_file.replace('.shp', ext))
            logger.info(f"已删除旧的SHP文件: {output_shp_file}")

        # 创建 SHP 文件驱动
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        if os.path.exists(output_shp_file):
            shp_driver.DeleteDataSource(output_shp_file)
        shp_ds = shp_driver.CreateDataSource(output_shp_file)
        if shp_ds is None:
            raise RuntimeError("Failed to create SHP file")
        # 创建 SHP 图层
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # WGS84
        shp_layer = shp_ds.CreateLayer('points', srs, ogr.wkbPoint)
        # 创建字段
        field_name = ogr.FieldDefn('Name', ogr.OFTString)
        field_name.SetWidth(24)
        shp_layer.CreateField(field_name)
        # 创建经纬度字段
        field_longitude = ogr.FieldDefn('Longitude', ogr.OFTReal)
        shp_layer.CreateField(field_longitude)
        field_latitude = ogr.FieldDefn('Latitude', ogr.OFTReal)
        shp_layer.CreateField(field_latitude)
        # 创建要素并添加到图层
        for obspid, coords in self.pointDict.items():
            feature = ogr.Feature(shp_layer.GetLayerDefn())
            feature.SetField('Name', obspid)
            feature.SetField('Longitude', float(coords['longitude']))
            feature.SetField('Latitude', float(coords['latitude']))
            # 创建点要素
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(coords['longitude']), float(coords['latitude']))
            feature.SetGeometry(point)
            # 添加要素
            shp_layer.CreateFeature(feature)
            feature = None  # 清理要素
        # 清理
        shp_ds = None
        print(f"点要素已成功生成SHP文件: {self.output_shp_file}")

        # 将shp文件压缩为zip文件
        zip_file = os.path.join(WORKSPACE, self.date.yyyymm_str, self.date.yyyymmdd_str, f"GMAS_points_until_{self.date.yyyymmdd_str}.zip")
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ext in DataSubmition.SHP_EXTENSIONS:
                zipf.write(output_shp_file.replace('.shp', ext), os.path.basename(output_shp_file).replace('.shp', ext))
        logger.info(f"SHP文件已压缩为 ZIP 文件: {zip_file}")

        # 在制图工程文件夹下创建新文件夹
        latest_files_folder = os.path.join(WORKSPACE, "Finished observation points of Group1", f"Finished_ObsPoints_Until_{self.date.yyyymmdd_str}")
        # 将shp文件及相关文件(.shp, .shx, .dbf, .prj)移动至新文件夹
        weekdayDir = os.path.join(WORKSPACE, MAP_PROJECT_FOLDER, f"Finished_ObsPoints_Until_{self.date.yyyymmdd_str}")
        if os.path.exists(weekdayDir):
            shutil.rmtree(weekdayDir)
        os.makedirs(weekdayDir, exist_ok=True)
        logger.info(f"创建新文件夹: {latest_files_folder}")
        for ext in DataSubmition.SHP_EXTENSIONS:
            shutil.copy(output_shp_file.replace('.shp', ext), latest_files_folder)
        logger.info(f"已拷贝今日的 SHP 文件及相关文件至: {latest_files_folder}")

        # 尝试从多种路径读取一周前的文件(zip，shp)
        one_week_ago = DateType(date_str=(self.date.date_datetime - timedelta(days=7)))
        # 从制图工程文件夹中读取一周前的shp文件
        one_week_ago_shpfile = os.path.join(WORKSPACE, MAP_PROJECT_FOLDER, f"Finished_ObsPoints_Until_{one_week_ago.yyyymmdd_str}", f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.shp")
        # 从存档文件夹中读取一周前的zip文件
        one_week_ago_zipfile = os.path.join(WORKSPACE, one_week_ago.yyyymm_str, one_week_ago.yyyymmdd_str, f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.zip")
        # 从存档文件夹中读取一周前的kmz文件
        # one_week_ago_kmzfile = os.path.join(WORKSPACE, one_week_ago.yyyymm_str, one_week_ago.yyyymmdd_str, f"GMAS_Points_and_tracks_until_{one_week_ago.yyyymmdd_str}.kmz")

        #TODO: 也可以尝试从kmz文件中读取一周前的点要素
        match (os.path.exists(one_week_ago_shpfile), os.path.exists(one_week_ago_zipfile)):
            case (True, _):
                # 拷贝一周前的shp文件至制图文件夹中
                for ext in DataSubmition.SHP_EXTENSIONS:
                    shutil.copy(one_week_ago_shpfile.replace('.shp', ext), latest_files_folder)
                logger.info(f"已拷贝一周前的 SHP 文件及相关文件至: {latest_files_folder}")
            case (False, True):
                # 解压一周前的zip文件至制图文件夹中
                with zipfile.ZipFile(one_week_ago_zipfile, 'r') as zip_ref:
                    zip_ref.extractall(latest_files_folder)
                logger.info(f"已解压一周前的 ZIP 文件到: {latest_files_folder}")
            case (False, False):
                logger.error(f"一周前的文件不存在: {one_week_ago_zipfile}\n{one_week_ago_shpfile}")
                return False

        one_week_ago_points_dict = self.read_shp_to_dict(os.path.join(latest_files_folder, f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.shp"))
        count_one_week_ago_points_dict = len(one_week_ago_points_dict)
        logger.info(f"一周前{one_week_ago.yyyymmdd_str}的点要素总数: {count_one_week_ago_points_dict}")
        diff_dict = {k: v for k, v in self.pointDict.items() if k not in one_week_ago_points_dict}
        diff_dict_num = len(diff_dict)
        logger.info(f"去掉重复项后的点要素: {diff_dict_num}")

        one_week_ago_nextday = DateType(date_str=(self.date.date_datetime - timedelta(days=6)))

        weekly_increase_shp_file = os.path.join(latest_files_folder, f"GMAS_points_{one_week_ago.yyyymmdd_str}_{self.date.yyyymmdd_str}.shp")
        self.generate_shp_from_points(diff_dict, weekly_increase_shp_file)

        logger.info(f"GMAS_points_{one_week_ago.yyyymmdd_str}_{self.date.yyyymmdd_str}.shp创建成功")

    def generate_shp_from_points(points_dict, shp_file):
        # 创建 SHP 文件驱动
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        if os.path.exists(shp_file):
            shp_driver.DeleteDataSource(shp_file)
        shp_ds = shp_driver.CreateDataSource(shp_file)
        if shp_ds is None:
            raise RuntimeError("Failed to create SHP file")

        # 创建 SHP 图层
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # WGS84
        shp_layer = shp_ds.CreateLayer('points', srs, ogr.wkbPoint)

        # 创建字段
        field_name = ogr.FieldDefn('Name', ogr.OFTString)
        field_name.SetWidth(24)
        shp_layer.CreateField(field_name)

        field_longitude = ogr.FieldDefn('Longitude', ogr.OFTReal)
        shp_layer.CreateField(field_longitude)

        field_latitude = ogr.FieldDefn('Latitude', ogr.OFTReal)
        shp_layer.CreateField(field_latitude)

        # 创建要素并添加到图层
        for obspid, coords in points_dict.items():
            feature = ogr.Feature(shp_layer.GetLayerDefn())
            feature.SetField('Name', obspid)
            feature.SetField('Longitude', float(coords['longitude']))
            feature.SetField('Latitude', float(coords['latitude']))

            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(coords['longitude']), float(coords['latitude']))
            feature.SetGeometry(point)

            shp_layer.CreateFeature(feature)
            feature = None  # 清理要素

        # 清理
        shp_ds = None
        print(f"点要素已成功生成 SHP 文件: {shp_file}")

    def read_shp_to_dict(shp_file):
        points_dict = {}

        # 打开 SHP 文件
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        shp_ds = shp_driver.Open(shp_file, 0)  # 0 表示只读模式
        if shp_ds is None:
            raise RuntimeError(f"Failed to open SHP file: {shp_file}")

        # 获取图层
        shp_layer = shp_ds.GetLayer()

        # 遍历要素
        for feature in shp_layer:
            obspid = feature.GetField('Name')
            longitude = feature.GetField('Longitude')
            latitude = feature.GetField('Latitude')

            points_dict[obspid] = {
                'longitude': longitude,
                'latitude': latitude
            }

        # 清理
        shp_ds = None
        print(f"已成功读取 SHP 文件: {shp_file}")

        return points_dict


@dataclass
class DateType:

    date_datetime: datetime = None
    yyyymmdd_str: str = ''
    yymmdd_str: str = ''
    yyyy_str: str = ''
    yyyy_mm_str: str = ''
    yy_str: str = ''
    mm_str: str = ''
    dd_str: str = ''
    yymm_str: str = ''

    def __post_init__(self):
        if self.yyyymmdd_str:
            self.date_datetime = datetime.strptime(self.yyyymmdd_str, "%Y%m%d")
        elif self.date_datetime:
            self.yyyymmdd_str = self.date_datetime.strftime("%Y%m%d")                                       # 20211231
        self.yymmdd_str = self.date_datetime.strftime("%y%m%d")                                             # 211231
        self.yyyymm_str = self.date_datetime.strftime("%Y%m")                                               # 202112
        self.yyyy_str = self.date_datetime.strftime("%Y")                                                   # 2021
        self.yy_str = self.date_datetime.strftime("%y")                                                     # 21
        self.mm_str = self.date_datetime.strftime("%m")                                                     # 12
        self.dd_str = self.date_datetime.strftime("%d")                                                     # 31
        self.yyyy_mm_str = self.date_datetime.strftime("%Y") + '-' + self.date_datetime.strftime("%m")      # 2021-12
        self.yymm_str = self.date_datetime.strftime("%y%m")                                                 # 2112


if __name__ == "__main__":

    currentDate = DateType(yyyymmdd_str="20241102")

    file = KMZFile(r'D:\RouteDesigen\202412\20241210\Finished points\Ad_Dawadami_finished_points_and_tracks_20241204.kmz')


