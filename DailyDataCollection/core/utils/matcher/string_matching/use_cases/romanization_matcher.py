# -*- coding: utf-8 -*-
"""
增强版罗马化字母匹配器 - 专门处理罗马化名称的匹配
支持多语言罗马化匹配：中文拼音、日文罗马字、韩文罗马字、阿拉伯文拉丁化、
俄文拉丁化、希腊文拉丁化、泰文罗马化、越南文等
"""

import re
import unicodedata
import math
from typing import List, Optional, Dict, Tuple, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter

try:
    from ..base_matcher import StringMatcher
    from ..fuzzy_matcher import FuzzyStringMatcher
    from ..similarity_calculator import SimilarityCalculator
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_matcher import StringMatcher
    from fuzzy_matcher import FuzzyStringMatcher
    from similarity_calculator import SimilarityCalculator


@dataclass
class RomanizationMapping:
    """罗马化映射数据类"""
    original: str      # 原始文字
    romanized: str     # 罗马化形式
    language: str      # 语言类型
    confidence: float  # 映射置信度
    variants: List[str] = field(default_factory=list)  # 变体形式
    region: str = ""   # 地区方言
    source: str = ""   # 来源系统（如：pinyin, hepburn, wade-giles等）


@dataclass
class PhoneticMapping:
    """音韵映射数据类"""
    sound: str         # 音素
    romanizations: List[str]  # 罗马化表示
    language: str      # 语言
    weight: float = 1.0  # 权重


@dataclass
class SyllableInfo:
    """音节信息"""
    onset: str = ""    # 声母
    nucleus: str = ""  # 韵母主要部分
    coda: str = ""     # 韵尾
    tone: str = ""     # 声调
    full: str = ""     # 完整音节


class EnhancedRomanizationMatcher(StringMatcher):
    """增强版罗马化字母匹配器
    
    支持多语言罗马化匹配，具备以下增强功能：
    1. 音韵级别的匹配分析
    2. 多种罗马化标准支持
    3. 跨语言相似性检测
    4. 自适应学习机制
    5. 上下文相关匹配
    """
    
    def __init__(self, fuzzy_threshold: float = 0.7, debug: bool = False,
                 enable_phonetic_matching: bool = True,
                 enable_cross_language: bool = False,
                 enable_adaptive_learning: bool = True):
        """初始化增强版罗马化匹配器
        
        Args:
            fuzzy_threshold: 模糊匹配阈值
            debug: 是否启用调试模式
            enable_phonetic_matching: 是否启用音韵匹配
            enable_cross_language: 是否启用跨语言匹配
            enable_adaptive_learning: 是否启用自适应学习
        """
        super().__init__(debug)
        self.fuzzy_threshold = fuzzy_threshold
        self.fuzzy_matcher = FuzzyStringMatcher(threshold=fuzzy_threshold, debug=debug)
        
        # 功能开关
        self.enable_phonetic_matching = enable_phonetic_matching
        self.enable_cross_language = enable_cross_language
        self.enable_adaptive_learning = enable_adaptive_learning
        
        # 初始化各种映射和规则
        self.predefined_mappings = self._initialize_mappings()
        self.sound_change_rules = self._initialize_sound_rules()
        self.phonetic_mappings = self._initialize_phonetic_mappings()
        self.syllable_patterns = self._initialize_syllable_patterns()
        
        # 自适应学习相关
        self.learned_mappings: Dict[str, List[RomanizationMapping]] = defaultdict(list)
        self.match_statistics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 语言检测模式
        self.language_weights = {
            'chinese': 1.0,
            'japanese': 1.0,
            'korean': 1.0,
            'arabic': 1.0,
            'russian': 1.0,
            'greek': 1.0,
            'thai': 1.0,
            'vietnamese': 1.0,
            'hindi': 1.0,
            'persian': 1.0
        }
        super().__init__(debug)
        self.fuzzy_threshold = fuzzy_threshold
        self.fuzzy_matcher = FuzzyStringMatcher(threshold=fuzzy_threshold, debug=debug)
        
        # 预定义的罗马化映射
        self.predefined_mappings = self._initialize_mappings()
        
        # 音变规则
        self.sound_change_rules = self._initialize_sound_rules()
    
    def _initialize_mappings(self) -> Dict[str, List[RomanizationMapping]]:
        """初始化预定义的罗马化映射 - 增强版"""
        mappings = {
            'chinese_pinyin': [
                # 中文拼音映射 - 城市
                RomanizationMapping("北京", "Beijing", "chinese", 1.0, ["Peking"], "standard", "pinyin"),
                RomanizationMapping("上海", "Shanghai", "chinese", 1.0, ["Shang Hai"], "standard", "pinyin"),
                RomanizationMapping("广州", "Guangzhou", "chinese", 1.0, ["Canton", "Kwangchow"], "guangdong", "pinyin"),
                RomanizationMapping("深圳", "Shenzhen", "chinese", 1.0, ["Sham Chun"], "guangdong", "pinyin"),
                RomanizationMapping("杭州", "Hangzhou", "chinese", 1.0, ["Hang-chou"], "zhejiang", "pinyin"),
                RomanizationMapping("南京", "Nanjing", "chinese", 1.0, ["Nanking"], "jiangsu", "pinyin"),
                RomanizationMapping("武汉", "Wuhan", "chinese", 1.0, ["Wu-han"], "hubei", "pinyin"),
                RomanizationMapping("成都", "Chengdu", "chinese", 1.0, ["Cheng-tu"], "sichuan", "pinyin"),
                RomanizationMapping("西安", "Xi'an", "chinese", 1.0, ["Xian", "Sian"], "shaanxi", "pinyin"),
                RomanizationMapping("重庆", "Chongqing", "chinese", 1.0, ["Chung-king"], "sichuan", "pinyin"),
                RomanizationMapping("天津", "Tianjin", "chinese", 1.0, ["Tientsin"], "hebei", "pinyin"),
                RomanizationMapping("苏州", "Suzhou", "chinese", 1.0, ["Soochow"], "jiangsu", "pinyin"),
                RomanizationMapping("青岛", "Qingdao", "chinese", 1.0, ["Tsingtao"], "shandong", "pinyin"),
                RomanizationMapping("大连", "Dalian", "chinese", 1.0, ["Dairen", "Talien"], "liaoning", "pinyin"),
                RomanizationMapping("沈阳", "Shenyang", "chinese", 1.0, ["Mukden"], "liaoning", "pinyin"),
                
                # 中文人名 - 扩展
                RomanizationMapping("张伟", "Zhang Wei", "chinese", 1.0, ["Chang Wei"], "standard", "pinyin"),
                RomanizationMapping("王芳", "Wang Fang", "chinese", 1.0, ["Wong Fong"], "standard", "pinyin"),
                RomanizationMapping("李娜", "Li Na", "chinese", 1.0, ["Lee Na"], "standard", "pinyin"),
                RomanizationMapping("刘强", "Liu Qiang", "chinese", 1.0, ["Lau Keung"], "standard", "pinyin"),
                RomanizationMapping("陈敏", "Chen Min", "chinese", 1.0, ["Chan Man"], "standard", "pinyin"),
                RomanizationMapping("杨静", "Yang Jing", "chinese", 1.0, ["Yeung Ching"], "standard", "pinyin"),
                RomanizationMapping("赵磊", "Zhao Lei", "chinese", 1.0, ["Chiu Lui"], "standard", "pinyin"),
                RomanizationMapping("黄丽", "Huang Li", "chinese", 1.0, ["Wong Lai"], "standard", "pinyin"),
                RomanizationMapping("马云", "Ma Yun", "chinese", 1.0, ["Jack Ma"], "standard", "pinyin"),
                RomanizationMapping("李小明", "Li Xiaoming", "chinese", 1.0, ["Lee Siu Ming"], "standard", "pinyin"),
            ],
            
            'japanese_romaji': [
                # 日文罗马字映射 - 城市（Hepburn vs Kunrei）
                RomanizationMapping("東京", "Tokyo", "japanese", 1.0, ["Toukyou", "Tōkyō"], "kanto", "hepburn"),
                RomanizationMapping("大阪", "Osaka", "japanese", 1.0, ["Ōsaka"], "kansai", "hepburn"),
                RomanizationMapping("京都", "Kyoto", "japanese", 1.0, ["Kyōto"], "kansai", "hepburn"),
                RomanizationMapping("名古屋", "Nagoya", "japanese", 1.0, ["Nagoya"], "chubu", "hepburn"),
                RomanizationMapping("横浜", "Yokohama", "japanese", 1.0, ["Yokohama"], "kanto", "hepburn"),
                RomanizationMapping("神戸", "Kobe", "japanese", 1.0, ["Kōbe"], "kansai", "hepburn"),
                RomanizationMapping("福岡", "Fukuoka", "japanese", 1.0, ["Hukuoka"], "kyushu", "hepburn"),
                RomanizationMapping("札幌", "Sapporo", "japanese", 1.0, ["Sapporo"], "hokkaido", "hepburn"),
                RomanizationMapping("仙台", "Sendai", "japanese", 1.0, ["Sendai"], "tohoku", "hepburn"),
                RomanizationMapping("広島", "Hiroshima", "japanese", 1.0, ["Hirosima"], "chugoku", "hepburn"),
                
                # 日文人名
                RomanizationMapping("田中太郎", "Tanaka Taro", "japanese", 1.0, ["Tanaka Tarou"], "standard", "hepburn"),
                RomanizationMapping("佐藤花子", "Sato Hanako", "japanese", 1.0, ["Satou Hanako"], "standard", "hepburn"),
                RomanizationMapping("高橋一郎", "Takahashi Ichiro", "japanese", 1.0, ["Takahasi Itirou"], "standard", "hepburn"),
                RomanizationMapping("山田美咲", "Yamada Misaki", "japanese", 1.0, ["Yamada Misaki"], "standard", "hepburn"),
                RomanizationMapping("渡辺健太", "Watanabe Kenta", "japanese", 1.0, ["Watanabe Kenta"], "standard", "hepburn"),
                RomanizationMapping("鈴木花音", "Suzuki Kanon", "japanese", 1.0, ["Suzuki Kanon"], "standard", "hepburn"),
            ],
            
            'korean_romanization': [
                # 韩文罗马字映射 - 城市（Revised vs McCune-Reischauer）
                RomanizationMapping("서울", "Seoul", "korean", 1.0, ["Sŏul"], "standard", "revised"),
                RomanizationMapping("부산", "Busan", "korean", 1.0, ["Pusan", "Pŭsan"], "gyeongsang", "revised"),
                RomanizationMapping("대구", "Daegu", "korean", 1.0, ["Taegu", "Taegu"], "gyeongsang", "revised"),
                RomanizationMapping("인천", "Incheon", "korean", 1.0, ["Inch'ŏn"], "gyeonggi", "revised"),
                RomanizationMapping("광주", "Gwangju", "korean", 1.0, ["Kwangju", "Kwangju"], "jeolla", "revised"),
                RomanizationMapping("대전", "Daejeon", "korean", 1.0, ["Taejŏn", "Taejon"], "chungcheong", "revised"),
                RomanizationMapping("울산", "Ulsan", "korean", 1.0, ["Ulsan"], "gyeongsang", "revised"),
                RomanizationMapping("수원", "Suwon", "korean", 1.0, ["Suwŏn"], "gyeonggi", "revised"),
                RomanizationMapping("창원", "Changwon", "korean", 1.0, ["Ch'angwŏn"], "gyeongsang", "revised"),
                
                # 韩文人名
                RomanizationMapping("김민수", "Kim Minsu", "korean", 1.0, ["Kim Min-su"], "standard", "revised"),
                RomanizationMapping("이지영", "Lee Jiyoung", "korean", 1.0, ["Yi Chi-yŏng"], "standard", "revised"),
                RomanizationMapping("박준호", "Park Junho", "korean", 1.0, ["Pak Chun-ho"], "standard", "revised"),
                RomanizationMapping("최수진", "Choi Sujin", "korean", 1.0, ["Ch'oe Su-jin"], "standard", "revised"),
                RomanizationMapping("정현우", "Jung Hyeonwoo", "korean", 1.0, ["Chŏng Hyŏn-u"], "standard", "revised"),
            ],
            
            'arabic_latinization': [
                # 阿拉伯文拉丁化映射 - 增强版
                
                # 常见男性名字及其变体
                RomanizationMapping("محمد", "Muhammad", "arabic", 1.0, ["Mohammed", "Mohamed", "Mohammad", "Muhammed"], "standard", "iso233"),
                RomanizationMapping("أحمد", "Ahmad", "arabic", 1.0, ["Ahmed", "Ahmet", "Achmad"], "standard", "iso233"),
                RomanizationMapping("علي", "Ali", "arabic", 1.0, ["Aly", "Aliy"], "standard", "iso233"),
                RomanizationMapping("عبدالله", "Abdullah", "arabic", 1.0, ["Abd Allah", "Abdallah", "Abdulla"], "standard", "iso233"),
                RomanizationMapping("خالد", "Khalid", "arabic", 1.0, ["Khaled", "Halid", "Khaleed"], "standard", "iso233"),
                RomanizationMapping("عمر", "Omar", "arabic", 1.0, ["Umar", "Omer"], "standard", "iso233"),
                RomanizationMapping("حسن", "Hassan", "arabic", 1.0, ["Hasan", "Hasaan"], "standard", "iso233"),
                RomanizationMapping("حسين", "Hussein", "arabic", 1.0, ["Hussain", "Hosein", "Hossein"], "standard", "iso233"),
                RomanizationMapping("يوسف", "Yusuf", "arabic", 1.0, ["Youssef", "Joseph", "Yousef"], "standard", "iso233"),
                RomanizationMapping("إبراهيم", "Ibrahim", "arabic", 1.0, ["Ibraheem", "Abraham"], "standard", "iso233"),
                RomanizationMapping("عبدالرحمن", "Abdurrahman", "arabic", 1.0, ["Abd al-Rahman", "Abdelrahman"], "standard", "iso233"),
                RomanizationMapping("سعد", "Saad", "arabic", 1.0, ["Sa'd", "Saed"], "standard", "iso233"),
                RomanizationMapping("فيصل", "Faisal", "arabic", 1.0, ["Faysal", "Feisal"], "standard", "iso233"),
                RomanizationMapping("طارق", "Tariq", "arabic", 1.0, ["Tarik", "Tareq"], "standard", "iso233"),
                
                # 常见女性名字及其变体
                RomanizationMapping("فاطمة", "Fatima", "arabic", 1.0, ["Fatma", "Fatimah", "Fatemeh"], "standard", "iso233"),
                RomanizationMapping("عائشة", "Aisha", "arabic", 1.0, ["Aysha", "Aishah", "Ayesha"], "standard", "iso233"),
                RomanizationMapping("خديجة", "Khadija", "arabic", 1.0, ["Khadijah", "Hadija"], "standard", "iso233"),
                RomanizationMapping("زينب", "Zainab", "arabic", 1.0, ["Zaynab", "Zeinab"], "standard", "iso233"),
                RomanizationMapping("مريم", "Maryam", "arabic", 1.0, ["Mariam", "Mary"], "standard", "iso233"),
                RomanizationMapping("أمينة", "Amina", "arabic", 1.0, ["Aminah", "Ameena"], "standard", "iso233"),
                RomanizationMapping("سارة", "Sarah", "arabic", 1.0, ["Sara", "Saara"], "standard", "iso233"),
                RomanizationMapping("ليلى", "Layla", "arabic", 1.0, ["Laila", "Leila", "Lila"], "standard", "iso233"),
                RomanizationMapping("نادية", "Nadia", "arabic", 1.0, ["Nadiya", "Nadya"], "standard", "iso233"),
                
                # 阿拉伯国家和城市
                RomanizationMapping("الرياض", "Riyadh", "arabic", 1.0, ["Ar-Riyadh", "Er Riyadh", "Riyad"], "saudi", "iso233"),
                RomanizationMapping("القاهرة", "Cairo", "arabic", 1.0, ["Al-Qahirah", "El Qahira", "Al-Qāhirah"], "egypt", "iso233"),
                RomanizationMapping("دبي", "Dubai", "arabic", 1.0, ["Dubayy", "Dubay"], "uae", "iso233"),
                RomanizationMapping("بغداد", "Baghdad", "arabic", 1.0, ["Baghdād", "Bagdad"], "iraq", "iso233"),
                RomanizationMapping("الدوحة", "Doha", "arabic", 1.0, ["Ad-Dawḥah", "Ad-Doha"], "qatar", "iso233"),
                RomanizationMapping("الكويت", "Kuwait", "arabic", 1.0, ["Al-Kuwayt", "Al-Kuwait"], "kuwait", "iso233"),
                RomanizationMapping("عمان", "Amman", "arabic", 1.0, ["'Ammān"], "jordan", "iso233"),
                RomanizationMapping("مسقط", "Muscat", "arabic", 1.0, ["Masqaţ", "Maskat"], "oman", "iso233"),
                RomanizationMapping("دمشق", "Damascus", "arabic", 1.0, ["Dimashq", "Ash-Sham"], "syria", "iso233"),
                RomanizationMapping("بيروت", "Beirut", "arabic", 1.0, ["Bayrūt", "Beyrouth"], "lebanon", "iso233"),
                RomanizationMapping("الجزائر", "Algiers", "arabic", 1.0, ["Al-Jazā'ir", "Alger"], "algeria", "iso233"),
                RomanizationMapping("الرباط", "Rabat", "arabic", 1.0, ["Ar-Ribāţ"], "morocco", "iso233"),
                RomanizationMapping("تونس", "Tunis", "arabic", 1.0, ["Tūnis"], "tunisia", "iso233"),
                RomanizationMapping("طرابلس", "Tripoli", "arabic", 1.0, ["Ţarābulus"], "libya", "iso233"),
                RomanizationMapping("الخرطوم", "Khartoum", "arabic", 1.0, ["Al-Kharţūm", "Khartum"], "sudan", "iso233"),
                
                # 阿拉伯国家名称
                RomanizationMapping("السعودية", "Saudi Arabia", "arabic", 1.0, ["As-Sa'ūdiyyah", "KSA"], "country", "iso233"),
                RomanizationMapping("مصر", "Egypt", "arabic", 1.0, ["Miṣr", "Masr"], "country", "iso233"),
                RomanizationMapping("الإمارات", "UAE", "arabic", 1.0, ["Al-Imārāt", "Emirates"], "country", "iso233"),
                RomanizationMapping("العراق", "Iraq", "arabic", 1.0, ["Al-'Irāq"], "country", "iso233"),
                RomanizationMapping("الأردن", "Jordan", "arabic", 1.0, ["Al-'Urdun"], "country", "iso233"),
                RomanizationMapping("لبنان", "Lebanon", "arabic", 1.0, ["Lubnān"], "country", "iso233"),
                RomanizationMapping("سوريا", "Syria", "arabic", 1.0, ["Sūriyā", "Suriya"], "country", "iso233"),
                RomanizationMapping("فلسطين", "Palestine", "arabic", 1.0, ["Filasţīn"], "country", "iso233"),
                RomanizationMapping("المغرب", "Morocco", "arabic", 1.0, ["Al-Maghrib"], "country", "iso233"),
                RomanizationMapping("الجزائر", "Algeria", "arabic", 1.0, ["Al-Jazā'ir"], "country", "iso233"),
                RomanizationMapping("ليبيا", "Libya", "arabic", 1.0, ["Lībiyā"], "country", "iso233"),
                RomanizationMapping("السودان", "Sudan", "arabic", 1.0, ["As-Sūdān"], "country", "iso233"),
                
                # 阿拉伯语常用词汇
                RomanizationMapping("بيت", "bayt", "arabic", 1.0, ["bait", "beet"], "word", "iso233"),
                RomanizationMapping("شارع", "shari'", "arabic", 1.0, ["sharia", "street"], "word", "iso233"),
                RomanizationMapping("مدينة", "madina", "arabic", 1.0, ["medina", "city"], "word", "iso233"),
                RomanizationMapping("جامع", "jami'", "arabic", 1.0, ["jamia", "mosque"], "word", "iso233"),
                RomanizationMapping("مطار", "matar", "arabic", 1.0, ["airport"], "word", "iso233"),
            ],
            
            'russian_latinization': [
                # 俄文拉丁化映射
                RomanizationMapping("Москва", "Moscow", "russian", 1.0, ["Moskva", "Moskwa"], "standard", "iso9"),
                RomanizationMapping("Санкт-Петербург", "Saint Petersburg", "russian", 1.0, ["Sankt-Peterburg", "St. Petersburg"], "standard", "iso9"),
                RomanizationMapping("Новосибирск", "Novosibirsk", "russian", 1.0, ["Novosibirsk"], "siberia", "iso9"),
                RomanizationMapping("Екатеринбург", "Yekaterinburg", "russian", 1.0, ["Ekaterinburg"], "ural", "iso9"),
                RomanizationMapping("Нижний Новгород", "Nizhny Novgorod", "russian", 1.0, ["Nizhniy Novgorod"], "volga", "iso9"),
                
                # 俄文人名
                RomanizationMapping("Владимир", "Vladimir", "russian", 1.0, ["Wladimir"], "standard", "iso9"),
                RomanizationMapping("Александр", "Alexander", "russian", 1.0, ["Aleksandr"], "standard", "iso9"),
                RomanizationMapping("Наталья", "Natalia", "russian", 1.0, ["Natalya", "Natasha"], "standard", "iso9"),
                RomanizationMapping("Дмитрий", "Dmitry", "russian", 1.0, ["Dmitri", "Dimitri"], "standard", "iso9"),
            ],
            
            'greek_latinization': [
                # 希腊文拉丁化映射
                RomanizationMapping("Αθήνα", "Athens", "greek", 1.0, ["Athina"], "standard", "iso843"),
                RomanizationMapping("Θεσσαλονίκη", "Thessaloniki", "greek", 1.0, ["Saloniki"], "macedonia", "iso843"),
                RomanizationMapping("Πάτρα", "Patras", "greek", 1.0, ["Patra"], "peloponnese", "iso843"),
                RomanizationMapping("Ηράκλειο", "Heraklion", "greek", 1.0, ["Iraklion"], "crete", "iso843"),
                
                # 希腊人名
                RomanizationMapping("Γιάννης", "Yannis", "greek", 1.0, ["Giannis", "Ioannis"], "standard", "iso843"),
                RomanizationMapping("Μαρία", "Maria", "greek", 1.0, ["Mary"], "standard", "iso843"),
                RomanizationMapping("Νίκος", "Nikos", "greek", 1.0, ["Nicko"], "standard", "iso843"),
            ],
            
            'thai_romanization': [
                # 泰文罗马化映射
                RomanizationMapping("กรุงเทพมหานคร", "Bangkok", "thai", 1.0, ["Krung Thep"], "central", "rtgs"),
                RomanizationMapping("เชียงใหม่", "Chiang Mai", "thai", 1.0, ["Chiangmai"], "northern", "rtgs"),
                RomanizationMapping("ภูเก็ต", "Phuket", "thai", 1.0, ["Puket"], "southern", "rtgs"),
                RomanizationMapping("พัทยา", "Pattaya", "thai", 1.0, ["Phatthaya"], "central", "rtgs"),
                
                # 泰文人名
                RomanizationMapping("สมชาย", "Somchai", "thai", 1.0, ["Som Chai"], "standard", "rtgs"),
                RomanizationMapping("นิตยา", "Nitaya", "thai", 1.0, ["Nittaya"], "standard", "rtgs"),
            ],
            
            'vietnamese_romanization': [
                # 越南文罗马化映射（已经是罗马字母，但有声调）
                RomanizationMapping("Hà Nội", "Hanoi", "vietnamese", 1.0, ["Ha Noi"], "northern", "standard"),
                RomanizationMapping("Thành phố Hồ Chí Minh", "Ho Chi Minh City", "vietnamese", 1.0, ["Saigon", "HCMC"], "southern", "standard"),
                RomanizationMapping("Đà Nẵng", "Da Nang", "vietnamese", 1.0, ["Danang"], "central", "standard"),
                RomanizationMapping("Hải Phòng", "Hai Phong", "vietnamese", 1.0, ["Haiphong"], "northern", "standard"),
                
                # 越南人名
                RomanizationMapping("Nguyễn Văn A", "Nguyen Van A", "vietnamese", 1.0, ["Nguyen Van A"], "standard", "standard"),
                RomanizationMapping("Trần Thị B", "Tran Thi B", "vietnamese", 1.0, ["Tran Thi B"], "standard", "standard"),
            ]
        }
        
        return mappings
    
    def _initialize_phonetic_mappings(self) -> Dict[str, List[PhoneticMapping]]:
        """初始化音韵映射"""
        return {
            'consonants': [
                # 辅音映射
                PhoneticMapping("p", ["p", "b", "ph", "f"], "universal", 1.0),
                PhoneticMapping("t", ["t", "d", "th", "dt"], "universal", 1.0),
                PhoneticMapping("k", ["k", "g", "kh", "gh", "c", "q"], "universal", 1.0),
                PhoneticMapping("s", ["s", "z", "sh", "zh", "c", "ts"], "universal", 1.0),
                PhoneticMapping("n", ["n", "ng", "m", "ny"], "universal", 1.0),
                PhoneticMapping("r", ["r", "l", "rr", "rl"], "universal", 0.9),
                PhoneticMapping("h", ["h", "kh", "gh", "x"], "universal", 0.8),
                
                # 中文特有
                PhoneticMapping("zh", ["zh", "z", "j"], "chinese", 1.0),
                PhoneticMapping("ch", ["ch", "c", "q"], "chinese", 1.0),
                PhoneticMapping("sh", ["sh", "s", "x"], "chinese", 1.0),
                
                # 日文特有
                PhoneticMapping("tsu", ["tsu", "tu", "zu"], "japanese", 1.0),
                PhoneticMapping("chi", ["chi", "ti", "ki"], "japanese", 1.0),
                PhoneticMapping("shi", ["shi", "si", "hi"], "japanese", 1.0),
                
                # 阿拉伯文特有
                PhoneticMapping("'", ["'", "", "a"], "arabic", 0.8),
                PhoneticMapping("kh", ["kh", "h", "x"], "arabic", 1.0),
                PhoneticMapping("gh", ["gh", "g", "r"], "arabic", 1.0),
            ],
            
            'vowels': [
                # 元音映射
                PhoneticMapping("a", ["a", "ā", "à", "á", "â", "ă"], "universal", 1.0),
                PhoneticMapping("e", ["e", "ē", "è", "é", "ê", "ë"], "universal", 1.0),
                PhoneticMapping("i", ["i", "ī", "ì", "í", "î", "ï", "y"], "universal", 1.0),
                PhoneticMapping("o", ["o", "ō", "ò", "ó", "ô", "ö"], "universal", 1.0),
                PhoneticMapping("u", ["u", "ū", "ù", "ú", "û", "ü"], "universal", 1.0),
                
                # 复合元音
                PhoneticMapping("ai", ["ai", "ay", "ae", "ei"], "universal", 0.9),
                PhoneticMapping("au", ["au", "aw", "ao"], "universal", 0.9),
                PhoneticMapping("ou", ["ou", "ow", "oo"], "universal", 0.9),
                
                # 中文特有
                PhoneticMapping("ü", ["ü", "u", "yu"], "chinese", 1.0),
                PhoneticMapping("er", ["er", "r"], "chinese", 1.0),
                
                # 韩文特有
                PhoneticMapping("eo", ["eo", "o", "u"], "korean", 1.0),
                PhoneticMapping("eu", ["eu", "u", "oo"], "korean", 1.0),
            ]
        }
    
    def _initialize_syllable_patterns(self) -> Dict[str, List[str]]:
        """初始化音节模式"""
        return {
            'chinese': [
                # 中文音节结构：(声母)+(韵母)+(声调)
                r"^([bpmfvdtnlgkhjqxzhchshrzcszyw]?)([aeiouüvyw]+[ngrw]?)([1-4]?)$",
                r"^([bpmfvdtnlgkhjqxzhchshrzcszyw]?)([aeiouüvyw]+)([1-4]?)$",
            ],
            'japanese': [
                # 日文音节结构：(辅音)+元音 or 单独的n
                r"^([kgsztdnhbpmyrwfvj]?[yh]?)([aiueo])$",
                r"^n$",
                r"^([kgsztdnhbpmyrw]+[yh]?)([aiueo]+)$",
            ],
            'korean': [
                # 韩文音节结构：(声母)+(中声)+(终声?)
                r"^([bcdfghjklmnpqrstvwxyz]?)([aeiouyw]+)([ngtklmp]?)$",
            ],
            'arabic': [
                # 阿拉伯文音节结构：(辅音)+元音+(辅音?)
                r"^([bcdfghjklmnpqrstvwxyz']+)([aeiou]+)([bcdfghjklmnpqrstvwxyz']*)$",
            ]
        }
    
    def _initialize_sound_rules(self) -> Dict[str, List[Tuple[str, str]]]:
        """初始化音变规则 - 增强版"""
        return {
            'chinese': [
                # 中文拼音音变规则 - 扩展
                ("zh", "z"), ("ch", "c"), ("sh", "s"),  # 基础混淆
                ("x", "sh"), ("q", "ch"), ("j", "zh"),  # 音素混淆
                ("'", ""), ("-", ""), ("_", ""),        # 分隔符处理
                ("ü", "u"), ("ö", "o"), ("ā", "a"),     # 元音简化
                ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u"),  # 长音简化
                ("ou", "o"), ("ao", "au"), ("ei", "ai"), # 复合元音
                ("ng", "n"), ("nk", "ng"),               # 鼻音变化
                ("ian", "ien"), ("uan", "uen"),          # 韵母变体
                ("iang", "ieng"), ("uang", "ueng"),      # 复合韵母
                ("zi", "tzu"), ("ci", "tzu"), ("si", "szu"), # Wade-Giles变体
                ("zhi", "chih"), ("chi", "ch'ih"), ("shi", "shih"), # Wade-Giles变体
            ],
            
            'japanese': [
                # 日文罗马字音变规则 - 扩展
                ("ou", "o"), ("oo", "o"), ("uu", "u"),   # 长音省略
                ("ei", "e"), ("ii", "i"), ("aa", "a"),   # 长音省略
                ("nn", "n"), ("mm", "m"),                # 促音简化
                ("tsu", "tu"), ("chi", "ti"), ("shi", "si"), ("fu", "hu"),  # 不同系统
                ("ja", "dya"), ("ju", "dyu"), ("jo", "dyo"),  # 拗音变体
                ("sha", "sya"), ("shu", "syu"), ("sho", "syo"), # 拗音变体
                ("cha", "tya"), ("chu", "tyu"), ("cho", "tyo"), # 拗音变体
                ("kya", "kia"), ("kyu", "kiu"), ("kyo", "kio"), # 音变
                ("gya", "gia"), ("gyu", "giu"), ("gyo", "gio"), # 音变
                ("wo", "o"), ("we", "e"), ("wi", "i"),   # 古音简化
                ("du", "zu"), ("di", "zi"),              # 浊音变化
            ],
            
            'korean': [
                # 韩文罗马字音变规则 - 扩展
                ("eo", "o"), ("eu", "u"), ("ae", "e"),   # 元音简化
                ("oe", "we"), ("wi", "ui"), ("eui", "ui"), # 复合元音
                ("kw", "qu"), ("gw", "gu"), ("hw", "fu"), # 辅音组合
                ("ng", "n"), ("nk", "ng"), ("nt", "nd"),  # 词尾变化
                ("pp", "p"), ("tt", "t"), ("kk", "k"),   # 紧音简化
                ("ss", "s"), ("jj", "j"), ("cc", "ch"),  # 紧音简化
                ("rr", "r"), ("ll", "l"),                # 流音变化
                ("ya", "ia"), ("yo", "io"), ("yu", "iu"), # 半元音
                ("wa", "ua"), ("wo", "uo"), ("we", "ue"), # 半元音
                ("b", "p"), ("d", "t"), ("g", "k"),      # 无声化
                ("p'", "ph"), ("t'", "th"), ("k'", "kh"), # 送气音
            ],
            
            'arabic': [
                # 阿拉伯文音变规则 - 增强版
                
                # 声门塞音和重音符号省略
                ("'", ""), ("'", ""), ("`", ""), ("ʾ", ""), ("ʿ", ""),  # 声门塞音省略
                ("ʼ", ""), ("´", ""), ("̀", ""), ("̂", ""), ("̃", ""),   # 重音符号省略
                
                # 阿拉伯语特殊辅音的地区性变化
                ("kh", "h"), ("kh", "x"), ("x", "kh"),   # خ 的不同表示
                ("gh", "g"), ("gh", "r"),                # غ 的方言差异
                ("q", "k"), ("q", "g"), ("q", ""),       # ق 的地区差异（埃及方言常省略）
                ("j", "g"), ("j", "y"), ("j", "dj"),     # ج 的方言差异
                
                # 摩擦音和塞音的简化
                ("th", "t"), ("th", "s"), ("ث", "s"),    # ث 的变化（埃及方言）
                ("dh", "d"), ("dh", "z"), ("ذ", "z"),    # ذ 的变化
                ("zh", "z"), ("ظ", "z"),                 # ظ 通常变为 z
                ("sh", "s"),                             # ش 的简化
                
                # 咽头化音的简化
                ("D", "d"), ("ض", "d"),                  # ض -> d
                ("S", "s"), ("ص", "s"),                  # ص -> s  
                ("T", "t"), ("ط", "t"),                  # ط -> t
                ("Z", "z"), ("ظ", "z"),                  # ظ -> z
                ("H", "h"), ("ح", "h"),                  # ح -> h
                
                # 长音简化
                ("aa", "a"), ("ā", "a"), ("â", "a"),     # 长 a
                ("ii", "i"), ("ī", "i"), ("î", "i"),     # 长 i
                ("uu", "u"), ("ū", "u"), ("û", "u"),     # 长 u
                ("oo", "o"), ("ō", "o"), ("ô", "o"),     # 长 o
                ("ee", "e"), ("ē", "e"), ("ê", "e"),     # 长 e
                
                # 双元音变化
                ("ay", "ai"), ("ey", "ei"), ("oy", "oi"), # y结尾双元音
                ("aw", "au"), ("ew", "eu"), ("ow", "ou"), # w结尾双元音
                ("ai", "ay"), ("au", "aw"),               # 双元音互换
                
                # 半元音处理
                ("y", "i"), ("w", "u"), ("w", "o"),       # 半元音变元音
                ("ya", "ia"), ("yu", "iu"), ("yo", "io"), # y + 元音
                ("wa", "ua"), ("wu", "uu"), ("wo", "uo"), # w + 元音
                
                # 阿拉伯语定冠词 al- 的变化
                ("al-", ""), ("al", ""), ("el-", ""),     # 定冠词省略
                ("ar-", ""), ("as-", ""), ("at-", ""),    # 太阳字母同化后的省略
                ("an-", ""), ("ad-", ""), ("az-", ""),
                ("ash-", ""), ("as-", ""), ("ar-", ""),
                
                # 词尾变化
                ("ah", "a"), ("eh", "e"), ("ih", "i"),    # h 词尾的省略
                ("at", "a"), ("et", "e"), ("it", "i"),    # t 词尾的变化
                ("un", ""), ("an", ""), ("in", ""),       # 格变词尾省略
                
                # 重复辅音简化
                ("bb", "b"), ("dd", "d"), ("ff", "f"),    # 重复辅音
                ("gg", "g"), ("hh", "h"), ("jj", "j"),
                ("kk", "k"), ("ll", "l"), ("mm", "m"),
                ("nn", "n"), ("pp", "p"), ("qq", "q"),
                ("rr", "r"), ("ss", "s"), ("tt", "t"),
                ("vv", "v"), ("ww", "w"), ("xx", "x"),
                ("yy", "y"), ("zz", "z"),
                
                # 特殊符号和数字替代（Chat speak）
                ("9", "'"), ("3", "'"), ("7", "h"),       # 数字替代字母
                ("6", "t"), ("2", "'"), ("5", "kh"),      # 阿拉伯聊天用数字
                ("8", "gh"), ("4", "th"),                 # 更多数字替代
                
                # 不同拉丁化系统的兼容
                ("ḥ", "h"), ("ḫ", "kh"), ("ḍ", "d"),      # 带符号的字母
                ("ṣ", "s"), ("ṭ", "t"), ("ẓ", "z"),       # 咽头化音符号
                ("ḏ", "th"), ("ḏ", "dh"), ("ṯ", "th"),     # 摩擦音符号
                ("ġ", "gh"), ("š", "sh"), ("ğ", "g"),      # 其他特殊符号
                
                # 方言特色变化
                # 埃及方言
                ("gi", "g"), ("gy", "g"),                 # ج -> g 在埃及
                # 黎凡特方言  
                ("'a", "a"), ("'i", "i"), ("'u", "u"),    # 声门塞音弱化
                # 海湾方言
                ("ch", "k"), ("tch", "k"),               # 某些 ك 的变化
                # 马格里布方言
                ("v", "b"), ("p", "b"),                  # 借词中的音变
            ],
            
            'russian': [
                # 俄文拉丁化音变规则
                ("ya", "ia"), ("ye", "ie"), ("yo", "io"), ("yu", "iu"), # 软音
                ("zh", "z"), ("ch", "c"), ("sh", "s"),   # 颤音简化
                ("shch", "sh"), ("tsch", "ch"),          # 复合音简化
                ("iy", "y"), ("yy", "y"), ("ii", "i"),   # 元音简化
                ("'", ""), ("\"", ""), ("`", ""),        # 软硬符号省略
                ("kh", "h"), ("ts", "c"), ("ks", "x"),   # 音素组合
                ("ë", "e"), ("ï", "i"), ("ÿ", "y"),      # 变音符号
            ],
            
            'greek': [
                # 希腊文拉丁化音变规则
                ("th", "t"), ("ph", "f"), ("ch", "h"),   # 送气音简化
                ("ps", "s"), ("ks", "x"), ("ng", "n"),   # 复合音简化
                ("ai", "e"), ("ei", "i"), ("oi", "i"),   # 双元音简化
                ("au", "af"), ("eu", "ef"), ("ou", "u"), # 双元音变化
                ("y", "i"), ("ē", "e"), ("ō", "o"),      # 元音标准化
                ("rh", "r"), ("rrh", "r"),               # 流音简化
                ("mp", "b"), ("nt", "d"), ("gk", "g"),   # 鼻音同化
            ],
            
            'thai': [
                # 泰文罗马化音变规则
                ("ph", "p"), ("th", "t"), ("kh", "k"),   # 送气音简化
                ("ch", "c"), ("ng", "n"), ("ny", "n"),   # 音素简化
                ("ai", "ay"), ("ao", "aw"), ("oe", "e"), # 元音变体
                ("ue", "u"), ("ia", "ya"), ("ua", "wa"), # 元音变体
                ("r", "l"), ("l", "r"),                  # 流音混淆
            ],
            
            'vietnamese': [
                # 越南文音变规则（主要是声调省略）
                ("ă", "a"), ("â", "a"), ("ê", "e"), ("ô", "o"), ("ơ", "o"), ("ư", "u"), # 元音简化
                ("đ", "d"),                              # 特殊字母
                ("gi", "z"), ("gh", "g"), ("ng", "n"),   # 特殊组合
                ("ph", "f"), ("th", "t"), ("tr", "ch"),  # 音素组合
                ("qu", "kw"), ("ngh", "ng"),             # 复合音
            ],
            
            # 跨语言通用规则
            'universal': [
                ("ck", "k"), ("ph", "f"), ("gh", "g"),   # 通用简化
                ("sch", "sh"), ("tch", "ch"),            # 欧洲语言通用
                ("x", "ks"), ("qu", "kw"),               # 拉丁系通用
                ("double_consonant", "single"),          # 双辅音简化（需特殊处理）
            ]
        }
    
    def match_string(self, target: str, candidates: List[str]) -> Optional[str]:
        """增强版罗马化字符串匹配
        
        Args:
            target: 目标字符串（可能是罗马化或原文）
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        matched, _ = self.match_string_with_score(target, candidates)
        return matched
    
    def match_string_with_score(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """增强版罗马化字符串匹配并返回分数
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 相似度分数)
        """
        if not target or not candidates:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        match_details = []
        
        # 1. 精确匹配
        if target in candidates:
            self._log_debug(f"[增强罗马化] 精确匹配: '{target}'")
            return target, 1.0
        
        # 2. 预定义映射匹配（包括变体）
        for candidate in candidates:
            score = self._check_enhanced_predefined_mapping(target, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
                match_details.append(f"预定义映射: {score:.3f}")
        
        # 3. 音韵级别匹配（如果启用）
        if self.enable_phonetic_matching and best_score < 0.85:
            for candidate in candidates:
                score = self._check_phonetic_matching(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"音韵匹配: {score:.3f}")
        
        # 3.5. 阿拉伯语专门增强匹配
        if best_score < 0.85:
            for candidate in candidates:
                score = self._enhance_arabic_romanization_matching(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"阿拉伯语增强: {score:.3f}")
        
        # 4. 音节结构匹配
        if best_score < 0.8:
            for candidate in candidates:
                score = self._check_syllable_structure_match(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"音节结构: {score:.3f}")
        
        # 5. 增强音变规则匹配
        if best_score < 0.75:
            for candidate in candidates:
                score = self._check_enhanced_sound_change_match(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"增强音变: {score:.3f}")
        
        # 6. 跨语言相似性检测（如果启用）
        if self.enable_cross_language and best_score < 0.7:
            for candidate in candidates:
                score = self._check_cross_language_similarity(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"跨语言: {score:.3f}")
        
        # 7. 字符级编辑距离匹配
        if best_score < 0.65:
            for candidate in candidates:
                score = self._check_character_level_similarity(target, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    match_details.append(f"字符级: {score:.3f}")
        
        # 8. 回退到传统模糊匹配
        if best_score < self.fuzzy_threshold:
            fuzzy_match, fuzzy_score = self.fuzzy_matcher.match_string_with_score(target, candidates)
            if fuzzy_score > best_score:
                best_score = fuzzy_score
                best_match = fuzzy_match
                match_details.append(f"模糊匹配: {fuzzy_score:.3f}")
        
        # 自适应学习（如果启用）
        if self.enable_adaptive_learning and best_match and best_score >= self.fuzzy_threshold:
            self._learn_from_match(target, best_match, best_score)
        
        if best_match and best_score >= self.fuzzy_threshold:
            self._log_debug(f"[增强罗马化] 匹配成功: '{target}' -> '{best_match}' (分数: {best_score:.3f}, 方法: {', '.join(match_details[-1:])})")
            return best_match, best_score
        else:
            self._log_debug(f"[增强罗马化] 匹配失败: '{target}' (最高分数: {best_score:.3f})")
            return None, best_score
    
    def _check_enhanced_predefined_mapping(self, target: str, candidate: str) -> float:
        """检查增强预定义映射（包括变体） - 改进版"""
        target_lower = target.lower()
        candidate_lower = candidate.lower()
        
        # 同时检查标准化版本
        target_norm = self._normalize_for_comparison(target)
        candidate_norm = self._normalize_for_comparison(candidate)
        
        best_score = 0.0
        
        # 检查所有预定义映射
        for language, mappings in self.predefined_mappings.items():
            language_weight = self.language_weights.get(language.split('_')[0], 1.0)
            
            for mapping in mappings:
                current_score = 0.0
                
                # 标准化映射数据
                mapping_original_norm = self._normalize_for_comparison(mapping.original)
                mapping_romanized_norm = self._normalize_for_comparison(mapping.romanized)
                
                # 正向匹配：原文 -> 罗马化 (同时检查原始和标准化版本)
                if ((mapping.original.lower() == candidate_lower and mapping.romanized.lower() == target_lower) or
                    (mapping_original_norm == candidate_norm and mapping_romanized_norm == target_norm)):
                    current_score = mapping.confidence * language_weight
                
                # 反向匹配：罗马化 -> 原文 (同时检查原始和标准化版本)
                elif ((mapping.romanized.lower() == candidate_lower and mapping.original.lower() == target_lower) or
                      (mapping_romanized_norm == candidate_norm and mapping_original_norm == target_norm)):
                    current_score = mapping.confidence * language_weight
                
                # 变体匹配（包括标准化检查）
                elif mapping.variants:
                    for variant in mapping.variants:
                        variant_lower = variant.lower()
                        variant_norm = self._normalize_for_comparison(variant)
                        
                        # 变体 -> 原文
                        if ((variant_lower == target_lower and mapping.original.lower() == candidate_lower) or
                            (variant_norm == target_norm and mapping_original_norm == candidate_norm)):
                            current_score = max(current_score, mapping.confidence * 0.95 * language_weight)
                        
                        # 原文 -> 变体
                        elif ((mapping.original.lower() == target_lower and variant_lower == candidate_lower) or
                              (mapping_original_norm == target_norm and variant_norm == candidate_norm)):
                            current_score = max(current_score, mapping.confidence * 0.95 * language_weight)
                        
                        # 变体间匹配
                        elif ((variant_lower == target_lower and mapping.romanized.lower() == candidate_lower) or
                              (variant_norm == target_norm and mapping_romanized_norm == candidate_norm)):
                            current_score = max(current_score, mapping.confidence * 0.9 * language_weight)
                        elif ((mapping.romanized.lower() == target_lower and variant_lower == candidate_lower) or
                              (mapping_romanized_norm == target_norm and variant_norm == candidate_norm)):
                            current_score = max(current_score, mapping.confidence * 0.9 * language_weight)
                
                best_score = max(best_score, current_score)
        
        return best_score
    
    def _check_phonetic_matching(self, target: str, candidate: str) -> float:
        """检查音韵级别匹配
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        if not self.enable_phonetic_matching:
            return 0.0
        
        target_phonemes = self._extract_phonemes(target.lower())
        candidate_phonemes = self._extract_phonemes(candidate.lower())
        
        if not target_phonemes or not candidate_phonemes:
            return 0.0
        
        # 计算音韵相似度
        phonetic_score = self._calculate_phonetic_similarity(target_phonemes, candidate_phonemes)
        return phonetic_score
    
    def _check_syllable_structure_match(self, target: str, candidate: str) -> float:
        """检查音节结构匹配
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        target_syllables = self._extract_syllables(target.lower())
        candidate_syllables = self._extract_syllables(candidate.lower())
        
        if not target_syllables or not candidate_syllables:
            return 0.0
        
        # 比较音节数量
        length_diff = abs(len(target_syllables) - len(candidate_syllables))
        if length_diff > 2:  # 音节数差异过大
            return 0.0
        
        # 计算音节相似度
        syllable_score = self._calculate_syllable_similarity(target_syllables, candidate_syllables)
        
        # 长度惩罚
        length_penalty = 1.0 - (length_diff * 0.1)
        
        return syllable_score * length_penalty
    
    def _check_enhanced_sound_change_match(self, target: str, candidate: str) -> float:
        """检查增强音变规则匹配
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        max_score = 0.0
        
        # 检测可能的语言类型
        detected_languages = self._detect_language_context(target, candidate)
        
        # 对每种可能的语言应用音变规则
        for language in detected_languages:
            if language in self.sound_change_rules:
                rules = self.sound_change_rules[language]
                score = self._apply_sound_rules_with_score(target.lower(), candidate.lower(), rules)
                max_score = max(max_score, score * detected_languages[language])
        
        # 应用通用规则
        if 'universal' in self.sound_change_rules:
            universal_rules = self.sound_change_rules['universal']
            score = self._apply_sound_rules_with_score(target.lower(), candidate.lower(), universal_rules)
            max_score = max(max_score, score * 0.8)  # 通用规则权重稍低
        
        return max_score
    
    def _check_cross_language_similarity(self, target: str, candidate: str) -> float:
        """检查跨语言相似性
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        if not self.enable_cross_language:
            return 0.0
        
        # 检测字符类型
        target_script = self._detect_script_type(target)
        candidate_script = self._detect_script_type(candidate)
        
        # 如果都是同一种文字类型，不需要跨语言匹配
        if target_script == candidate_script:
            return 0.0
        
        # 计算跨语言音韵相似度
        cross_lang_score = self._calculate_cross_language_phonetic_similarity(target, candidate)
        
        return cross_lang_score
    
    def _check_character_level_similarity(self, target: str, candidate: str) -> float:
        """检查字符级相似性
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        # 标准化处理
        target_norm = self._normalize_for_comparison(target)
        candidate_norm = self._normalize_for_comparison(candidate)
        
        # 计算编辑距离
        edit_distance = self._calculate_edit_distance(target_norm, candidate_norm)
        max_length = max(len(target_norm), len(candidate_norm))
        
        if max_length == 0:
            return 1.0 if target_norm == candidate_norm else 0.0
        
        # 转换为相似度分数
        similarity = 1.0 - (edit_distance / max_length)
        
        # 对于短字符串，提高要求
        if max_length <= 3:
            similarity = similarity ** 2
        
        return max(0.0, similarity)
    
    def _learn_from_match(self, target: str, matched: str, score: float):
        """从匹配结果中学习
        
        Args:
            target: 目标字符串
            matched: 匹配到的字符串
            score: 匹配分数
        """
        if not self.enable_adaptive_learning:
            return
        
        # 更新匹配统计
        self.match_statistics[target][matched] += 1
        
        # 如果匹配次数达到阈值，添加到学习映射中
        if self.match_statistics[target][matched] >= 3 and score >= 0.8:
            # 检测语言类型
            detected_lang = self._detect_language_simple(target, matched)
            
            # 创建学习到的映射
            learned_mapping = RomanizationMapping(
                original=target if self._is_original_script(target) else matched,
                romanized=matched if self._is_original_script(target) else target,
                language=detected_lang,
                confidence=min(0.95, score),
                variants=[],
                region="learned",
                source="adaptive"
            )
            
            self.learned_mappings[detected_lang].append(learned_mapping)
            self._log_debug(f"[自适应学习] 新增映射: {learned_mapping.original} <-> {learned_mapping.romanized}")

    def _check_predefined_mapping(self, target: str, candidate: str) -> float:
        """检查预定义映射
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        target_lower = target.lower()
        candidate_lower = candidate.lower()
        
        # 检查所有预定义映射
        for language, mappings in self.predefined_mappings.items():
            for mapping in mappings:
                # 正向匹配：原文 -> 罗马化
                if (mapping.original.lower() == candidate_lower and 
                    mapping.romanized.lower() == target_lower):
                    return mapping.confidence
                
                # 反向匹配：罗马化 -> 原文
                if (mapping.romanized.lower() == candidate_lower and 
                    mapping.original.lower() == target_lower):
                    return mapping.confidence
        
        return 0.0
    
    def _check_sound_change_match(self, target: str, candidate: str) -> float:
        """检查音变规则匹配
        
        Args:
            target: 目标字符串
            candidate: 候选字符串
            
        Returns:
            float: 匹配分数
        """
        max_score = 0.0
        
        # 尝试对目标字符串应用音变规则
        for language, rules in self.sound_change_rules.items():
            # 正向音变
            modified_target = self._apply_sound_rules(target.lower(), rules)
            if modified_target == candidate.lower():
                max_score = max(max_score, 0.85)
            
            # 反向音变
            modified_candidate = self._apply_sound_rules(candidate.lower(), rules)
            if modified_candidate == target.lower():
                max_score = max(max_score, 0.85)
            
            # 双向音变
            if modified_target == modified_candidate:
                max_score = max(max_score, 0.8)
        
        return max_score
    
    def _apply_sound_rules(self, text: str, rules: List[Tuple[str, str]]) -> str:
        """应用音变规则
        
        Args:
            text: 原始文本
            rules: 音变规则列表
            
        Returns:
            str: 应用音变规则后的文本
        """
        result = text
        for old, new in rules:
            result = result.replace(old, new)
        return result
    
    def add_custom_mapping(self, original: str, romanized: str, language: str, confidence: float = 1.0):
        """添加自定义映射
        
        Args:
            original: 原始文字
            romanized: 罗马化形式
            language: 语言类型
            confidence: 置信度
        """
        if language not in self.predefined_mappings:
            self.predefined_mappings[language] = []
        
        mapping = RomanizationMapping(original, romanized, language, confidence)
        self.predefined_mappings[language].append(mapping)
        self._log_debug(f"添加自定义映射: {original} <-> {romanized} ({language}, {confidence})")
    
    def add_sound_rule(self, language: str, old_pattern: str, new_pattern: str):
        """添加音变规则
        
        Args:
            language: 语言类型
            old_pattern: 原模式
            new_pattern: 新模式
        """
        if language not in self.sound_change_rules:
            self.sound_change_rules[language] = []
        
        self.sound_change_rules[language].append((old_pattern, new_pattern))
        self._log_debug(f"添加音变规则: {old_pattern} -> {new_pattern} ({language})")
    
    def get_romanization_suggestions(self, text: str) -> List[RomanizationMapping]:
        """获取罗马化建议
        
        Args:
            text: 输入文本
            
        Returns:
            List[RomanizationMapping]: 罗马化建议列表
        """
        suggestions = []
        text_lower = text.lower()
        
        for language, mappings in self.predefined_mappings.items():
            for mapping in mappings:
                if (mapping.original.lower() == text_lower or 
                    mapping.romanized.lower() == text_lower):
                    suggestions.append(mapping)
        
        # 按置信度排序
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions
    
    def normalize_romanization(self, text: str, target_language: str = None) -> str:
        """标准化罗马化文本
        
        Args:
            text: 输入文本
            target_language: 目标语言类型
            
        Returns:
            str: 标准化后的文本
        """
        normalized = text.lower().strip()
        
        # 移除多余的空格和标点
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s\'-]', '', normalized)
        
        # 如果指定了目标语言，应用相应的标准化规则
        if target_language in self.sound_change_rules:
            rules = self.sound_change_rules[target_language]
            normalized = self._apply_sound_rules(normalized, rules)
        
        return normalized


    # =========================
    # 增强匹配器辅助方法
    # =========================
    
    def _extract_phonemes(self, text: str) -> List[str]:
        """提取音素"""
        phonemes = []
        i = 0
        while i < len(text):
            # 检查双字符音素
            if i < len(text) - 1:
                double_char = text[i:i+2]
                if self._is_known_phoneme(double_char):
                    phonemes.append(double_char)
                    i += 2
                    continue
            
            # 单字符音素
            single_char = text[i]
            if single_char.isalpha():
                phonemes.append(single_char)
            i += 1
        
        return phonemes
    
    def _is_known_phoneme(self, sound: str) -> bool:
        """检查是否是已知音素"""
        known_phonemes = {
            'zh', 'ch', 'sh', 'th', 'ph', 'kh', 'gh', 'ng', 'ny', 'ts', 'dz',
            'tsu', 'chi', 'shi', 'ou', 'ai', 'ei', 'ao', 'au', 'ia', 'ua'
        }
        return sound.lower() in known_phonemes
    
    def _calculate_phonetic_similarity(self, phonemes1: List[str], phonemes2: List[str]) -> float:
        """计算音韵相似度"""
        if not phonemes1 or not phonemes2:
            return 0.0
        
        # 使用动态规划计算最优对齐
        dp = [[0.0] * (len(phonemes2) + 1) for _ in range(len(phonemes1) + 1)]
        
        for i in range(1, len(phonemes1) + 1):
            for j in range(1, len(phonemes2) + 1):
                # 计算音素相似度
                phoneme_sim = self._calculate_single_phoneme_similarity(phonemes1[i-1], phonemes2[j-1])
                
                # 三种操作：匹配、插入、删除
                match_score = dp[i-1][j-1] + phoneme_sim
                insert_score = dp[i][j-1] + 0.1  # 插入惩罚
                delete_score = dp[i-1][j] + 0.1  # 删除惩罚
                
                dp[i][j] = max(match_score, insert_score, delete_score)
        
        # 标准化分数
        max_possible = max(len(phonemes1), len(phonemes2))
        return dp[len(phonemes1)][len(phonemes2)] / max_possible if max_possible > 0 else 0.0
    
    def _calculate_single_phoneme_similarity(self, p1: str, p2: str) -> float:
        """计算单个音素相似度"""
        if p1 == p2:
            return 1.0
        
        # 检查音韵映射
        for category, mappings in self.phonetic_mappings.items():
            for mapping in mappings:
                if p1 in mapping.romanizations and p2 in mapping.romanizations:
                    return mapping.weight * 0.9
        
        # 基于字符相似度的回退
        if len(p1) == 1 and len(p2) == 1:
            return self._character_similarity(p1, p2)
        
        return 0.0
    
    def _character_similarity(self, c1: str, c2: str) -> float:
        """计算字符相似度"""
        # 基本元音音素相似度
        vowel_groups = [
            ['a', 'ā', 'à', 'á', 'â', 'ă'],
            ['e', 'ē', 'è', 'é', 'ê', 'ë'],
            ['i', 'ī', 'ì', 'í', 'î', 'ï', 'y'],
            ['o', 'ō', 'ò', 'ó', 'ô', 'ö'],
            ['u', 'ū', 'ù', 'ú', 'û', 'ü']
        ]
        
        for group in vowel_groups:
            if c1.lower() in group and c2.lower() in group:
                return 0.8
        
        # 基本辅音相似度
        consonant_groups = [
            ['p', 'b', 'f', 'v'],
            ['t', 'd', 'th'],
            ['k', 'g', 'c', 'q'],
            ['s', 'z', 'c'],
            ['n', 'm'],
            ['r', 'l']
        ]
        
        for group in consonant_groups:
            if c1.lower() in group and c2.lower() in group:
                return 0.7
        
        return 0.0
    
    def _extract_syllables(self, text: str) -> List[SyllableInfo]:
        """提取音节信息"""
        syllables = []
        
        # 检测可能的语言
        detected_lang = self._detect_language_from_text(text)
        
        if detected_lang in self.syllable_patterns:
            patterns = self.syllable_patterns[detected_lang]
            
            # 按空格分割可能的音节
            potential_syllables = re.split(r'[\s\-_]+', text.lower())
            
            for syll_text in potential_syllables:
                if not syll_text:
                    continue
                
                syll_info = self._parse_syllable(syll_text, patterns)
                if syll_info:
                    syllables.append(syll_info)
        
        return syllables
    
    def _parse_syllable(self, syllable: str, patterns: List[str]) -> Optional[SyllableInfo]:
        """解析单个音节"""
        for pattern in patterns:
            match = re.match(pattern, syllable)
            if match:
                groups = match.groups()
                
                # 根据匹配组数决定音节结构
                if len(groups) >= 2:
                    return SyllableInfo(
                        onset=groups[0] if groups[0] else "",
                        nucleus=groups[1] if len(groups) > 1 else "",
                        coda=groups[2] if len(groups) > 2 else "",
                        tone=groups[3] if len(groups) > 3 else "",
                        full=syllable
                    )
        
        # 如果没有匹配的模式，返回简单结构
        return SyllableInfo(full=syllable)
    
    def _calculate_syllable_similarity(self, syllables1: List[SyllableInfo], syllables2: List[SyllableInfo]) -> float:
        """计算音节相似度"""
        if not syllables1 or not syllables2:
            return 0.0
        
        total_score = 0.0
        max_length = max(len(syllables1), len(syllables2))
        
        # 使用最长公共子序列算法
        for i in range(min(len(syllables1), len(syllables2))):
            syll_score = self._compare_syllables(syllables1[i], syllables2[i])
            total_score += syll_score
        
        return total_score / max_length if max_length > 0 else 0.0
    
    def _compare_syllables(self, syll1: SyllableInfo, syll2: SyllableInfo) -> float:
        """比较两个音节"""
        if syll1.full == syll2.full:
            return 1.0
        
        score = 0.0
        
        # 比较各组成部分
        if syll1.onset and syll2.onset:
            if syll1.onset == syll2.onset:
                score += 0.3
            else:
                score += self._character_similarity(syll1.onset, syll2.onset) * 0.2
        
        if syll1.nucleus and syll2.nucleus:
            if syll1.nucleus == syll2.nucleus:
                score += 0.5
            else:
                score += self._character_similarity(syll1.nucleus, syll2.nucleus) * 0.3
        
        if syll1.coda and syll2.coda:
            if syll1.coda == syll2.coda:
                score += 0.2
            else:
                score += self._character_similarity(syll1.coda, syll2.coda) * 0.1
        
        return min(1.0, score)
    
    def _detect_language_context(self, target: str, candidate: str) -> Dict[str, float]:
        """检测语言环境"""
        language_scores = defaultdict(float)
        
        # 基于字符集检测
        target_scripts = self._analyze_script_composition(target)
        candidate_scripts = self._analyze_script_composition(candidate)
        
        # 合并字符集信息
        all_scripts = set(target_scripts.keys()) | set(candidate_scripts.keys())
        
        for script in all_scripts:
            if script == 'latin':
                # 拉丁字母可能对应多种语言
                language_scores['chinese'] += 0.2
                language_scores['japanese'] += 0.2
                language_scores['korean'] += 0.2
                language_scores['arabic'] += 0.1
            elif script == 'han':
                language_scores['chinese'] += 0.8
            elif script == 'hiragana' or script == 'katakana':
                language_scores['japanese'] += 0.8
            elif script == 'hangul':
                language_scores['korean'] += 0.8
            elif script == 'arabic':
                language_scores['arabic'] += 0.8
        
        # 基于预定义映射的语言推断
        for lang_key in self.predefined_mappings:
            lang = lang_key.split('_')[0]
            for mapping in self.predefined_mappings[lang_key]:
                if (target.lower() in [mapping.original.lower(), mapping.romanized.lower()] or
                    candidate.lower() in [mapping.original.lower(), mapping.romanized.lower()]):
                    language_scores[lang] += 0.3
        
        # 标准化分数
        total_score = sum(language_scores.values())
        if total_score > 0:
            for lang in language_scores:
                language_scores[lang] /= total_score
        
        return dict(language_scores)
    
    def _analyze_script_composition(self, text: str) -> Dict[str, float]:
        """分析文本的文字系统组成"""
        script_counts = defaultdict(int)
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                script = self._get_character_script(char)
                script_counts[script] += 1
        
        # 计算比例
        script_ratios = {}
        if total_chars > 0:
            for script, count in script_counts.items():
                script_ratios[script] = count / total_chars
        
        return script_ratios
    
    def _get_character_script(self, char: str) -> str:
        """获取字符的文字系统"""
        code_point = ord(char)
        
        if 0x4E00 <= code_point <= 0x9FFF:  # 汉字
            return 'han'
        elif 0x3040 <= code_point <= 0x309F:  # 平假名
            return 'hiragana'
        elif 0x30A0 <= code_point <= 0x30FF:  # 片假名
            return 'katakana'
        elif 0xAC00 <= code_point <= 0xD7AF:  # 韩文
            return 'hangul'
        elif 0x0600 <= code_point <= 0x06FF:  # 阿拉伯文
            return 'arabic'
        elif 0x0400 <= code_point <= 0x04FF:  # 西里尔字母
            return 'cyrillic'
        elif 0x0370 <= code_point <= 0x03FF:  # 希腊字母
            return 'greek'
        elif (0x0041 <= code_point <= 0x005A) or (0x0061 <= code_point <= 0x007A):  # 拉丁字母
            return 'latin'
        else:
            return 'unknown'
    
    def _apply_sound_rules_with_score(self, target: str, candidate: str, rules: List[Tuple[str, str]]) -> float:
        """应用音变规则并计算分数"""
        # 正向音变
        modified_target = self._apply_sound_rules(target, rules)
        if modified_target == candidate:
            return 0.9
        
        # 反向音变
        modified_candidate = self._apply_sound_rules(candidate, rules)
        if modified_candidate == target:
            return 0.9
        
        # 双向音变
        if modified_target == modified_candidate:
            return 0.8
        
        # 部分匹配评分
        partial_score = self._calculate_partial_rule_match(target, candidate, rules)
        return partial_score
    
    def _calculate_partial_rule_match(self, target: str, candidate: str, rules: List[Tuple[str, str]]) -> float:
        """计算部分规则匹配分数"""
        target_transformed = target
        candidate_transformed = candidate
        
        matches = 0
        total_rules = len(rules)
        
        for old, new in rules:
            if old in target_transformed:
                target_transformed = target_transformed.replace(old, new)
                if new in candidate or old in candidate:
                    matches += 1
            
            if old in candidate_transformed:
                candidate_transformed = candidate_transformed.replace(old, new)
                if new in target or old in target:
                    matches += 1
        
        if total_rules == 0:
            return 0.0
        
        # 基础规则匹配分数
        rule_score = matches / (total_rules * 2)  # 因为有正向和反向
        
        # 最终相似度
        final_similarity = self._calculate_edit_distance_similarity(target_transformed, candidate_transformed)
        
        return (rule_score * 0.3 + final_similarity * 0.7) * 0.7  # 最高0.7分
    
    def _calculate_cross_language_phonetic_similarity(self, target: str, candidate: str) -> float:
        """计算跨语言音韵相似度"""
        # 提取音韵特征
        target_features = self._extract_phonetic_features(target)
        candidate_features = self._extract_phonetic_features(candidate)
        
        # 计算特征相似度
        feature_similarity = self._compare_phonetic_features(target_features, candidate_features)
        
        return feature_similarity * 0.6  # 跨语言匹配置信度较低
    
    def _extract_phonetic_features(self, text: str) -> Dict[str, float]:
        """提取音韵特征"""
        features = {
            'vowel_ratio': 0.0,
            'consonant_clusters': 0.0,
            'syllable_count': 0.0,
            'length': len(text),
            'has_tones': 0.0,
            'complexity': 0.0
        }
        
        vowels = 'aeiouāēīōūàèìòùáéíóúâêîôûäëïöü'
        vowel_count = sum(1 for c in text.lower() if c in vowels)
        
        features['vowel_ratio'] = vowel_count / len(text) if text else 0.0
        
        # 音节计数 (简化估算)
        syllable_count = max(1, vowel_count)
        features['syllable_count'] = syllable_count
        
        # 辅音簇检测
        consonant_clusters = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{2,}', text.lower()))
        features['consonant_clusters'] = consonant_clusters
        
        # 声调检测 (变音符号)
        tone_marks = 'āēīōūàèìòùáéíóúâêîôûäëïöü'
        features['has_tones'] = float(any(c in tone_marks for c in text))
        
        # 复杂度 (特殊字符和组合)
        special_chars = len(re.findall(r'[\'`\-_]', text))
        features['complexity'] = special_chars / len(text) if text else 0.0
        
        return features
    
    def _compare_phonetic_features(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """比较音韵特征"""
        similarity = 0.0
        
        # 元音比例相似度
        vowel_diff = abs(features1['vowel_ratio'] - features2['vowel_ratio'])
        similarity += max(0, 1 - vowel_diff * 2) * 0.3
        
        # 音节数相似度
        syll_diff = abs(features1['syllable_count'] - features2['syllable_count'])
        max_syllables = max(features1['syllable_count'], features2['syllable_count'])
        if max_syllables > 0:
            similarity += max(0, 1 - syll_diff / max_syllables) * 0.4
        
        # 长度相似度
        length_diff = abs(features1['length'] - features2['length'])
        max_length = max(features1['length'], features2['length'])
        if max_length > 0:
            similarity += max(0, 1 - length_diff / max_length) * 0.2
        
        # 声调匹配
        if features1['has_tones'] == features2['has_tones']:
            similarity += 0.1
        
        return similarity
    
    def _detect_script_type(self, text: str) -> str:
        """检测文本的主要文字类型"""
        script_counts = defaultdict(int)
        
        for char in text:
            if char.isalpha():
                script = self._get_character_script(char)
                script_counts[script] += 1
        
        if not script_counts:
            return 'unknown'
        
        return max(script_counts.items(), key=lambda x: x[1])[0]
    
    def _enhance_arabic_romanization_matching(self, target: str, candidate: str) -> float:
        """
        阿拉伯语罗马化匹配增强器
        专门处理阿拉伯语名字和地名的复杂罗马化变体
        """
        # 检测是否包含阿拉伯文字符
        def contains_arabic(text):
            return bool(re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        
        # 检测聊天语言（数字替代）
        def contains_chat_numbers(text):
            return bool(re.search(r'[0-9]', text))
        
        # 如果都不包含阿拉伯文，且不是常见的阿拉伯音韵特征或聊天语言，跳过
        if not contains_arabic(target) and not contains_arabic(candidate):
            arabic_patterns = ['kh', 'gh', 'sh', 'th', 'dh', "'", 'aa', 'ii', 'uu']
            has_arabic_features = any(pattern in target.lower() for pattern in arabic_patterns) or \
                                any(pattern in candidate.lower() for pattern in arabic_patterns)
            has_chat_features = contains_chat_numbers(target) or contains_chat_numbers(candidate)
            
            if not has_arabic_features and not has_chat_features:
                return 0.0
        
        # 阿拉伯语标准化处理
        def normalize_arabic_text(text):
            text = text.lower()
            
            # 特殊处理：聊天语言数字替代（优先处理）
            chat_number_map = {
                '0': 'o',     # 0 -> o
                '1': 'i',     # 1 -> i/l
                '2': "'",     # 2 -> hamza
                '3': "'",     # 3 -> ain/hamza
                '4': 'th',    # 4 -> tha
                '5': 'kh',    # 5 -> kha
                '6': 't',     # 6 -> ta
                '7': 'h',     # 7 -> ha
                '8': 'gh',    # 8 -> ghain
                '9': '',      # 9 -> qaf (often omitted)
            }
            
            # 应用数字替代（如果文本包含数字）
            if contains_chat_numbers(text):
                for num, replacement in chat_number_map.items():
                    text = text.replace(num, replacement)
            
            # 阿拉伯字母标准化映射
            arabic_normalizations = {
                # 基础字母归一化
                'ا': 'a', 'أ': 'a', 'إ': 'a', 'آ': 'aa',
                'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
                'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'dh',
                'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
                'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z',
                'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
                'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
                'ه': 'h', 'و': 'w', 'ي': 'y', 'ة': 'h',
                'ء': '', 'ئ': '', 'ؤ': 'w', 'إ': 'a',
                
                # 处理组合字符
                'لا': 'la', 'لأ': 'la', 'لإ': 'li', 'لآ': 'laa',
                
                # 定冠词处理
                'ال': 'al', 'الا': 'ala', 'الإ': 'ali', 'الأ': 'ala',
            }
            
            # 应用阿拉伯字母映射
            for arabic, latin in arabic_normalizations.items():
                text = text.replace(arabic, latin)
            
            # 处理常见的拉丁化变体
            latin_normalizations = [
                # 声门塞音和重音
                ("'", ""), ("'", ""), ("`", ""), ("ʾ", ""), ("ʿ", ""),
                ("ʼ", ""), ("´", ""), ("̀", ""), ("̂", ""), ("̃", ""),
                
                # 长音简化
                ("aa", "a"), ("ii", "i"), ("uu", "u"), ("oo", "o"), ("ee", "e"),
                ("ā", "a"), ("ī", "i"), ("ū", "u"), ("ō", "o"), ("ē", "e"),
                
                # 双元音标准化
                ("ay", "ai"), ("aw", "au"), ("ey", "ei"), ("ow", "ou"),
                
                # 辅音组合标准化
                ("kh", "h"), ("gh", "g"), ("sh", "s"), ("th", "t"), ("dh", "d"),
                ("ph", "f"), ("ch", "c"),
                
                # 特殊字母和符号
                ("ḥ", "h"), ("ḫ", "kh"), ("ḍ", "d"), ("ṣ", "s"), ("ṭ", "t"), ("ẓ", "z"),
                ("ḏ", "dh"), ("ṯ", "th"), ("ġ", "gh"), ("š", "sh"), ("ğ", "g"),
                
                # 方言变体
                ("j", "g"), ("q", "k"), ("q", ""), ("x", "kh"),
                
                # 重复辅音简化
                ("bb", "b"), ("dd", "d"), ("ff", "f"), ("gg", "g"), ("hh", "h"),
                ("jj", "j"), ("kk", "k"), ("ll", "l"), ("mm", "m"), ("nn", "n"),
                ("pp", "p"), ("qq", "q"), ("rr", "r"), ("ss", "s"), ("tt", "t"),
                ("vv", "v"), ("ww", "w"), ("xx", "x"), ("yy", "y"), ("zz", "z"),
                
                # 定冠词处理
                ("al-", ""), ("el-", ""), ("ar-", ""), ("as-", ""), ("at-", ""),
                ("an-", ""), ("ad-", ""), ("az-", ""), ("ash-", ""), ("al", ""),
                
                # 词尾处理
                ("ah", "a"), ("eh", "e"), ("ih", "i"), ("uh", "u"), ("oh", "o"),
                ("at", "a"), ("et", "e"), ("it", "i"), ("ut", "u"), ("ot", "o"),
                ("un", ""), ("an", ""), ("in", ""), ("on", ""),
                
                # 半元音处理
                ("w", "u"), ("y", "i"), ("ya", "ia"), ("wa", "ua"),
            ]
            
            # 应用拉丁化标准化
            for old, new in latin_normalizations:
                text = text.replace(old, new)
            
            # 移除非字母数字字符
            text = re.sub(r'[^a-zA-Z0-9]', '', text)
            
            return text
        
        # 特殊处理：聊天语言匹配
        def chat_language_match(chat_text, standard_candidates):
            """专门处理聊天语言（数字替代）的匹配"""
            if not contains_chat_numbers(chat_text):
                return 0.0, None
            
            # 常见的聊天语言模式映射
            chat_patterns = {
                'mo7amed': ['muhammad', 'mohammed', 'mohamed'],
                'mo7ammed': ['muhammad', 'mohammed', 'mohamed'],
                'mu7ammad': ['muhammad', 'mohammed', 'mohamed'],
                'a7med': ['ahmad', 'ahmed'],
                'a7mad': ['ahmad', 'ahmed'],
                '3ali': ['ali'],
                '3ly': ['ali'],
                '5alid': ['khalid', 'khaled'],
                '5aled': ['khalid', 'khaled'],
                '7asan': ['hassan', 'hasan'],
                '7assan': ['hassan', 'hasan'],
                '7usain': ['hussain', 'hussein'],
                '7ussein': ['hussain', 'hussein'],
                'fatma7': ['fatma', 'fatimah'],
                '3aisha': ['aisha', 'aysha'],
                '3aysha': ['aisha', 'aysha'],
            }
            
            chat_lower = chat_text.lower()
            best_score = 0.0
            best_match = None
            
            # 直接模式匹配
            if chat_lower in chat_patterns:
                expected_forms = chat_patterns[chat_lower]
                for candidate in standard_candidates:
                    if candidate.lower() in expected_forms:
                        return 1.0, candidate
            
            # 更灵活的匹配
            for pattern, expected_forms in chat_patterns.items():
                if self._calculate_edit_distance_similarity(chat_lower, pattern) >= 0.8:
                    for candidate in standard_candidates:
                        if candidate.lower() in expected_forms:
                            score = 0.95
                            if score > best_score:
                                best_score = score
                                best_match = candidate
            
            return best_score, best_match
        
        # 首先尝试聊天语言匹配
        if contains_chat_numbers(target):
            chat_score, chat_match = chat_language_match(target, [candidate])
            if chat_score > 0:
                return chat_score
        
        # 标准化两个文本
        norm_target = normalize_arabic_text(target)
        norm_candidate = normalize_arabic_text(candidate)
        
        # 如果标准化后完全匹配
        if norm_target == norm_candidate:
            return 1.0
        
        # 计算标准化后的相似度
        if len(norm_target) == 0 or len(norm_candidate) == 0:
            return 0.0
        
        # 使用编辑距离计算相似度
        edit_distance = self._calculate_edit_distance(norm_target, norm_candidate)
        max_len = max(len(norm_target), len(norm_candidate))
        similarity = 1.0 - (edit_distance / max_len)
        
        # 如果相似度较高，应用额外的阿拉伯语特定检查
        if similarity >= 0.6:
            # 检查子字符串匹配
            substr_score = 0.0
            if norm_target in norm_candidate or norm_candidate in norm_target:
                substr_score = 0.2
            
            # 检查公共前缀/后缀
            prefix_len = 0
            suffix_len = 0
            min_len = min(len(norm_target), len(norm_candidate))
            
            # 公共前缀
            for i in range(min_len):
                if norm_target[i] == norm_candidate[i]:
                    prefix_len += 1
                else:
                    break
            
            # 公共后缀
            for i in range(1, min_len + 1):
                if norm_target[-i] == norm_candidate[-i]:
                    suffix_len += 1
                else:
                    break
            
            affix_score = (prefix_len + suffix_len) / max_len * 0.3
            
            # 最终分数
            similarity = min(1.0, similarity + substr_score + affix_score)
        
        # 对于阿拉伯语，适当提高匹配阈值
        if similarity >= 0.7:
            return similarity
        
        return similarity * 0.8  # 轻微降权非高相似度匹配
    
    def _normalize_for_comparison(self, text: str) -> str:
        """标准化文本用于比较 - 增强版"""
        # Unicode标准化
        normalized = unicodedata.normalize('NFD', text.lower())
        
        # 移除变音符号
        no_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # 处理常见分隔符：空格、下划线、连字符转换为空字符串
        no_separators = re.sub(r'[\s\-_\'`]', '', no_accents)
        
        # 移除其他标点符号
        alphanumeric = re.sub(r'[^\w]', '', no_separators)
        
        return alphanumeric
    
    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离（Levenshtein距离）"""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_edit_distance_similarity(self, s1: str, s2: str) -> float:
        """基于编辑距离计算相似度"""
        distance = self._calculate_edit_distance(s1, s2)
        max_length = max(len(s1), len(s2))
        
        if max_length == 0:
            return 1.0
        
        return max(0.0, 1.0 - distance / max_length)
    
    def _detect_language_simple(self, text1: str, text2: str) -> str:
        """简单语言检测"""
        # 基于字符集的简单检测
        scripts1 = self._analyze_script_composition(text1)
        scripts2 = self._analyze_script_composition(text2)
        
        all_scripts = set(scripts1.keys()) | set(scripts2.keys())
        
        if 'han' in all_scripts:
            return 'chinese'
        elif 'hiragana' in all_scripts or 'katakana' in all_scripts:
            return 'japanese'
        elif 'hangul' in all_scripts:
            return 'korean'
        elif 'arabic' in all_scripts:
            return 'arabic'
        elif 'cyrillic' in all_scripts:
            return 'russian'
        elif 'greek' in all_scripts:
            return 'greek'
        else:
            return 'unknown'
    
    def _is_original_script(self, text: str) -> bool:
        """判断是否为原始文字（非拉丁字母）"""
        script = self._detect_script_type(text)
        return script != 'latin'
    
    def _detect_language_from_text(self, text: str) -> str:
        """从文本检测语言"""
        script = self._detect_script_type(text)
        
        if script == 'han':
            return 'chinese'
        elif script in ['hiragana', 'katakana']:
            return 'japanese'
        elif script == 'hangul':
            return 'korean'
        elif script == 'arabic':
            return 'arabic'
        elif script == 'cyrillic':
            return 'russian'
        elif script == 'greek':
            return 'greek'
        else:
            # 对于拉丁字母，尝试基于模式推断
            if re.search(r'[āēīōūàèìòùáéíóúâêîôûäëïöü]', text):
                return 'chinese'  # 可能是拼音
            elif re.search(r'[ōū]', text):
                return 'japanese'  # 可能是罗马字
            else:
                return 'universal'


class RomanizationMatcher(EnhancedRomanizationMatcher):
    """罗马化匹配器 - 保持向后兼容性的别名"""
    pass


class RomanizationDatabase:
    """罗马化数据库
    
    用于管理和查询罗马化映射数据
    """
    
    def __init__(self):
        self.mappings: Dict[str, List[RomanizationMapping]] = {}
        self.reverse_index: Dict[str, List[RomanizationMapping]] = {}
    
    def add_mapping(self, mapping: RomanizationMapping):
        """添加映射"""
        language = mapping.language
        if language not in self.mappings:
            self.mappings[language] = []
        
        self.mappings[language].append(mapping)
        
        # 更新反向索引
        self._update_reverse_index(mapping)
    
    def _update_reverse_index(self, mapping: RomanizationMapping):
        """更新反向索引"""
        # 原文索引
        original_key = mapping.original.lower()
        if original_key not in self.reverse_index:
            self.reverse_index[original_key] = []
        self.reverse_index[original_key].append(mapping)
        
        # 罗马化索引
        romanized_key = mapping.romanized.lower()
        if romanized_key not in self.reverse_index:
            self.reverse_index[romanized_key] = []
        self.reverse_index[romanized_key].append(mapping)
    
    def search(self, query: str) -> List[RomanizationMapping]:
        """搜索映射"""
        query_lower = query.lower()
        return self.reverse_index.get(query_lower, [])
    
    def get_all_romanizations(self, original: str) -> List[str]:
        """获取所有罗马化形式"""
        mappings = self.search(original)
        return [m.romanized for m in mappings if m.original.lower() == original.lower()]
    
    def get_all_originals(self, romanized: str) -> List[str]:
        """获取所有原文形式"""
        mappings = self.search(romanized)
        return [m.original for m in mappings if m.romanized.lower() == romanized.lower()]
