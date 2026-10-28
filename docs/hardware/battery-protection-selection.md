# 3S 电池保护与均衡选型调查

更新日期：2026-10-23。当前用户确认：**CW1244ALBS 作为第一版保护与均衡芯片**。这不是样机验证通过或完整 BOM 参数冻结。充电继续使用 IP2326 标准版，IP2326 的 23/24 脚悬空。

## 决策与参数边界

用户明确电池为 3S、电机为 2204 云台电机，并在多厂商、开源项目、市场价格和拆解调查后确认“那就先定 CW1244ALBS 呗”。本轮替代此前“首版不做板载均衡、保护芯片未定”的状态。

CW1244ALBS 用于独立电芯及电池包保护与 3S 被动均衡；保护 MOS、采样电阻、均衡开关/电阻、温度检测、故障延时、恢复条件和实际均衡电流待按对应版本完整手册设计。保护及均衡不依赖 MCU 菜单正常运行，不额外默认配置 I²C/SPI。

此前助手以两颗云台电机估算的电池侧正常 1～3 A、瞬时 5 A、5 A 通路和约 7 A 过流，仅为设计预算；5 mΩ 等也是未确认的示例，不能作为 CW1244ALBS 已定参数。电池电流不同于电机相电流，BMS 过流保护不能代替驱动器限流或绕组热保护。电芯允许放电电流尚未核实。

## 厂商路线对照

| 路线 | 功能与取舍 | 当前定位 |
| --- | --- | --- |
| CellWise CW1244ALBS | 3～4S，电压、充放电过流、温度和断线保护，带均衡功能；均衡外围仍须核对 | 用户已确认第一版主选 |
| iCM CM1033-DS＋3×HYCON HY2213-BB3A | 3S 保护＋每节独立被动均衡；CM1033 不集成电芯温度检测，完整成本需计均衡及温度电路 | 成本对照，未选定 |
| TI BQ7791501PWR | 3～5S，自主均衡及温度保护；内部均衡开关支持最高 50 mA，资料和 EVM 完整 | 研究对照，用户未选定 |
| ABLIC S-8254AAVFT-TB-U＋3×HY2213 | 3～4S 保护，均衡另加；本次小批价格未显示明显优势 | 对照，未选定 |

厂商来源：[CW1244 手册](https://uploadcdn.oneyac.com/attachments/files/brand_pdf/cellwise/11/66/Cellwise-CW1244_V1.5.pdf)、[CM1033 手册](https://dianyuan-public.oss-cn-shenzhen.aliyuncs.com/community/2019/05/22/1558512333-28143.pdf)、[BQ77915 手册](https://www.ti.com/lit/ds/symlink/bq77915.pdf)、[S-8254A 手册](https://www.ablic.com/cn/doc/datasheet/battery_protection/S8254A_C.pdf)、[HY2213 手册](https://www.hycontek.com/wp-content/uploads/DS-HY2213_SC.pdf)。公开 CW1244 简版资料不能替代对应后缀的完整设计资料。

## 价格与供货记录

检索日期：2026-10-23。以下保留本次公开页面显示值，非成交承诺。不同币种、渠道及起订档位分列；均不包含完整电路外围、PCB、装配和运输成本。

| 型号及渠道 | 公开展示价/数量档 | 限制 |
| --- | --- | --- |
| [CW1244 混型号市场聚合页](https://tao.hooos.com/goods_4A5oRnUgt25qmACwwBTNtg-DokRR8IPZxxOReMTq.html) | 约 ¥1.40 起 | 低可信询价线索；混合 CW1244ALBS/AFAS/CW1246，未确认指定型号的小批成交价 |
| [CW1244ALBS / 唯样](https://www.oneyac.com/product/34249328.html) | 无报价，显示起订 2500 | 页面无现货，小批货源仍需核实 |
| [CM1033-DS / 立创旧展示](https://item.szlcsc.com/product/jpg_2785193.html) | ¥1.161 起 | [主页面](https://item.szlcsc.com/2785193.html)显示停售，不当作现货价 |
| [CM1033-DS / 独立分销](https://www.ic-components.com/products/CENTER-TECHNOLOGY/CM1033-DS.jsp) | US$0.2923，1+ | 独立渠道展示，采购前核验来源 |
| [HY2213-BB3A / LCSC](https://www.lcsc.com/de/product-detail/Battery-Management-ICs_HYCON-Tech-HY2213-BB3A_C113632.html) | US$0.1312，5+；US$0.1064，50+ | 3S 每板三颗，首档按单价摊算 US$0.3936，未含均衡 MOS/电阻 |
| [BQ7791501PWR / TI](https://www.ti.com.cn/product/cn/BQ77915/part-details/BQ7791501PWT) | PWR 包装选项 US$1.640，1～99 | 原厂与分销库存不同；不能将 PWT 的另一包装价混用 |
| [BQ7791501PWR / DigiKey](https://www.digikey.com/en/products/detail/texas-instruments/BQ7791501PWR/10716149) | US$2.05，1+ | 正规分销公开阶梯价 |
| [S-8254AAVFT-TB-U / Mouser](https://www.mouser.com/ProductDetail/ABLIC/S-8254AAVFT-TB-U?qs=%2FukktrhNKsYa0eQ41z45AA%3D%3D) | US$1.95，1+；US$1.64，10+ | 仍需另计三颗均衡 IC 及外围 |

CW1244ALBS 的小批可靠货源、完整手册和报价是下一步采购核查项；本次未购买元件。

## 开源与厂商参考

- [CW1244-3S 锂电保护板](https://oshwhub.com/eda_ccqcftukh/cw1244-3s)：作者标注已验证、3 串 21700；未取得完整测试记录，不等同本车验证。
- [SW6306V 三串 65W 充电宝](https://oshwhub.com/kingghost/18650-si-chuan-65w-ban-_sw6306_copy_copy_copy)：CW1244＋被动均衡，整机应用参考。
- [ModBee 18650 电池组](https://github.com/mod-bee/modbee-battery-pack-18650)：BQ7791501PWR、3S；README 部分阈值与 TI 型号表不符，不直接抄参数。
- [S8254A-HY2213-4S](https://github.com/mengguang/S8254A-HY2213-4S)：Eagle 原理图/PCB；4S 对照，改 3S 按厂商接法。
- [CM1033＋ETA3006 三串主动均衡板](https://oshwhub.com/gezhe7/zhu-dong-jun-heng-dian-gan-3-chuan-eta3006)：作者标注打板验证；用于保护与均衡分工参考，主动均衡不是本车已选路线。
- [TI BQ77915 EVM 指南](https://www.ti.com/lit/ug/sluubu2b/sluubu2b.pdf)：原理图、BOM 和测试方法。

部分开源页面全文访问受限，使用了检索索引中的作者说明；未宣称审核完整原理图或复现实测。另有标题写磷酸铁锂、BOM 列 ALBS 且作者未提供充分测试结果的 CW1244 项目，不作为可靠验证依据。

## 商品应用与拆解证据

- [小米 PB1050ZM 原始拆解](https://www.chongdiantou.com/archives/46607.html)：明确三串电池、CW1244 和独立保护 MOS；系列采用证据，不确认所有生产批次或完整后缀。
- [酷态科 40000mAh/300W P+Series 视频发布页](https://www.chongdiantou.com/archives/239840.html)：发布者说明电池保护为 CW1244。
- [斯丹德 100W 相机电池快充仓视频](https://www.bilibili.com/video/BV17EQEByEsw/)：发布者说明使用 CW1244。
- [小能人 X16 储能电源原始拆解](https://www.big-bit.com/news/400752.html)：识别到 CM1033，未确认具体后缀。
- [A&S 11.1V/4.4Ah 电池组厂商规格](https://www.szaspower.com/products/li-ion-battery/18650-11-1v-4400mah-li-ion-battery-pack-cb-ce-un38-3certified.html)：明确列 CW1244ALBS，提供完整后缀的商品应用线索。

视频证据基于发布者说明与配套资料，未逐帧观看。商品采用只能佐证应用，不代替本项目电路审查、保护动作和回生测试。
