# BalanceCar-DualFOC

桌面级小型双轮平衡车，轻载、小功率、不载人。独立 STM32G4 执行双路 FOC、姿态和平衡控制，两颗 DRV8323SRTAR 驱动外置 MOS 三相功率桥。

主控仅选STM32，要求BGA并给双FOC＋单色OLED上的LVGL留余量，球数不限。2026-10-28技术首选提案为STM32G473VEH6，STM32G491REI6备选；国内小批价格与完整资源映射尚待核实，未冻结型号，GD32已排除。项目目前处于方案设计阶段，原理图、PCB 和固件工程尚未纳入仓库。

更新日期：2026-10-28。完整状态以决策表为准。电机为 2204 云台电机，电池为 3S；IMU 为 ICM-42670-P，每电机双电阻，PWM 按两电机总计 6 路预算。充电采用 IP2326 标准版；用户本轮确认 CW1244ALBS 作为第一版电池保护与被动均衡芯片，替代此前“首版不做板载均衡、保护芯片未定”的状态。保护 MOS、采样电阻、均衡外围、温度检测及电流门限待设计验证；最终 MCU 未定。主板 Buck 主选 TPS563201DDCR，输出 5 V，再由 LDO 生成主板 3.3 V；扩展板采用另一颗同型号 Buck 输出 3.3 V 供 ESP32-S3-WROOM-1-N16R8。TPS562201DDCR 保留备选，LDO 拟用 ME6211C33M5G-N，负载、外围及温升待核算，扩展板输入已确认取主板5 V。

## 当前方案

| 分类 | 文档 | 内容 |
| --- | --- | --- |
| 总体方案 | [整车总体方案](docs/architecture/overall-plan.md) | 整车架构、驱动设计与模块关系 |
| 决策状态 | [当前选型状态](docs/project/decisions.md) | 已确定、候选和待验证事项 |
| 硬件选型 | [主控、驱动与传感器](docs/hardware/component-selection.md) | 当前器件方案及选型约束 |
| 接口采样 | [接口与采样预算](docs/hardware/interface-budget.md) | IO、PWM、ADC 与总线要求 |
| 充电选型 | [IP2326 与 CN3303 对照](docs/hardware/charging-comparison.md) | 规格、采购档位、商业产品证据、USB 手动充电与 BMS 边界 |
| 电池保护 | [保护与均衡选型调查](docs/hardware/battery-protection-selection.md) | CW1244ALBS 确认、其他厂商对照、价格及开源/拆解证据 |
| 全部选型快照 | [当前全部选型与交接](docs/project/current-selection-snapshot.md) | 可独立阅读的完整状态，用于 OneDrive 与云对话同步 |
| 电源结构 | [电源、机械与标定](docs/hardware/power-mechanics.md) | 电池、Buck、回生和安装规划 |
| 电路预计方案 | [电路参考与核查](docs/hardware/circuit-review-proposal.md) | 多 agent 调查、参考设计证据与选型边界 |
| 电源路径预算 | [电源路径与负载预算草案](docs/hardware/power-path-budget.md) | USB 核心供电、保护回路、3.3 V 预算及热核算 |
| 电源运行模式 | [已确认电源与运行模式](docs/hardware/power-operating-modes.md) | 板间连接器、USB VCOM、长按整机开关及充电/电机互锁 |
| 首版交互 | [功能补充与交互草案](docs/project/interaction-and-first-build.md) | 逐项确认、按键/灯光提案、首次校准及后续扩展 |
| 蜂鸣器 | [蜂鸣器选型说明](docs/hardware/buzzer-selection.md) | 小尺寸候选、供电负担、声音条件和定型号流程 |
| 控制验证 | [控制与分阶段验证](docs/development/control-validation.md) | 软件路线、故障流程和验证步骤 |
| 开发环境 | [云端开发环境](docs/development/cloud-environment.md) | 当前工具和构建条件 |
| 待定事项 | [待确认清单](docs/project/information-needed.md) | 需要继续讨论的问题与工程资料 |
| 剩余事项提案 | [整合提案 V0.1](docs/project/remaining-design-proposal.md) | 2026-10-28推荐器件、电源结构、软件与调试参数，供后续修改 |

## 文档维护

本仓库只维护当前最新版方案。每讨论完成一部分，更新对应模块；涉及架构或选型变化时，同步总体方案和当前选型状态。未知信息先确认，候选不写成定案，未执行的验证不写成通过。

目前没有固件源码、依赖清单、构建脚本或测试套件，尚不能编译、运行或验证实车。

## 许可证

参见 [LICENSE](LICENSE)。

2026-10-26 增补：保留四颗 WS2812，增加两颗 0603 LED 和一颗小型蜂鸣器；双电机共用一组制动电阻＋单颗低侧 N-MOS，由硬件比较器＋基准＋迟滞自动控制，MCU 采样监测。推挽比较器直驱待评估，能力不足再加缓冲或低侧驱动器，不默认加 LM5109。具体待定器件与参数见决策表及电源模块。
