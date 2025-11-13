"""
观测数据模型

包含观测数据的处理和验证逻辑
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from lxml import etree

# 创建 logger 实例
logger = logging.getLogger('Observation Data')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class ObservationData:
    """观测数据类，用于处理KML文件中的观测点和路径数据"""

    OSPID_PATTERN = r'\d{5}[A-Za-z]\d{3}'
    LONGITUDE_PATTERN = r'<td>Longitude</td>\s*<td>(-?\d+\.\d+)</td>'
    LATITUDE_PATTERN = r'<td>Latitude</td>\s*<td>(-?\d+\.\d+)</td>'

    points: Dict[str, Dict[str, float]] = field(default_factory=dict)
    pointsCount: int = 0
    routes: List[str] = field(default_factory=list)
    routesCount: int = 0

    __lablePoints: Dict[str, Dict[str, float]] = field(default_factory=dict)
    __ospidPoints: Dict[str, Dict[str, float]] = field(default_factory=dict)
    __errorMsg: List[str] = field(default_factory=list)

    kml_content: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.kml_content:
            self.__getPoints()
            self.__getRoutes()
            # 在解析KML内容后删除KML内容, 以释放内存
            del self.kml_content
            # 检查点号
            self.__pointCheck()

    def __getPoints(self) -> None: 
        """从KML内容中提取点要素, 包括OBSID、经度和纬度"""
        root = etree.fromstring(self.kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        
        # Step 1: 通过Point元素提取点要素
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
            if point is not None:
                name = placemark.find('.//{http://www.opengis.net/kml/2.2}name')
                if name is not None and name.text:
                    obspid_pattern = re.compile(ObservationData.OSPID_PATTERN)
                    if obspid_pattern.match(name.text):
                        obspid = name.text
                        coordinates = point.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.split(',')
                        longitude, latitude = coordinates[0], coordinates[1]
                        if obspid and longitude and latitude:
                            if not obspid in self.__lablePoints:
                                self.__lablePoints[obspid] = {'longitude': float(longitude), 'latitude': float(latitude)}
                            else:
                                error = f"点要素{obspid}的Label中存在OBSID重复(The Lable of Point feature {obspid} is dupulicated)"
                                self.__errorMsg.append(error)
                    else:
                        error = f"点要素{name.text}的标签格式不符合OBSID命名规范(The name pattern of the point feature '{name.text}' is not right)"
                        self.__errorMsg.append(error)

        # Step 2: 通过Description元素提取点要素
        for description in root.findall('.//{http://www.opengis.net/kml/2.2}description'):
            if description is not None and description.text:
                obspidPattern = re.compile(ObservationData.OSPID_PATTERN)
                longitudePattern = re.compile(ObservationData.LONGITUDE_PATTERN)
                latitudePattern = re.compile(ObservationData.LATITUDE_PATTERN)

                obspid_match = obspidPattern.search(description.text)
                longitude_match = longitudePattern.search(description.text)
                latitude_match = latitudePattern.search(description.text)

                obspid = obspid_match.group(0) if obspid_match else None
                longitude = float(longitude_match.group(1)) if longitude_match else None
                latitude = float(latitude_match.group(1)) if latitude_match else None

                if obspid and longitude and latitude:
                    if not obspid in self.__ospidPoints:
                        self.__ospidPoints[obspid] = { 'longitude': longitude, 'latitude': latitude}
                    else:
                        error = f"点要素{obspid}的属性表中存在OBSID重复(Dupulicated point feature {obspid} in attributed table)"
                        self.__errorMsg.append(error)

                # 如果OBSID、经度和纬度中有一个为空, 则记录日志
                if obspid and (not longitude and not latitude):
                    error = f"点要素{obspid}的属性表中缺少经度值和纬度值(Missing Longtitude or Lattitude value in the attribue table of point feature {obspid})"
                    self.__errorMsg.append(error)
                elif obspid and not longitude and latitude:
                    error = f"点要素{obspid}的属性表中缺少经度值(Missing Longtitude value in the attribue table of point feature {obspid})"
                    self.__errorMsg.append(error)
                elif obspid and longitude and not latitude:
                    error = f"点要素{obspid}的属性表中缺少纬度值(Missing Lattitude value in the attribue table of point feature {obspid})"
                    self.__errorMsg.append(error)

        # 合并两个字点典, 如果有重复的键, 则覆盖
        self.points = {**self.__lablePoints, **self.__ospidPoints}
        self.pointsCount = len(self.points)

    def __getRoutes(self) -> None:
        """从KML内容中提取路径要素"""
        root = etree.fromstring(self.kml_content, parser=etree.XMLParser(encoding='utf-8',recover=True))
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            linestring = placemark.find('.//{http://www.opengis.net/kml/2.2}LineString')
            if linestring is not None:
                coordinates = linestring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
                if coordinates is not None:
                    self.routes.append(coordinates.text.strip())
        self.routesCount = len(self.routes)

    def __pointCheck(self) -> bool:
        """检查点要素的完整性和连续性"""
        # 通过第self.points字典的键, 第6位解析组号并存储在字典中
        obsptidStatistics_dict = {}
        for key in self.points:
            teamkey = key[5]
            if teamkey not in obsptidStatistics_dict:
                obsptidStatistics_dict[teamkey] = []
            obsptidStatistics_dict[teamkey].append(key)

        # 分别计算第六位相同的个数（每组的点数）, 以及第六位相同的all_matches列表元素后三位是否连续
        statistics_dict = {}
        for key, values in obsptidStatistics_dict.items():
            count = len(values)
            values.sort(key=lambda x: int(x[-3:]))  # 按后三位数字排序
            is_duplicate = len(values) != len(set(values))  # 检查是否有重复的点号
            is_consecutive = all(int(values[i][-3:]) + 1 == int(values[i + 1][-3:]) for i in range(len(values) - 1))
            
            # 遍历数组, 检查相邻元素之间的差是否为1
            pointValues = [int(value[-3:]) for value in values]
            gaps = []
            for i in range(1, count):
                if pointValues[i] - pointValues[i - 1] != 1:
                    gaps.append((f"{key}{pointValues[i - 1]}", f"{key}{pointValues[i]}"))
            
            # 如果有间断, 输出间断的位置
            if gaps:
                msg = f"组{key}的点号间断位置: {gaps}(Work squad {key} number mark break at) "
            else:
                msg = None
                
            max_value = max(values, key=lambda x: int(x[-3:]))
            new_key = key + "组"
            statistics_dict[new_key] = {
                "完成点数": count, 
                "最大列表元素": max_value, 
                "点号是否重复": is_duplicate, 
                "点号是否连续": is_consecutive, 
                "间断位置": msg
            }

        # 检查所有"点号是否连续"是否为 True
        all_consecutive = all(value["点号是否连续"] for key, value in statistics_dict.items())
        # 检查所有"点号是否重复"是否为 False
        all_not_duplicate = all(not value["点号是否重复"] for key, value in statistics_dict.items())
        # 累加所有"完成点数"
        total_completed_points = sum(value["完成点数"] for key, value in statistics_dict.items())
        # 检查总完成点数是否等于所有"完成点数相加"
        total_points_match = total_completed_points == len(self.points)
        
        # 如果以上条件均满足, 则输出"验证通过"
        if all_consecutive and all_not_duplicate and total_points_match:
            return True
        else:
            print(f"\nOBSID数据验证失败")
            print(statistics_dict, "\n")
            self.__errorMsg.append(str(statistics_dict))
            return False

    def __add__(self, other: 'ObservationData') -> 'ObservationData':
        """用加法操作实现两个文件数据合并, 得到一个新的字典"""
        if not isinstance(other, ObservationData):
            raise TypeError("Operands must be of type 'ObservationData'")
        
        # 创建新的ObservationData对象
        new_file = ObservationData()
        # 合并点要素（相同的键进行了覆盖）
        new_file.points = {**self.points, **other.points}
        new_file.pointsCount = len(new_file.points)
        # 合并线要素（列表相加并去重）
        new_file.routes = list(set(self.routes + other.routes))
        new_file.routesCount = len(new_file.routes)
        return new_file

    def __sub__(self, other: 'ObservationData') -> 'ObservationData':
        """用减法操作实现两个文件数据的差异, 得到一个新的字典"""
        # 创建新的ObservationData对象
        new_file = ObservationData()

        if not isinstance(other, ObservationData):
            error = f"数据类型必须是'ObservationData'"
            self.__errorMsg.append(error)
            logger.error(error)
            return None
            
        # 验证一个字典的键是否是另一个字典键的子集
        if not (other.points.keys() <= self.points.keys()):
            error = f"两个KML文件中的点要素不是另一个的子集"
            self.__errorMsg.append(error)
            logger.error(error)
            return new_file

        # 点要素的顺序减法
        new_file.points = {
            key: value for key, value in self.points.items() if key not in other.points
        }
        
        # 根据字典中元素差异判断是否今日点有误
        pointCount = len(set(self.points.keys())) - len(set(other.points.keys()))
        if pointCount < 0:
            error = f"今日文件有误，点数少于上一天，今日增加点为负数: {pointCount}"
            self.__errorMsg.append(error)
            logger.error(error)
            return new_file

        new_file.pointsCount = len(new_file.points)

        # 线要素的顺序减法
        new_file.routes = [route for route in self.routes if route not in other.routes]
        new_file.routesCount = len(new_file.routes)
        
        return new_file
    
    @property
    def errorMsg(self) -> Union[List[str], None]:
        """获取错误消息"""
        if isinstance(self.__errorMsg, list):
            if len(self.__errorMsg) == 0:
                return None  # 没有错误时返回None，而不是字符串
            else:
                return self.__errorMsg
        else:
            return [str(self.__errorMsg)] if self.__errorMsg else None
