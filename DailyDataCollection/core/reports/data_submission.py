"""
数据提交报告模块

根据指定的收集周期生成SHP文件和周报告
"""

import os
import stat
import shutil
import zipfile
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Any
from osgeo import ogr, osr

# 导入配置
try:
    from config import WORKSPACE, MAP_PROJECT_FOLDER
except ImportError:
    WORKSPACE = ""
    MAP_PROJECT_FOLDER = ""

# 创建 logger 实例
logger = logging.getLogger('Data Submission')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class DataSubmition:
    """
    数据提交类
    
    根据COLLECTION_WEEKDAYS列表, 在每周的某一天: 
    1. 输出shp文件
    2. 在制图工程文件夹下创建目录, 并拷贝截止当天的shp
    3. 拷贝一周前的shp文件（或kmz文件）
    4. 生成一周新增的shp文件
    5. 调用ArcPy, 生成一周报告
    """
    
    SHP_EXTENSIONS = ['.shp', '.shx', '.dbf', '.prj']

    def __init__(self, date: Any, points_dict: Dict[str, Dict[str, float]]):
        """
        初始化数据提交
        
        Args:
            date: 日期对象
            points_dict: 点要素字典
        """
        self.date = date
        self.pointDict: Dict[str, Dict[str, float]] = points_dict

    def __pointDictValidation(self) -> bool:
        """检查点要素字典的有效性"""
        if not self.pointDict:
            logger.error("点要素字典为空")
            return False
        
        for obspid, coords in self.pointDict.items():
            if not isinstance(coords, dict) or 'longitude' not in coords or 'latitude' not in coords:
                logger.error(f"点要素 {obspid} 格式错误")
                return False
                
        return True

    def weeklyPointToShp(self) -> bool:
        """生成周报告SHP文件"""
        try:
            # 验证点要素字典
            if not self.__pointDictValidation():
                return False
            
            # 在制图工程文件夹下建立新文件夹, 如果已存在则删除清理文件树
            week_report_folder = os.path.join(
                WORKSPACE, 
                MAP_PROJECT_FOLDER, 
                f"Finished_ObsPoints_Until_{self.date.yyyymmdd_str}"
            )
            
            if os.path.exists(week_report_folder):
                shutil.rmtree(week_report_folder)
            os.makedirs(week_report_folder, exist_ok=True)

            # 输出shp文件
            output_shp_file = os.path.join(
                week_report_folder, 
                f"GMAS_points_until_{self.date.yyyymmdd_str}.shp"
            )
            self.pointDictToShp(self.pointDict, output_shp_file)

            # 将shp文件压缩为zip文件
            zip_file = os.path.join(
                WORKSPACE, 
                self.date.yyyymm_str, 
                self.date.yyyymmdd_str, 
                f"GMAS_points_until_{self.date.yyyymmdd_str}.zip"
            )
            
            if os.path.exists(zip_file):
                os.remove(zip_file)
                
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for ext in DataSubmition.SHP_EXTENSIONS:
                    shp_file_with_ext = output_shp_file.replace('.shp', ext)
                    if os.path.exists(shp_file_with_ext):
                        zipf.write(
                            shp_file_with_ext, 
                            os.path.basename(output_shp_file).replace('.shp', ext)
                        )
            
            logger.info(f"截止今日的完成点已生成SHP文件, 并已压缩为ZIP文件: {zip_file}")
            
            # 处理一周前的文件
            return self._process_weekly_comparison(week_report_folder)
            
        except Exception as e:
            logger.error(f"生成周报告SHP文件失败: {e}")
            return False

    def _process_weekly_comparison(self, week_report_folder: str) -> bool:
        """处理一周前文件的比较"""
        try:
            # 延迟导入以避免循环依赖
            from ..data_models.date_types import DateType
            
            # 一周前的日期
            one_week_ago = DateType(date_datetime=(self.date.date_datetime - timedelta(days=7)))
            
            # 定义一周前的文件路径
            one_week_ago_shpfile = os.path.join(
                WORKSPACE, 
                MAP_PROJECT_FOLDER, 
                f"Finished_ObsPoints_Until_{one_week_ago.yyyymmdd_str}", 
                f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.shp"
            )
            one_week_ago_zipfile = os.path.join(
                WORKSPACE, 
                one_week_ago.yyyymm_str, 
                one_week_ago.yyyymmdd_str, 
                f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.zip"
            )

            # 根据文件存在情况处理
            if os.path.exists(one_week_ago_shpfile):
                # 拷贝一周前的shp文件至制图文件夹中
                for ext in DataSubmition.SHP_EXTENSIONS:
                    src_file = one_week_ago_shpfile.replace('.shp', ext)
                    if os.path.exists(src_file):
                        shutil.copy(src_file, week_report_folder)
                os.chmod(week_report_folder, stat.S_IWRITE | stat.S_IREAD)
            elif os.path.exists(one_week_ago_zipfile):
                # 解压一周前的zip文件至制图文件夹中
                with zipfile.ZipFile(one_week_ago_zipfile, 'r') as zip_ref:
                    zip_ref.extractall(week_report_folder)
            else:
                logger.warning(f"一周前的文件不存在: {one_week_ago_zipfile}\\n{one_week_ago_shpfile}")
                return False

            # 读取一周前的点要素
            one_week_ago_shp_path = os.path.join(
                week_report_folder, 
                f"GMAS_points_until_{one_week_ago.yyyymmdd_str}.shp"
            )
            
            if not os.path.exists(one_week_ago_shp_path):
                logger.error(f"无法找到一周前的SHP文件: {one_week_ago_shp_path}")
                return False
                
            one_week_ago_points_dict = self.readShpToPointDict(one_week_ago_shp_path)
            count_one_week_ago_points_dict = len(one_week_ago_points_dict)
            logger.info(f"一周前{one_week_ago.yyyymmdd_str}的点要素总数: {count_one_week_ago_points_dict}")
            
            # 计算本周新增的点要素
            diff_dict = {k: v for k, v in self.pointDict.items() if k not in one_week_ago_points_dict}

            one_week_ago_nextday = DateType(date_datetime=(self.date.date_datetime - timedelta(days=6)))
            logger.info(f"{one_week_ago_nextday.yyyymmdd_str}至{self.date.yyyymmdd_str}, 本周新增点要素: {len(diff_dict)}")

            # 生成本周新增点要素的SHP文件
            weekly_increase_shp_file = os.path.join(
                week_report_folder, 
                f"GMAS_points_{one_week_ago_nextday.yyyymmdd_str}_{self.date.yyyymmdd_str}.shp"
            )
            self.pointDictToShp(diff_dict, weekly_increase_shp_file)

            logger.info(f"GMAS_points_{one_week_ago_nextday.yyyymmdd_str}_{self.date.yyyymmdd_str}.shp创建成功")
            return True
            
        except Exception as e:
            logger.error(f"处理周比较失败: {e}")
            return False

    def pointDictToShp(self, pointDict: Dict[str, Dict[str, float]], output_shp_file: str) -> bool:
        """将点要素字典转换为SHP文件"""
        try:
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
            field_longitude = ogr.FieldDefn('Longitude', ogr.OFTReal)
            shp_layer.CreateField(field_longitude)
            field_latitude = ogr.FieldDefn('Latitude', ogr.OFTReal)
            shp_layer.CreateField(field_latitude)
            
            # 创建要素并添加到图层
            for obspid, coords in pointDict.items():
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
            print(f"点要素已成功生成 SHP 文件: {output_shp_file}")
            return True
            
        except Exception as e:
            logger.error(f"转换SHP文件失败: {e}")
            return False

    def readShpToPointDict(self, shp_file: str) -> Dict[str, Dict[str, float]]:
        """从SHP文件读取点要素字典"""
        points_dict = {}
        
        try:
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
                
                if obspid and longitude is not None and latitude is not None:
                    points_dict[obspid] = {
                        'longitude': longitude,
                        'latitude': latitude
                    }
                    
            # 清理
            shp_ds = None
            
        except Exception as e:
            logger.error(f"读取SHP文件失败: {e}")
            
        return points_dict
