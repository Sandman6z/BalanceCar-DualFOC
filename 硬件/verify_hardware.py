"""Datasheet-based arithmetic and ideal logic checks. No board or SPICE simulation."""
from pathlib import Path
import itertools,json,math
root=Path(__file__).resolve().parent
# Currents below are design allocations, NOT measured maxima.
loads={'mcu':0.100,'encoders':0.030,'imu':0.005,'oled':0.050,'misc':0.015,'drv_vref':0.006}
base=sum(loads.values());avg=base+0.100;peak=base+3.3/13
ldo_power=(5-3.3)*avg;ldo_peak=(5-3.3)*peak
assert (5-3.3)*0.2>0.300
thermal={'allocations_3v3_A':loads,'base_A':base,'buzzer_on_average_A':avg,'resistive_buzzer_peak_upper_bound_A':3.3/13,'total_peak_allocation_A':peak,'ME6211_SOT23_listed_limit_W':0.300,'LDO_average_W':ldo_power,'LDO_peak_W_not_continuous_rating':ldo_peak,'ME6211_5V_to_3V3_absolute_ceiling_A_before_derating':0.300/1.7}
# 5 V source power: conservative WS2812 allocation; ESP supply scenarios are allocations.
rail5=avg+4*.060+3.3*.5/(5*.85)+.015
rail5_heavy=avg+4*.060+3.3*1/(4.75*.8)+.015
charge_nom=12.6*.5/(5*.85)
charge_corner=12.6*.55/(4.75*.8)
usb={'baseline_5V_rail_A':rail5,'charger_only_nominal_USB_A':charge_nom,'nominal_total_USB_A':rail5+charge_nom,'heavy_4V75_total_USB_A':rail5_heavy+charge_corner,'available_battery_charge_A_with_1V5A_source_and_1A_core':max(0,(1.5-1.0)*5*.85/12.6),'IP2326_RISET_ohms_for_0V5A':90000/.5,'note':'Do not multiply battery-side charge current by 3 or equate it with USB current. Input-current limiting must cover both branches.'}
assert charge_nom>1.4 and usb['heavy_4V75_total_USB_A']>3
# Actual input after the MUX and wiring, not an ideal 5 V source.
ext_vin=4.75-1.5*.15-.1
assert ext_vin<4.5
buck={'TPS563201_extension_input_example_V':ext_vin,'TPS563201_min_recommended_V':4.5,'main_L_H':3.3e-6,'main_ripple_A_at_12V6':5*(1-5/12.6)/(3.3e-6*580e3),'FB_54k9_10k_output_nominal_V':.768*(1+54.9/10),'5V_MUX_drop_V_at_1V5A_150mOhm':1.5*.15}
# DRV current-sense static margins and uncalibrated error.
shunt={'R_ohm':.010,'gain':20,'scale_V_per_A':.2,'shunt_W_at_5A':25*.010,'gain_shunt_scale_tolerance_fraction':1.03*1.01-1,'uncalibrated_4mV_input_offset_A':.004/.010,'SEN_OCP_lowest_nominal_A':.25/.010,'SEN_OCP_default_nominal_A':1/.010,'CSA_20x_settling_typical_ns':600,'gate_drive_HS_average_A_using_Qg35nC_3FETs_20kHz':35e-9*3*20000}
assert shunt['SEN_OCP_lowest_nominal_A']==25
# ADC RC note: a 100-ohm / 1 nF output filter takes ~4.6 tau to reach 1%.
shunt['example_100ohm_1nF_1percent_settling_us']=-math.log(.01)*100*1e-9*1e6
# Open drain rising edge to 0.7 VDD; total C is an engineering bound, needs measurement.
spi={'bus_capacitance_assumption_F':50e-12,'pullup_ohms':2200,'open_drain_to_70percent_ns':-math.log(.3)*2200*50e-12*1e9,'DRV_clock_Hz':170e6/128,'DRV_half_clock_ns':.5/(170e6/128)*1e9,'DRV_SDO_delay_max_ns':30,'ENC_clock_Hz':170e6/32,'ENC_64clocks_plus_CS_us':64/(170e6/32)*1e6+4*.35}
assert spi['open_drain_to_70percent_ns']+30+20<spi['DRV_half_clock_ns']
# Hysteresis corners: deliberately conservative initial reference + temperature drift,
# offset/CMRR allowance, resistor tolerance, internal hysteresis and loaded output swing.
def thresholds(rb):
 on=[];off=[]
 for rt,bot,rf,ref,vos,hys,vol,voh in itertools.product([99900,100100],[rb*.999,rb*1.001],[1.5e6*.999,1.5e6*1.001],[1.223*.99,1.260*1.01],[-.012,.012],[.002,.008],[0,.2],[4.7,5.1]):
  k=1+rt/bot+rt/rf
  on.append((ref+vos+hys/2)*k-vol*rt/rf)
  off.append((ref+vos-hys/2)*k-voh*rt/rf)
 k=1+100000/rb+100000/1.5e6
 return {'Rb_ohm':rb,'nominal_on_V':(1.242+.003)*k,'nominal_off_V':(1.242-.003)*k-5*100000/1.5e6,'on_envelope_V':[min(on),max(on)],'off_envelope_V':[min(off),max(off)],'scope':'Conservative design envelope, not a manufacturer guarantee or SPICE simulation; reference drift assumed additionally +/-1%, equivalent offset/CMRR +/-12mV.'}
old=thresholds(10300);new=thresholds(10000)
assert old['off_envelope_V'][0]<12.7 and new['off_envelope_V'][0]>12.8
regen={'old_13V4_13V0_proposal':old,'revised_13V8_13V4_proposal':new,'resistor_W_at_13V8_10ohm':13.8**2/10,'full_on_absorption_A_at_13V8_10ohm':13.8/10,'full_on_bus_V_for_2A_and_10ohm':2*10,'coldstart_scenario_V_from_6V_2A_5ms_Cminus20percent':6+2*.005/(470e-6*.8),'TPS70950_startup_max_under_datasheet_test_ms':1.5,'TLV3012B_power_on_typical_ms_no_guaranteed_max':1.9,'note':'The 5ms/2A cold-start scenario is an assumption, not a measured current or bounded start time. 470uF and a 10-ohm resistor are not certified adequate.'}
assert regen['coldstart_scenario_V_from_6V_2A_5ms_Cminus20percent']>30
# Ideal DFF: /CLR = nFAULT & EN_L & EN_R; D=1; /PRE=1; CLK is explicit ARM pulse.
class ArmLatch:
 def __init__(self):self.q=False;self.clock=False
 def step(self,nfault,en_l,en_r,clock,vm_ok=True):
  clear_ok=nfault and vm_ok and en_l and en_r
  if not clear_ok:self.q=False
  elif clock and not self.clock:self.q=True
  self.clock=clock
  return self.q
l=ArmLatch();assert not l.step(True,False,False,False)
assert not l.step(True,True,True,False) # Drivers awake, outputs remain masked.
assert l.step(True,True,True,True)
assert not l.step(False,True,True,True) # Asynchronous hardware trip.
assert not l.step(True,True,True,True) # Fault recovery alone must not re-arm.
assert not l.step(True,True,True,False)
assert l.step(True,True,True,True) # Only a deliberate new edge re-arms.
assert not l.step(True,False,True,True) # Reset/one enable low masks BOTH bridges.
assert not l.step(True,True,True,False)
assert l.step(True,True,True,True)
assert not l.step(True,True,True,True,vm_ok=False) # Power loss without an nFAULT assertion.
assert not l.step(True,True,True,True,vm_ok=True) # Power recovery alone must not re-arm.
# 3PWM truth: INL=0 forces both MOS gates off regardless of INH.
for inh in [False,True]:
 inl=False;gh=inl and inh;gl=inl and not inh
 assert not gh and not gl
gh,gl=(True and False),(True and not False)
assert (gh,gl)==(False,True) # Datasheet counterexample to PWM-low == all-gates-off.
logic={'tests':'startup, explicit arming, fault, no automatic recovery, explicit re-arm, reset, VM loss/recovery and 3PWM Hi-Z truth table passed','candidate_parts':['SN74LVC2G74 (one D flip-flop)','SN74LVC1G11 (3-input AND)','TLV3011B or equivalent open-drain VM-valid monitor (not finalized)'],'scope':'Ideal Boolean behavior only; release/recovery timing, reset ramps, leakage and PCB propagation require validation.'}
result={'status':'desk audit; open hardware items remain','ldo':thermal,'usb':usb,'buck':buck,'current_sense':shunt,'spi':spi,'regen':regen,'fault_latch':logic,'open_items':['CW1244ALBS complete parameter B data and pin/peripheral details','Exact battery and motor electrical parameters','OLED module and WS2812 variant','USB power authorization and low-power startup with extension attached','Core latch/MUX and high-side switch schematic','Brake startup/energy and thermal waveforms','All physical measurements']}
(root/'验证结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
