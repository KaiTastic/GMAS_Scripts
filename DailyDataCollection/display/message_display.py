"""
消息显示器 - 专门处理通用消息显示功能
"""


class MessageDisplay:
    """消息显示器 - 负责通用消息的显示功能"""
    
    @staticmethod
    def show_completion():
        """显示完成消息"""
        print(f"所有待接收的文件已经全部接收完成,退出监视...")
    
    @staticmethod
    def show_file_detected(filename: str):
        """显示检测到文件"""
        print(f'\n监测到KMZ文件: {filename}')
    
    @staticmethod
    def show_validation_error(filename: str, error_type: str):
        """显示验证错误"""
        error_messages = {
            'invalid_name': f"文件名称不符合要求（无法判断是完成点文件/计划线路文件）: {filename}",
            'no_valid_finished': f"文件名中没有包含有效完成点名称: {filename}",
            'no_valid_plan': f"文件名中没有包含有效的计划路线名称: {filename}"
        }
        
        message = error_messages.get(error_type, f"未知验证错误: {filename}")
        print(message)
