"""Build a resource probe, not production firmware. Python 3 and ARM GCC required."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys
p=argparse.ArgumentParser()
p.add_argument('--cube',default=str(Path.home()/'STM32Cube/Repository/STM32Cube_FW_G4_V1.6.3'))
p.add_argument('--lvgl',default=str(Path.home()/'.cache/balancecar/lvgl-v9.2.2'))
a=p.parse_args(); root=Path(__file__).resolve().parent; sdk=Path(a.cube); lv=Path(a.lvgl)
assert (sdk/'Drivers/CMSIS/Device/ST/STM32G4xx/Include/stm32g431xx.h').is_file()
assert (lv/'src/lv_init.c').is_file(), 'Fetch pinned LVGL sources first; see fetch_lvgl.py'
out=root/'build';out.mkdir(exist_ok=True)
gcc=shutil.which('arm-none-eabi-gcc');assert gcc,'ARM GCC missing from PATH'
prefix=str(Path(gcc).parent/'arm-none-eabi-')
inc=[root,lv,sdk/'Drivers/CMSIS/Include',sdk/'Drivers/CMSIS/Device/ST/STM32G4xx/Include',sdk/'Drivers/STM32G4xx_HAL_Driver/Inc',sdk/'Middlewares/ST/STM32_USB_Device_Library/Core/Inc',sdk/'Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc']
flags=['-mcpu=cortex-m4','-mthumb','-mfpu=fpv4-sp-d16','-mfloat-abi=hard','-Os','-ffunction-sections','-fdata-sections','-fstack-usage','-DSTM32G431xx','-DUSE_HAL_DRIVER','-DLV_CONF_INCLUDE_SIMPLE']+['-I'+str(x) for x in inc]
hal=sdk/'Drivers/STM32G4xx_HAL_Driver/Src'
names=['hal','hal_adc','hal_adc_ex','hal_cortex','hal_dma','hal_dma_ex','hal_exti','hal_flash','hal_flash_ex','hal_gpio','hal_i2c','hal_i2c_ex','hal_pcd','hal_pcd_ex','hal_pwr','hal_pwr_ex','hal_rcc','hal_rcc_ex','hal_spi','hal_spi_ex','hal_tim','hal_tim_ex','hal_uart','hal_uart_ex','ll_usb']
sources=sorted(root.glob('*.c'))+[hal/('stm32g4xx_'+n+'.c') for n in names]
sources += sorted((lv/'src').rglob('*.c'))
usblib=sdk/'Middlewares/ST/STM32_USB_Device_Library'
sources += [x for x in (usblib/'Core/Src').glob('*.c') if 'template' not in x.name]+[usblib/'Class/CDC/Src/usbd_cdc.c']
sources += [sdk/'Drivers/CMSIS/Device/ST/STM32G4xx/Source/Templates/system_stm32g4xx.c',sdk/'Drivers/CMSIS/Device/ST/STM32G4xx/Source/Templates/gcc/startup_stm32g431xx.s']
def compile_one(item):
 i,src=item;obj=out/(str(i)+'_'+src.stem+'.o')
 result=subprocess.run([gcc,*flags,'-c',str(src),'-o',str(obj)],capture_output=True,text=True,encoding='utf-8',errors='replace')
 return obj,result
objects=[];logs=[];failed=False
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for obj,r in ex.map(compile_one,enumerate(sources)):
  objects.append(obj)
  if r.stderr:logs.append(r.stderr)
  if r.returncode:failed=True
(out/'compile.log').write_text(''.join(logs),encoding='utf-8')
if failed:
 print(''.join(logs)[-14000:]);sys.exit(1)
elf=out/'probe.elf'
cmd=[gcc,*flags,*map(str,objects),'-T'+str(root/'g431.ld'),'--specs=nano.specs','--specs=nosys.specs','-Wl,--gc-sections,-Map='+str(out/'probe.map'),'-Wl,--print-memory-usage','-lm','-lc','-o',str(elf)]
r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
(out/'link.log').write_text(r.stdout+r.stderr,encoding='utf-8');print(r.stdout+r.stderr)
if r.returncode:sys.exit(r.returncode)
size=subprocess.check_output([prefix+'size.exe','-A',str(elf)],text=True)
(out/'size.txt').write_text(size);print(size)
sections={line.split()[0]:int(line.split()[1]) for line in size.splitlines() if line.startswith('.') and len(line.split())>=3}
flash=sum(sections.get(k,0) for k in ['.isr_vector','.text','.ARM.extab','.ARM.exidx','.preinit_array','.init_array','.fini_array','.data'])
ram=sum(sections.get(k,0) for k in ['.data','.bss','.heap_stack'])
assert flash<=126*1024 and ram<=32*1024
(root/'build_result.json').write_text(json.dumps({'flash_used_bytes':flash,'flash_program_limit_bytes':126*1024,'flash_parameter_reserved_bytes':2048,'flash_program_free_bytes':126*1024-flash,'ram_used_with_reservations_bytes':ram,'ram_free_outside_reservations_bytes':32*1024-ram,'monochrome_font':'probe_font_12: thresholded 1-bit Montserrat, ASCII/symbols only','compiler':subprocess.check_output([gcc,'--version'],text=True).splitlines()[0],'cube':'1.6.3','lvgl':'9.2.2','compiled_sources':len(sources),'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'size_sections':size,'limitations':['Compile/link probe only','No sensor calibration, real motor control validation or OLED/USB hardware test','See emulation_result.json for GUI/math emulator checks; not target hardware high-water','4 KB stack is a reservation, not a measured peak','No complete production safety state machine or Chinese glyph set']},indent=2))
