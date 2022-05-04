# 三维动画实时控制器使用说明

## 准备工作
### 运行环境准备

- 打开`controller.blend`，找到脚本`main.py`；
- 更改第11行中`torch_path`的值为本地包含`torch`环境的目录
	+ 文件夹应当形如`xxxxxxx/lib/python3.9/site-packages`
	+ 由于自己使用的`blender2.93`内置环境为PY3.9，因此外部环境也保持了PY3.9
	+ 环境构建过程：
		- 使用`conda`构建虚拟环境，设定虚拟环境所在路径
		- 在环境中安装：
			+ pytorch >= 1.4（理论上如此，实际上看运气，自己本地环境为1.10.2，并使用cuda加速）
			+ pytorch其他附加包
			+ `MoGlow`需求环境：https://github.com/simonalexanderson/StyleGestures
			+ `pos2BVH`需求环境
	+ 注意：
		- 保持`torch_path`在插入`sys.path`时在队列首位，防止包之间依赖出现问题

### 算法输入准备

- 更改`xxxxxxxx/blender_file/blender_python/data/ai_input.json`
	+ `running_rate`： 每一次调用算法的时间间隔。实际运行时有加入同步锁，理论上可以设置为趋近于0的数来测试算法运行的极限速度，但自己未测试。
	+ 其他项目暂略

- 更改`xxxxxxxx/blender_file/blender_python/ai/moglow/moglow.py`
	+ 需要更改原因：需要正确加载网络训练得到的参数
	+ 61行`hparams`，需要找到正确的`json`文件
	+ `json`文件内容、构造见`MoGlow`：https://github.com/simonalexanderson/StyleGestures
	+ 注意：
		- 务必设置`json`文件中最后一项训练参数路径，否则必然无法运行
		- 目前加载模型与数据到GPU进行运算，设置同样在`json`文件中，请根据需要更改

### pos2BVH准备

- 更改`xxxxxxx/blender_file/blender_python/data/trans_input_new.json`
	+ 文件中使用大写字母定义项目同源程序中在`constants.py`的定义
	+ 最后两项为`blender`读取`bvh`文件时的默认设置，用于调整骨架整体的朝向。其如何设置有待研究。

## 运行

- 在`blender`内部运行`main.py`脚本
- 生成的面板在`3D 视图`区域的工作栏中

### 读取bvh文件

- 设置骨骼架构
	+ 首先设置骨骼所在物体名称
	+ 使用按钮增加骨骼或删除骨骼
	+ 或使用`Import`导入已经存储的骨骼，在`xxxxxxxx/blender_file/bone_structure`中

- 设置读取时的播放速度，之后选取bvh文件并打开
	+ 在开始读取后，有设置部分按键来操作
		- `ESC`为停止读取与插入关键帧
		- 其他按键经测试与`blender`内部冲突……

### 运行算法

- 设置骨骼
- 设置算法所在路径，即`moglow.py`所在文件夹
- 设置`ai_input.json`所在位置
- 如需要用到pos2BVH，设置`trans_input_new.json`所在位置
	+ 建议以上路径设置绝对路径……虽然`blender`提供了GUI选择菜单但是有bug……
- 调整输入参数。
	+ `MoGlow`网络对于参数有点敏感。目前自己使用测试集的参数：（0.6-0.4， 0.9-1.3， 0-0.1）
- 点击运行
	+ 如果打开控制台，有部分`DEBUG`输出
	+ `MoGlow`在我这里运行前初始化大约需要半分钟
- 旁边的`Stop`按键功能已实现，可以停止算法运行并消除内存占用

***
~~以上……祝您好运~~


