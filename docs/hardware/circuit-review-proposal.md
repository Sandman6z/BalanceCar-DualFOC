# 整车电路预计方案与参考资料核查

日期：2026-10-26。依据当前决策和三个并行 agent 的分项调查，主 agent 补查主控及双电机驱动。本记录是预计电路方案，未修改器件定案；未完成本车原理图、仿真、PCB 或实测。

## 如何理解“验证过”

- 有测试报告的厂家 EVM/Verified Design：可采用其测试条件下的结果。
- 厂家手册典型应用/参考接法：可作为电路依据，不能称本车已通过测试。
- 商业成品/公开硬件：证明架构有应用，须审查版本、接线与本车的差异。
- 本车工程建议：以下明确标为建议的改动均待确认和验证；不覆盖已有用户定案。

没有找到一套同时覆盖 STM32G4、双 DRV8323S、3S、IP2326、CW1244ALBS 和自主回生控制的完整实测参考，因此按模块复用有依据的电路，统一审查电源、地与故障动作。

## 主控、电机驱动及采样

预计继续采用独立 STM32G4＋DRV8323SRTAR×2＋外置六管桥×2。STM32G431RBI6 保留候选；其双高级定时器和 ADC 资源不等于双 FOC 加所有外围已完成资源验证。按两电机合计 6PWM、每电机双电阻、总计四路电流 ADC 验证；不擅自升级到十二路 PWM 或三电阻。

MCU 最小系统按 ST AN5093 和最终型号手册完成逐供电脚去耦、模拟电源/参考、复位、BOOT、时钟和 SWD。建议保留 HSE 晶体位置、SWDIO/SWCLK/NRST/电源参考/地调试口及关键触发测试点，晶体频率和负载电容不在此冻结。

每路驱动照厂家典型应用检查电荷泵、栅极供电去耦、VM 局部去耦与母线电容；ENABLE 保持上电禁能，nFAULT 独立回 MCU，SDO 上拉和 SPI 模式按手册。栅极电流和栅阻按实际 MOS 栅电荷及波形确定。功率 MOS 先筛选约 30～40 V 耐压等级、在实际驱动电压下有导通电阻保证的器件，属于工程筛选方向，最终耐压需结合钳位最坏值和尖峰验证。

采样电阻按峰值相电流、CSA 增益、有效输出摆幅和热功耗联合选取；使用开尔文连接，输出 RC 与 ADC 采样建立时间配合。双电阻第三通道未使用时，须连同 LS_REF、VDS 保护参考审查，不能简单把整个第三相检测路径接地。先证明两路采样窗口、重建算法和控制时序可用，再冻结引脚与布局。

建议预留两颗驱动独立故障输入，并评估故障对两路 PWM 的硬件联动停机，不能将 nFAULT 不经检查直接当作功率切断。电流软件限幅、VDS 过流保护、BMS 电流保护各自计算。

参考与边界：

- [ST AN5093](https://www.st.com/resource/en/application_note/an5093-getting-started-with-stm32g4-series--hardware-development-boards-stmicroelectronics.pdf)：厂家最小系统参考，第8章含原理图；不是本车封装引脚表。
- [STM32G431 手册](https://www.st.com/resource/en/datasheet/stm32g431rb.pdf)：外设和引脚能力依据。
- [BOOSTXL-DRV8323RS EVM](https://www.ti.com/tool/BOOSTXL-DRV8323RS)：提供硬件文件和驱动评估基础；带 R 版 Buck、单电机及原板采样方案不直接复制到本车无 R 版双电阻架构。
- [DRV8323 手册](https://www.ti.com/lit/ds/symlink/drv8323.pdf)：外围、PWM 模式、CSA、故障和布局依据。
- [TIDA-00774 测试设计](https://www.ti.com/tool/TIDA-00774)、[设计指南](https://www.ti.com/lit/ug/tiducl0/tiducl0.pdf)：含 DRV8323S 功率级及保护/热测试，但为大功率梯形控制、VDS 电流检测；只借鉴驱动与布局，不采用其电流额定值、MOS 并联或检测方案。

## 回生耗能

预计电路：双电机共用母线→制动电阻组→单颗低侧 N-MOS→该母线功率回流地。母线分压/适度滤波→比较器＋基准＋外部正反馈→栅阻/栅极下拉→MOS；另设 MCU 母线 ADC 监测。保持硬件自主动作。

候选 TLV3012B（集成基准）与 TLV3201＋外部基准继续评估，不默认 LM5109。TLV3012B 最坏基准精度须按手册表6.9的 ±1.5%预算，不能只取首页1%；5 V 输出摆幅是在 ±5 mA 条件保证的。TLV3201 的40 ns也不是挂功率MOS后的切换时间。两者均须按实际栅电荷、米勒平台、源/灌电流及栅阻检查；迟滞控制也可能反复快速切换，直驱不合格再加缓冲或低侧驱动器。

电阻、母线电容、比较器参考地和控制供电须在 BMS 或系统开关断开后仍与回生功率桥形成有效回路的一侧。低侧 BMS 的 B−与 P−不能混用。软关机不得先切掉制动控制电源。比较器独立于 MCU 不代表覆盖5 V失效；须明确该失效下的设计边界。

上/下门限先满足正常满充及误差下不误动作、最坏误差和过冲下不超母线器件允许值，再计算分压/迟滞。用双电机总回生电流和能量计算电阻脉冲/连续功率、MOS损耗和母线电容，旧13.2/14 V均未定案。

参考与边界：

- [TI TIPD144](https://www.ti.com/tool/TIPD144)：有仿真、验证结果、原理图、BOM及PCB的迟滞比较器设计；未验证本车制动功率级。
- [TI 正逻辑迟滞比较器](https://www.ti.com/tool/CIRCUIT060078)：适合过压输出高的电阻计算参考。
- [TLV3012B 手册](https://www.ti.com/lit/gpn/tlv3012b)、[TLV3201 手册](https://www.ti.com/lit/ds/symlink/tlv3201.pdf)：候选器件实际能力依据。
- [ODrive Regen Clamp](https://docs.odriverobotics.com/v/latest/hardware/regen-clamp-datasheet.html)：支持多个下游驱动共用耗能，但其10～58 V范围和差压控制不同于本车，不能覆盖完整3S运行范围或直接照搬门限。

## 主板与扩展板供电

预计保留受保护母线→TPS563201DDCR→主板5 V→LDO→3V3_MAIN；扩展板另用 TPS563201DDCR→3V3_ESP，输入已确认取主板5 V。两路3.3 V不并联，扩展板输入损耗和WS2812均计入主板5 V预算。

TPS563201手册表7-2的设计起点：5 V反馈54.9 kΩ/10 kΩ、电感3.3 µH、有效输出电容20～68 µF；3.3 V反馈33.2 kΩ/10 kΩ、电感2.2 µH。仅作厂家应用起点，按最低输入电压、负载峰值、纹波、饱和电流、电容偏压降容和PCB重算，不直接冻结外围BOM。

ME6211C33M5G-N保持拟选。查到微盟V14完整手册，第3页给出C33M5G为3.3 V/SOT23-5，第5页绝对最大表仅标SOT23功耗300 mW，未给板材、铜面积、温度和降额条件；“-N”修订对应性未确认。5→3.3 V在100/150/200 mA分别约0.17/0.255/0.34 W，这提示200 mA已有明显热风险，不能按500 mA电流指标判定可用。先完成典型/峰值负载表和最高环境温度预算，再决定保留或换较好散热封装/其他稳压路线，不擅自换型。

参考：

- [TPS563201手册](https://www.ti.com/lit/ds/symlink/tps563201.pdf)：典型电路和选件计算。
- [TPS563201EVM-715完整指南](https://www.ti.com/lit/ug/slvuak7a/slvuak7a.pdf)：含原理图、布局、BOM、纹波/瞬态/启动测试；原EVM输出1.05 V，不代表本车5 V或扩展板3.3 V已测。
- [ME6211微盟V14手册，LCSC托管](https://datasheet.lcsc.com/datasheet/pdf/d15331d096a848ac81a26b001a32d4e3.pdf?productCode=C82942)：完整家族资料，不等于已完成-N后缀验证。

## USB、充电、保护与均衡

Type-C按USB2.0固定受电设备布置，CC1/CC2各自5.1 kΩ下拉；两组D+及D−分别靠接口合并后接MCU，低电容ESD贴近接口。VBUS进入受限流、防倒灌的充电路径；USB与电池系统电源路径需避免回灌，低电池时USB是否可唤醒MCU/启动充电尚需设计。MCU外部D+上拉、串阻及VBUS检测按最终型号核查，不直接套22 Ω。

CC下拉不授权任取1.5/3 A；OLED手动CHG_EN不能代替硬件限流和USB源供电能力约束。维持不做自动识别的既定方向时，先定义连接条件和保守限流；较大电流需明确供电来源和约束。用户已确认充电期间不使能电机，OLED及其他交互保持正常。

IP2326标准版3S保持已选，按V1.11资料采用CON_SEL经1 kΩ接地、23/24脚未用均衡悬空、EN硬件默认关。充电终止电流表为200～300 mA，低电流充电及系统并联负载对终止行为的影响待验证。输入功率、充电电流和系统负载不能独立按各自最大值预算。

CW1244ALBS继续保持第一版选择；本轮可读V1.5资料仅两页简版，尚不足以冻结保护MOS、采样、均衡、NTC、门限及恢复接线，尤其需拿到准确后缀完整手册和典型图。不能从其他BMS移植数值。逐节测试点、电芯配组和保护恢复测试保留。

参考：

- [ST AN5225 §10.1/图10](https://www.st.com/resource/en/application_note/an5225-introduction-to-usb-typec-power-delivery-for-stm32-mcus-and-mpus-stmicroelectronics.pdf)：厂家USB2.0 Type-C接法。
- [IP2326 V1.11，M5Stack托管](https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1132/IP2326.pdf)：厂家充电典型应用与规格。
- [M5Stack Tab5](https://docs.m5stack.com/en/core/Tab5)：可追溯商品/原理图应用，但为2S，只借鉴IP2326控制和外围思路。
- [CW1244 V1.5两页资料，LCSC托管](https://datasheet.lcsc.com/datasheet/pdf/a04dd9f3ca46ce457aca0e159bb872a9.pdf?productCode=C2758484)：资料不完整，未取得全套电路依据。
- [BQ77915 EVM指南](https://www.ti.com/lit/ug/sluubu2b/sluubu2b.pdf)：只借鉴保护测试方法，不替换已选芯片，不移植外围值。

## 传感器、显示、灯与蜂鸣器

| 模块 | 预计方案 | 边界 |
| --- | --- | --- |
| AS5047P×2 | 编码器板用主板3.3 V；VDD与VDD3V3相连，100 nF就近；SPI共享、各自CS，mode 1与奇偶校验 | 官方5 V供电模式逻辑VIH为0.7×VDD，不默认3.3 V SPI直连；磁铁规格、气隙和安装仍需样件验证 |
| ICM-42670-P | VDD/VDDIO用3.3 V，SPI＋INT1，按厂家图6去耦，远离功率电感、蜂鸣器和机械应力点 | 已找到DK-42670-P实体开发板；本轮完整手册PDF获取失败，不把搜索摘要电容值写成已核验BOM |
| 0.96英寸SSD1315 | 用户已明确I²C OLED模块；核查模块供电、上拉、复位和初始化 | 取代先前SSD1306；不能套用旧模块电流或裸屏接法 |
| WS2812×4 | 5 V供电，建议SN74AHCT1G125将MCU数据转换至5 V；逐颗去耦、首颗串阻预留 | 转换器有厂家3.3→5 V应用依据；最终WS2812版本、供电电流及掉电IO行为需核对 |
| 0603 LED | 已确认蓝、绿各一颗，各自限流；1～2 mA为亮度评估起点 | 用途待定；蓝灯在3.3 V的压差不足时再用5 V＋开关管 |
| 蜂鸣器 | 优先无源压电、约12×12×3 mm、3 V驱动等级，一路普通定时器 | CPT-1203-03-SMT-TR仅为候选；按电容/引脚电流选串阻直驱或缓冲，停止时有放电路径、避免长期直流偏置，不强制使用5 V |
| ESP32扩展 | 独立3.3 V Buck；UART TX/RX/GND及独立板间电源引脚 | 两路3.3 V不并联；一侧断电时检查反向供电，必要时用带Ioff缓冲；模组EN的10 kΩ/1 µF为厂家起点，天线净空按指南 |

参考：

- [AS5047P官方归档手册](https://www.infineon.com/assets/row/public/documents/30/49/infineon-as5047p-datasheet-en.pdf)：供电、SPI和典型接法。
- [DK-42670-P](https://www.invensense.tdk.com/en-us/products/6-axis/dk-42670-p)、[ICM-42670-P手册入口](https://invensense.tdk.com/wp-content/uploads/2021/07/ds-000451_icm-42670-p-datasheet.pdf)：开发板存在已核实，完整PDF本轮未读到。
- [Adafruit OLED硬件下载](https://learn.adafruit.com/monochrome-oled-breakouts/downloads)：可追溯商品原理图/板文件，不能替代任意无料号模块。
- [SN74AHCT1G125](https://www.ti.com/product/SN74AHCT1G125)：输入VIH=2 V及厂家电平转换应用依据。
- [Murata外驱压电驱动说明](https://www.murata.com/en-global/support/faqs/sound/diaphragm/char/sch0001)：直驱与缓冲、串阻及放电依据。
- [ESP32-S3-WROOM-1/1U手册](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)：供电3.0～3.6 V、供电能力至少0.5 A、EN和天线参考；N16R8的GPIO35/36/37被Octal PSRAM占用。

## 监测、软开关与验证顺序

建议预留母线电压 ADC；功率区和电池温度传感接口按实际热源设计。若使用 NTC 分压＋RC 采样，核对温度曲线、容差、自热、断线/短路诊断及 ADC 建立时间；保护芯片 NTC 与 MCU 检测不能未经分析直接共接。保险、反接保护、连接器和断电开关须按整车峰值及回生路径共同审查，暂不定额定电流。软锁存开关完整电路暂缓冻结，先明确关机后哪些电源和耗能路径必须保持。

建议实施顺序：先完成电源路径/BMS断开回路图和负载预算；随后最小系统＋单电机限流验证；再双FOC时序与采样；再用受控电源/能量注入验证回生门限、栅波形和热；最后装车进行满电制动及故障注入。现有39个功能脚预算未包含全部新建议监测/保护接口，暂不改成最终总数。

本轮电源行为已确认，详见[电源与运行模式](power-operating-modes.md)：扩展主板5 V取电、可选安装；USB VCOM及核心供电；充电禁能电机；仅电池长按开关机、开机默认进入平衡。旧建议与此冲突处以该页为准。

2026-10-27批量补充：意外复位后待机、按功能键检查恢复；电池待机无操作超过5分钟软关机；充电异常和电池/主板过温恢复需人工请求。普通提示音可静音，低电量/故障提示不可静音；首次必要校准允许OLED引导与人工确认。首版只做原地平衡，整体紧凑，用户自制3D打印两轮/电池固定底座；后续手机App经ESP32和UART发送控制数据。OLED现为0.96英寸I²C SSD1315；主板BTB候选HC-PBB08-2-16-F-H4.0-G1-R-P-04，配对合高/封装仍待核查。电机授权先做情景估算，不将估算视作额定值；电芯型号仍未确定。按键/LED分配已委托提出方案，软件可参考SimpleFOC/ODrive但未选定。USB自动充电改为“简单可靠才考虑”的条件评估，G431具BC1.2能力不等于已验证整机自动启充；当前仍以默认关闭、菜单手动启充为实现基线。完整已确认范围、交互提案与原厂证据见[首版功能补充与交互草案](../project/interaction-and-first-build.md)。
