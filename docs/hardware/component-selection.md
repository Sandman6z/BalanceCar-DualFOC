# 主控、驱动与传感器

更新日期：2026-10-22。状态见[当前选型状态](../project/decisions.md)。

## 主控

STM32G431RBI6 暂列候选，后续可能更换，替代型号尚未确定。

候选规格：UFBGA64，5×5 mm、0.5 mm 球距；170 MHz Cortex-M4F；128 KB Flash、32 KB 总 RAM；最多 52 GPIO；两个 ADC、三个运放、两个高级电机控制定时器。

最终选型依据完整功能、IO 复用、ADC/PWM 时序、双 FOC 软件支持、Flash/RAM 和执行时间验证。不能只凭主频或引脚数量认定够用，也不能认定 GPIO 上限均可自由分配。

小封装需同时核对出线、板层、板厂工艺、贴装返修和总成本；0.5 mm UFBGA 不默认具有宽松球距封装的出线条件。BGA 自行焊接采用热风或回流方式。

## 三相栅驱与功率桥

已选 DRV8323SRTAR ×2，每电机一颗；SPI 配置、无集成系统 Buck、内置三路 CSA，WQFN40 6×6 mm。每路外置六颗 N-MOS，共十二颗，MOS 完整型号待选。

SPI 用于配置和诊断，实时 PWM 与电流 ADC 由 MCU 处理。CSA 仍需外部采样电阻，也不替代 ADC 通道和同步设计。栅极驱动电流不等于电机可持续电流。

系统使用独立 Buck。DRV8323S 自身的电荷泵和栅极供电仍需按手册配置。具体电路、保护、去耦和启动要求见[总体方案](../architecture/overall-plan.md)。

完整成本须计入两路驱动、MOS、采样、供电、PCB 和装配，当前没有最低成本结论。

## 传感器

IMU 已选择 ICM-42670-P，走四线 SPI 并接数据就绪中断，替换此前的 ICM-42688-P 倾向。需配置采样和滤波、校准零偏并融合加速度计；实际性能受安装、振动和延迟影响，最高采样率不代表控制带宽。

编码器已选择 AS5047P ×2，仅使用 SPI，不使用 ABI/ABZ/UVW 输出。角度由 SPI 读取，速度等由 MCU 基于角度计算。核对 SPI 事务、磁铁规格、气隙、坐标方向、极对数和标定；与驱动器或 IMU 共线前验证总线兼容和调度。

## 已确认外围与采样

每台电机使用两个低侧采样电阻，共四路 ADC；MCU 重建第三相，阻值与增益待定。两台电机总计 6 路 PWM 作为当前预算，按每颗驱动 3PWM 验证软件和采样时序。

SSD1306 I²C OLED；四颗 WS2812 串联；一个 NRST 复位键和两个功能键。暂不加蜂鸣器、普通 LED、CAN 或遥控器。ESP32 扩展板通过 UART 提供 Wi-Fi/蓝牙，USB 数据功能保留。

充电首选 IP2326 标准版，CN3303 为低价备选，MCU EN＋OLED 菜单手动控制。3S 独立 BMS 未选定；详见[充电选型对照](charging-comparison.md)。

## 官方资料

- [STM32G431 数据手册](https://www.st.com/resource/en/datasheet/stm32g431rb.pdf)
- [STM32G431RBI6 型号页](https://estore.st.com/en/stm32g431rbi6-cpn.html)
- [DRV8323 产品页](https://www.ti.com/product/DRV8323)
- [DRV8323 数据手册](https://www.ti.com/lit/ds/symlink/drv8323.pdf)
