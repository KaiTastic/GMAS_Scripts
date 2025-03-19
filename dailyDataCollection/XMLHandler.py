
import dataclasses
from email.mime import audio
import re
import stat
from turtle import title
import xml.etree.ElementTree as ET
import os
import json
from abc import ABC, ABCMeta, abstractmethod

from docutils import Component
from pandas import describe_option
from sympy import content

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

    def add_child(self, child):
        if isinstance(child, XMLWrapper):
            self.children.append(child)
        else:
            raise ValueError("Child must be an instance of XMLWrapper")

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



class PageContext(object):
    def __init__(self):
        self.param_items: dict = None
        self.data: list = []
        self.page: str = ''
        self.showpage: bool = True


class Page(metaclass=ABCMeta):

    @abstractmethod
    def init(self, context: PageContext) -> None:
        pass

    @abstractmethod
    def pre_render(self, context: PageContext) -> None:
        pass

    @abstractmethod
    def render(self, context: PageContext) -> str:
        pass

    @abstractmethod
    def completed(self, context: PageContext) -> None:
        pass


#框架，web框架的引擎
def page_handler(params: dict, page: Page):

    context = PageContext()
    # 传递参数，可以进行一些预处理，比如数据的获取，数据的处理（清晰）等
    context.param_items = params
    page.init(context)
    page.pre_render(context)
    page.render(context)
    page.completed(context)
    return context.page

class WebPage(Page):

    def init(self, context: PageContext) -> None:
        print('init', context.param_items)

    def pre_render(self, context: PageContext) -> None:
        context.data = ['Apple', 'Banana', 'Orange']

    def render(self, context: PageContext) -> None:
        context.page = '<html><body>'
        for item in context.data:
            context.page += f'<div>{item}</div>'
        context.page += '</body></html>'

    def completed(self, context: PageContext) -> None:
        if not context.showpage:
            context.page = 'Permission denied'

web_page = WebPage()
page_content = page_handler({}, web_page)
print(page_content)





def ff(param = None):
    if param != None:
        print('A')
    else:
        print('B')



class Obj:
    def __eq__(self, other) -> bool:
        return True
    
ff(Obj())



from typing import Optional

def func01(data: Optional[int]) -> None:
    if data:
        print('has data and doing something')


func01("abc")





def f1(data: int, lists: list[int] | None = None) -> list[int]:
    if not lists:
        lists = []
    print(lists)
    return [*lists, data]

raw_lists = [100, 200]
print((f1(1), f1(2, raw_lists), f1(3, raw_lists)))
print(raw_lists)