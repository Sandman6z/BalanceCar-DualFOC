"""Run ARM GUI/math checks under Unicorn. This does not simulate STM32 peripherals/timing."""
from pathlib import Path
import argparse,json,struct,sys
p=argparse.ArgumentParser();p.add_argument('--python-libs');a=p.parse_args()
if a.python_libs:sys.path.insert(0,a.python_libs)
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_PROT_ALL
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CONTROL, UC_CPU_ARM_CORTEX_M4
from elftools.elf.elffile import ELFFile
root=Path(__file__).resolve().parent
u=Uc(UC_ARCH_ARM, UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
u.mem_map(0x08000000,0x20000,UC_PROT_ALL);u.mem_map(0x20000000,0x8000,UC_PROT_ALL)
u.mem_map(0xE0000000,0x100000,UC_PROT_ALL)
u.mem_write(0xE000ED88,struct.pack('<I',0xF00000))
with (root/'build/probe.elf').open('rb') as f:
 e=ELFFile(f)
 for seg in e.iter_segments():
  if seg['p_type']=='PT_LOAD':u.mem_write(seg['p_vaddr'],seg.data())
 symbols={x.name:x['st_value'] for x in e.get_section_by_name('.symtab').iter_symbols()}
u.mem_write(0x20007000,b'\xa5'*4096)
u.reg_write(UC_ARM_REG_SP,0x20008000);u.reg_write(UC_ARM_REG_LR,0x0801FFF1)
u.reg_write(UC_ARM_REG_CONTROL,0)
try:u.emu_start(symbols['probe_emulation_test']|1,0x0801FFF0,count=300000000)
except Exception as ex:
 print('PC',hex(u.reg_read(UC_ARM_REG_PC)));raise
result=list(struct.unpack('<8I',u.mem_read(symbols['emulation_result'],32)))
stack=bytes(u.mem_read(0x20007000,4096));first=next((i for i,b in enumerate(stack) if b!=0xa5),4096)
report={'engine':'Unicorn 2.1.4 ARM Cortex-M4','status':hex(result[0]),'lvgl_pool_bytes':result[1],'lvgl_free_bytes':result[2],'lvgl_max_used_bytes':result[3],'rendered_frames':result[4],'gui_math_test_stack_bytes_observed':4096-first,'scope':'40 GUI refreshes, 16 dq transform checks and 100 saturation iterations; no peripheral or CPU timing simulation'}
(root/'emulation_result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert result[0]==0x600D,'Test did not return success (possible assertion/OOM/instruction limit)'
assert result[4]>=40 and result[2]>1024,'Insufficient rendering/pool margin'

# Render the actual emulated SSD1315 page buffer for visual inspection.
import zlib
pages=bytes(u.mem_read(symbols['oled_pages'],1024))
w,h,scale=128,64,4
raw=bytearray()
for y in range(h):
 row=bytearray()
 for x in range(w):
  pixel=255 if pages[(y//8)*w+x] & (1 << (y%8)) else 0
  row.extend(bytes([pixel])*scale)
 for unused in range(scale):raw.extend(b'\0'+row)
def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w*scale,h*scale,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(raw)))+chunk(b'IEND',b'')
(root/'gui.png').write_bytes(png)
