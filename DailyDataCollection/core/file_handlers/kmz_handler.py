"""
KMZ文件处理器

专门处理KMZ文件的读取、写入和转换
"""

import os
import stat
import shutil
import zipfile
import pyzipper
import xmlschema
import logging
from typing import Optional, Union
from lxml import etree
from osgeo import ogr, osr

from ..data_models.file_attributes import FileAttributes
from ..data_models.observation_data import ObservationData
from .base_io import GeneralIO

# 导入配置
from config.config_manager import ConfigManager

config_manager = ConfigManager()
KML_SCHEMA_22 = config_manager.get('resources.kml_schema_22', '')
KML_SCHEMA_23 = config_manager.get('resources.kml_schema_23', '')
ICON_1 = config_manager.get('resources.icon_1', '')

# 创建 logger 实例
logger = logging.getLogger('KMZ Handler')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class KMZFile(FileAttributes, GeneralIO):
    """KMZ文件处理类，支持KMZ文件的读取、写入和转换"""

    SCHEMA_22 = KML_SCHEMA_22
    SCHEMA_23 = KML_SCHEMA_23

    def __init__(self, filepath: Optional[str] = None, placemarks: Optional[ObservationData] = None):
        super().__init__(filepath)
        
        self.filepath = filepath
        if self.filepath:
            if self.filepath.endswith(".kmz"):
                self.filepath = filepath
            else:
                self.filepath = None
                logger.error(f"文件后缀名无效: {filepath}")
        
        self._placemarks: Optional[ObservationData] = placemarks
        self._kml_content: Optional[str] = None
        self._resources: dict = {}
        self._points: dict = {}
        self._pointsCount: int = 0
        self._routes: list = []
        self._routesCount: int = 0
        # 用于存储错误信息
        self.__errorMsg: list = []

        if self.filepath:
            self.read()

        if placemarks:
            self._points = self._placemarks.points
            self._pointsCount = self._placemarks.pointsCount
            self._routes = self._placemarks.routes
            self._routesCount = self._placemarks.routesCount
            # 如果self._placemarks.errorMsg是一个列表且不为空, 则将其添加到__errorMsg中
            if isinstance(self._placemarks.errorMsg, list) and self._placemarks.errorMsg:
                self.__errorMsg.extend(self._placemarks.errorMsg)
                print("KMZ初始化时发现的错误", self.errorMsg)

    def __validateKMZ(self, defaultSchema: str = "schema22") -> bool:
        """验证KMZ文件是否符合KML的XSD模式"""
        if defaultSchema == "schema22":
            schema = xmlschema.XMLSchema(KMZFile.SCHEMA_22) 
        elif defaultSchema == "schema23":
            schema = xmlschema.XMLSchema(KMZFile.SCHEMA_22)
        else:
            return print(f"无效的输入参数, 将使用默认的'{defaultSchema}'")
        
        if self._kml_content is None:
            return print("KML内容为空")
        else:
            try:
                schema.validate(self._kml_content)
                logger.info(f"XML文件与XSD'{defaultSchema}'验证通过")
                return True
            except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
                warning = f"XML文件与XSD'{defaultSchema}'验证不符"
                logger.warning(warning)
                self.__errorMsg.extend([warning])
                return False

    def read(self, filepath: Optional[str] = None, validate: bool = False, defaultSchema: str = "schema22") -> bool:
        """解压 KMZ 文件并提取 KML 内容"""
        if filepath is not None:
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                logger.error(f"文件路径不存在: {filepath}")
                return False
            if not filepath.endswith(".kmz"):
                logger.error(f"文件后缀名无效: {filepath}")
                return False
            if self.filepath is None:
                self.filepath = filepath
        elif self.filepath is None:
            logger.error("文件路径为空")
            return False
        else:
            filepath = self.filepath
        
        try:
            with pyzipper.AESZipFile(filepath, 'r') as kmz:
                # 查找 KML 文件
                kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
                if kml_files:
                    kml_file = kml_files[0]
                    # 读取 KML 文件内容
                    with kmz.open(kml_file) as kml:
                        self._kml_content = kml.read()
                        # 验证KML文件是否符合XSD模式
                        if validate:
                            self.__validateKMZ(defaultSchema)
                        # 解析KML内容
                        placemarks = ObservationData(kml_content=self._kml_content)
                        self._points = placemarks.points
                        self._pointsCount = placemarks.pointsCount
                        self._routes = placemarks.routes
                        self._routesCount = placemarks.routesCount
                        if placemarks.errorMsg:
                            self.__errorMsg.extend(placemarks.errorMsg)
                        self._placemarks = placemarks
                        # 删除KML内容, 释放内存
                        del self._kml_content
                else:
                    logger.error("在KMZ文件中没有找到 KML文件")
                    return False

        except Exception as e:
            error = f"读取文件时发生错误: {e}"
            logger.error(error)
            self.__errorMsg.append(error)
            return False
        
        return True

    def write(self, file_type: str = 'kmz') -> bool:
        """写入文件"""
        if self.filepath is not None:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            if file_type == 'kmz':
                if self.__toKMZ(self.filepath):
                    print(f"KMZ文件已保存到: {self.filepath}")
                    return True
                else:
                    print(f"KMZ文件保存失败")
                    logger.error(f"KMZ文件保存失败{self.filepath}")
                    return False
            elif file_type == 'shp':
                if self.__toShp(self.filepath):
                    print(f"SHP文件已保存到: {self.filepath}")
                    return True
                else:
                    print(f"SHP文件保存失败")
                    logger.error(f"SHP文件保存失败{self.filepath}")
                    return False
            else:
                logger.error(f"无效的输出文件类型: {file_type}")
                return False
        else:
            print("文件路径为空")
            logger.error("文件路径为空")
            return False

    def write_as(self, newpath: str) -> bool:
        """另存为指定路径"""
        if os.path.exists(newpath) and os.path.isfile(newpath):
            logger.warning(f"文件路径{newpath}将覆盖原文件")
        
        filetype = os.path.splitext(newpath)[1].lower()
        if filetype == '.kmz':
            if self.__toKMZ(newpath):
                print(f"KMZ文件已保存到: {newpath}")
                return True
            else:
                print(f"KMZ文件保存失败")
                logger.error(f"KMZ文件保存失败{newpath}")
                return False
        elif filetype == '.shp':
            if self.__toShp(newpath):
                print(f"SHP文件已保存到: {newpath}")
                return True
            else:
                print(f"SHP文件保存失败")
                logger.error(f"SHP文件保存失败{newpath}")
                return False
        else:
            print(f"无效的输出文件类型: {filetype}")
            logger.error(f"无效的输出文件类型: {filetype}")
            return False

    def delete(self) -> bool:
        """删除文件"""
        return super().delete()

    def update(self, content) -> bool:
        """更新文件内容"""
        return super().update(content)

    def __toKMZ(self, output_path: str) -> bool:
        """将 KML 数据写入 KMZ 文件"""
        if self.placemarks is None:
            logger.error("ObservationData is empty")
            return False
        
        # 创建输出目录
        if os.path.exists(output_path) and os.path.isfile(output_path):
            if not output_path.endswith('.kmz'):
                logger.error("Output file must be a KMZ file")
                return False
        
        output_dir = os.path.dirname(output_path)
        temp_dir = os.path.join(output_dir, "temp_kmz")
        os.makedirs(temp_dir, exist_ok=True)
        files_dir = os.path.join(temp_dir, 'files')
        os.makedirs(files_dir, exist_ok=True)
        
        # 创建临时KML文件
        temp_kml_file = os.path.join(output_dir, "temp_combined.kml")
        
        # 根节点
        document = etree.Element("Document")
        
        # 添加线样式
        style = etree.SubElement(document, "Style", id="lineStyle")
        line_style = etree.SubElement(style, "LineStyle")
        color = etree.SubElement(line_style, "color")
        color.text = "ff000000"  # 黑色, 格式为 AABBGGRR
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
        if ICON_1 and os.path.exists(ICON_1):
            shutil.copy(ICON_1, files_dir)
            os.chmod(files_dir, stat.S_IWRITE | stat.S_IREAD)
        
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
        return True

    def __toShp(self, output_path: str) -> bool:
        """转换为SHP文件"""
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
            # 创建点要素
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(coords['longitude']), float(coords['latitude']))
            feature.SetGeometry(point)
            # 添加要素
            shp_layer.CreateFeature(feature)
            feature = None  # 清理要素
        
        # 清理
        shp_ds = None
        print(f"点要素已成功生成 SHP 文件: {output_path}")
        return True

    def __getattr__(self, name):
        """动态获取属性"""
        if name == 'placemarks':
            return self._placemarks
        elif name == 'points':
            return self._points
        elif name == 'pointsCount':
            return self._pointsCount
        elif name == 'routes':
            return self._routes
        elif name == 'routesCount':
            return self._routesCount
        elif name == 'errorMsg':
            if self.__errorMsg:
                return self.__errorMsg
            else:
                return None
        else:
            return super().__getattr__(name)

    def __str__(self) -> str:
        """字符串表示"""
        return super().__str__()

    def __add__(self, other: 'KMZFile') -> 'KMZFile':
        """合并两个KMZ文件"""
        if not isinstance(other, KMZFile):
            raise TypeError("Operands must be of type 'KMZFile'")
        new_file = KMZFile()
        new_file._placemarks = self.placemarks + other.placemarks
        return new_file

    def __sub__(self, other: 'KMZFile') -> 'KMZFile':
        """计算两个KMZ文件的差异"""
        if not isinstance(other, KMZFile):
            raise TypeError("Operands must be of type 'KMZFile'")
        new_file = KMZFile()
        new_file._placemarks = self.placemarks - other.placemarks
        return new_file
