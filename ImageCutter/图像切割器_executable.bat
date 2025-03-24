chcp 65001

@echo Check the following parameters:
@REM :: 参数1 [--folder_path=]: 为将要切分的图像所在文件夹，请使用双引号""，将遍历所有后缀名为“.jpg”的文件。
@REM :: 参数2 [--split_num=]: 切分的块数，请使用双引号""。
@REM :: 参数3 [--auto_split]: 如果计算的切块数目不一致，是否使用计算的值覆盖。默认为计算值优先，利用计算值覆盖。如果强制需要使用设定的切分块数，则删去参数。[--auto_split]

@echo Press any key to continue

imageCutter.exe --folder_path="D:\MacBook\MacBookDocument\SourceCode\ImageCutter\testImageData" --num_splits="5" --auto_split

pause