"""
日志记录器的工厂方法示例
"""

from abc import ABC, abstractmethod

# 日志记录器接口
class Logger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass

# 控制台日志记录器
class ConsoleLogger(Logger):
    def log(self, message: str):
        print(f"Console Logger: {message}")

# 文件日志记录器
class FileLogger(Logger):
    def __init__(self, filename: str):
        self.filename = filename

    def log(self, message: str):
        with open(self.filename, 'a') as file:
            file.write(f"File Logger: {message}\n")

# 日志记录器工厂接口
class LoggerFactory(ABC):
    @abstractmethod
    def create_logger(self) -> Logger:
        pass

# 控制台日志记录器工厂
class ConsoleLoggerFactory(LoggerFactory):
    def create_logger(self) -> Logger:
        return ConsoleLogger()

# 文件日志记录器工厂
class FileLoggerFactory(LoggerFactory):
    def __init__(self, filename: str):
        self.filename = filename

    def create_logger(self) -> Logger:
        return FileLogger(self.filename)

# 客户端代码
def client_code(logger_factory: LoggerFactory):
    logger = logger_factory.create_logger()
    logger.log("This is a log message.")

# 使用工厂方法创建不同的日志记录器
if __name__ == "__main__":
    console_logger_factory = ConsoleLoggerFactory()
    client_code(console_logger_factory)
    
    file_logger_factory = FileLoggerFactory("logfile.txt")
    client_code(file_logger_factory)



