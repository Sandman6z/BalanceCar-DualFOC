"""Check the physical pin plan and analytical ADC window; not a hardware test."""
from pathlib import Path
import argparse,csv,json,xml.etree.ElementTree as E
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--db',default='C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/db/mcu/STM32G431R(6-8-B)Ix.xml');a=p.parse_args()
mcu=E.parse(a.db).getroot()
pins={x.attrib['Name'].split('-')[0]:x for x in mcu if x.tag.endswith('Pin')}
rows=list(csv.DictReader((root/'pinout.csv').open(encoding='utf-8-sig')))
assert len(rows)==52 and len({x['pin'] for x in rows})==52 and len({x['ball'] for x in rows})==52
for row in rows:
 pin=pins[row['pin']];signals={x.attrib.get('Name') for x in pin if x.tag.endswith('Signal')}
 assert row['ball']==pin.attrib['Position']
 assert row['signal'] in signals or row['signal'] in {'GPIO_Input','GPIO_Output','RESET'}
assert set(x['pin'] for x in rows)=={p for p,x in pins.items() if x.attrib.get('Type')=='I/O'}
by_role={r['role']:r for r in rows}
assert by_role['CHARGE_EN']['pin']=='PB8' # Boot pin must be held low, not an I2C pull-up.
assert by_role['NRST']['pin']=='PG10'
for side in ['L','R']:
 for phase in ['A','B']:assert by_role['CURRENT_'+side+'_'+phase]['signal'].startswith('ADC')
dma_header=Path.home()/'STM32Cube/Repository/STM32Cube_FW_G4_V1.6.3/Drivers/STM32G4xx_HAL_Driver/Inc/stm32g4xx_hal_dma.h'
if dma_header.exists():
 text=dma_header.read_text(encoding='utf-8')
 for request in ['SPI1_RX','SPI1_TX','SPI3_RX','SPI3_TX','I2C1_TX','USART3_RX','USART3_TX','TIM4_CH1']:
  assert 'DMA_REQUEST_'+request in text,request
pwm_hz=170e6/(2*4250)
adc_hz=170e6/4
sequence_us=2*(24.5+12.5)/adc_hz*1e6
window_us=(1-0.92)/pwm_hz*1e6
assert pwm_hz==20000 and sequence_us+2.0<window_us
report={'pins_checked':len(rows),'free_gpio':0,'pwm_hz':pwm_hz,'adc_hz':adc_hz,'two_rank_dual_adc_us':sequence_us,'ideal_common_low_window_us_at_max_92_percent_duty':window_us,'trigger_before_peak_us':1.0,'assumed_edge_guard_us':1.0,'adc_irq_period_us':50,'target_worst_adc_isr_us':30,'dma_plan':{'DMA1_CH1':'SPI1_RX','DMA1_CH2':'SPI1_TX','DMA1_CH3':'SPI3_RX','DMA1_CH4':'SPI3_TX','DMA1_CH5':'I2C1_TX','DMA1_CH6':'USART3_RX','DMA2_CH1':'USART3_TX','DMA2_CH2':'TIM4_CH1'},'scope':'Pin AF/ADC availability and analytical timing only. Analog settling, timer sync skew, DMA/IRQ arbitration and ISR timing require bench verification.'}
(root/'pincheck.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
