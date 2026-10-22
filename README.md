# BalanceCar-DualFOC

桌面级小型双轮平衡车，轻载、小功率、不载人。独立 STM32G4 执行双路 FOC、姿态和平衡控制，两颗 DRV8323SRTAR 驱动外置 MOS 三相功率桥。

主控暂以 STM32G431RBI6 为候选，后续可能更换，替代型号未定。项目目前处于方案设计阶段，原理图、PCB 和固件工程尚未纳入仓库。

## 当前方案

| 分类 | 文档 | 内容 |
| --- | --- | --- |
| 总体方案 | [整车总体方案](docs/architecture/overall-plan.md) | 整车架构、驱动设计与模块关系 |
| 决策状态 | [当前选型状态](docs/project/decisions.md) | 已确定、候选和待验证事项 |
| 硬件选型 | [主控、驱动与传感器](docs/hardware/component-selection.md) | 当前器件方案及选型约束 |
| 接口采样 | [接口与采样预算](docs/hardware/interface-budget.md) | IO、PWM、ADC 与总线要求 |
| 电源结构 | [电源、机械与标定](docs/hardware/power-mechanics.md) | 电池、Buck、回生和安装规划 |
| 控制验证 | [控制与分阶段验证](docs/development/control-validation.md) | 软件路线、故障流程和验证步骤 |
| 开发环境 | [云端开发环境](docs/development/cloud-environment.md) | 当前工具和构建条件 |
| 待定事项 | [待确认清单](docs/project/information-needed.md) | 需要继续讨论的问题与工程资料 |

## 文档维护

本仓库只维护当前最新版方案。每讨论完成一部分，更新对应模块；涉及架构或选型变化时，同步总体方案和当前选型状态。未知信息先确认，候选不写成定案，未执行的验证不写成通过。

目前没有固件源码、依赖清单、构建脚本或测试套件，尚不能编译、运行或验证实车。

## 许可证

参见 [LICENSE](LICENSE)。
