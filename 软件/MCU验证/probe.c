/* Resource/configuration probe only. No calibration, arming or motor output start. */
#include "main.h"
#include "usb_device.h"
#include "lvgl.h"
#include "control.h"
#include <string.h>
#include <math.h>

static ADC_HandleTypeDef adc[2];
static TIM_HandleTypeDef tim[4];
static SPI_HandleTypeDef spi[2];
static I2C_HandleTypeDef i2c;
static UART_HandleTypeDef uart;
static uint8_t drawing[1032] __attribute__((aligned(4))), oled_pages[1024];
static uint8_t bus_buffers[872] __attribute__((used,section(".probe_reserve")));
volatile uint32_t control_cycles_max, sample_count, display_frames;
volatile float attitude, gyro_sample, accel_angle_sample, measured_bus = 11.1f;
static lv_obj_t *title, *value, *hint;
volatile uint32_t emulation_result[8];
static uint32_t fake_tick;
static uint32_t test_tick(void) { return fake_tick; }

void Error_Handler(void) { __disable_irq(); for (;;) {} }
void SystemClock_Config(void) {
    RCC_OscInitTypeDef o = {0}; RCC_ClkInitTypeDef c = {0};
    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);
    o.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    o.HSIState = RCC_HSI_ON; o.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    o.PLL.PLLState = RCC_PLL_ON; o.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    o.PLL.PLLM = RCC_PLLM_DIV4; o.PLL.PLLN = 85;
    o.PLL.PLLP = RCC_PLLP_DIV2; o.PLL.PLLQ = RCC_PLLQ_DIV2; o.PLL.PLLR = RCC_PLLR_DIV2;
    if (HAL_RCC_OscConfig(&o) != HAL_OK) Error_Handler();
    c.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
    c.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    c.AHBCLKDivider = RCC_SYSCLK_DIV1; c.APB1CLKDivider = RCC_HCLK_DIV1; c.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&c, FLASH_LATENCY_4) != HAL_OK) Error_Handler();
}
static void peripherals(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE(); __HAL_RCC_GPIOB_CLK_ENABLE(); __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOF_CLK_ENABLE(); __HAL_RCC_SYSCFG_CLK_ENABLE(); __HAL_RCC_PWR_CLK_ENABLE();
    HAL_PWREx_DisableUCPDDeadBattery();
    /* All motor/charge enable pins remain low, even while exercising USB and LVGL. */
    GPIO_InitTypeDef g = {0};
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_8|GPIO_PIN_13|GPIO_PIN_14, GPIO_PIN_RESET);
    g.Pin = GPIO_PIN_8|GPIO_PIN_13|GPIO_PIN_14; g.Mode = GPIO_MODE_OUTPUT_PP; g.Pull = GPIO_PULLDOWN;
    HAL_GPIO_Init(GPIOB, &g);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_0|GPIO_PIN_1, GPIO_PIN_RESET);
    g.Pin = GPIO_PIN_0|GPIO_PIN_1; HAL_GPIO_Init(GPIOC, &g);
    HAL_GPIO_WritePin(GPIOF, GPIO_PIN_1, GPIO_PIN_RESET);
    g.Pin = GPIO_PIN_1; HAL_GPIO_Init(GPIOF, &g); /* ARM clock stays low; no authorization pulses. */
    __HAL_RCC_ADC12_CLK_ENABLE(); __HAL_RCC_TIM1_CLK_ENABLE(); __HAL_RCC_TIM8_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE(); __HAL_RCC_TIM17_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE(); __HAL_RCC_SPI3_CLK_ENABLE();
    __HAL_RCC_I2C1_CLK_ENABLE(); __HAL_RCC_USART3_CLK_ENABLE();
    for (unsigned i = 0; i < 2; ++i) {
        adc[i].Instance = i ? ADC2 : ADC1;
        adc[i].Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
        adc[i].Init.Resolution = ADC_RESOLUTION_12B; adc[i].Init.DataAlign = ADC_DATAALIGN_RIGHT;
        adc[i].Init.ScanConvMode = ADC_SCAN_ENABLE; adc[i].Init.NbrOfConversion = 1;
        adc[i].Init.EOCSelection = ADC_EOC_SINGLE_CONV;
        if (HAL_ADC_Init(&adc[i]) != HAL_OK) Error_Handler();
        ADC_InjectionConfTypeDef j = {0};
        j.InjectedSamplingTime = ADC_SAMPLETIME_24CYCLES_5;
        j.InjectedNbrOfConversion = 2;
        j.ExternalTrigInjecConv = ADC_EXTERNALTRIGINJEC_T1_TRGO2;
        j.ExternalTrigInjecConvEdge = ADC_EXTERNALTRIGINJECCONV_EDGE_RISING;
        j.InjectedRank = ADC_INJECTED_RANK_1; j.InjectedChannel = i ? ADC_CHANNEL_2 : ADC_CHANNEL_1;
        if (HAL_ADCEx_InjectedConfigChannel(&adc[i], &j) != HAL_OK) Error_Handler();
        j.InjectedRank = ADC_INJECTED_RANK_2; j.InjectedChannel = ADC_CHANNEL_3;
        if (HAL_ADCEx_InjectedConfigChannel(&adc[i], &j) != HAL_OK) Error_Handler();
    }
    ADC_MultiModeTypeDef multi = {0}; multi.Mode = ADC_DUALMODE_INJECSIMULT;
    if (HAL_ADCEx_MultiModeConfigChannel(&adc[0], &multi) != HAL_OK) Error_Handler();
    TIM_TypeDef *instances[] = {TIM1,TIM8,TIM4,TIM17};
    for (unsigned i = 0; i < 4; ++i) {
        tim[i].Instance = instances[i]; tim[i].Init.Period = i < 2 ? 4250 : 211;
        tim[i].Init.CounterMode = i < 2 ? TIM_COUNTERMODE_CENTERALIGNED1 : TIM_COUNTERMODE_UP;
        if (i == 3) { tim[i].Init.Prescaler = 169; tim[i].Init.Period = 629; }
        tim[i].Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
        if (HAL_TIM_PWM_Init(&tim[i]) != HAL_OK) Error_Handler();
        TIM_OC_InitTypeDef oc = {0}; oc.OCMode = TIM_OCMODE_PWM1;
        oc.Pulse = i < 2 ? 2125 : 106; oc.OCPolarity = TIM_OCPOLARITY_HIGH;
        if (HAL_TIM_PWM_ConfigChannel(&tim[i], &oc, TIM_CHANNEL_1) != HAL_OK) Error_Handler();
        if (i < 2) {
            HAL_TIM_PWM_ConfigChannel(&tim[i], &oc, TIM_CHANNEL_2);
            HAL_TIM_PWM_ConfigChannel(&tim[i], &oc, TIM_CHANNEL_3);
            TIM_BreakDeadTimeConfigTypeDef b = {0}; b.BreakState = TIM_BREAK_ENABLE;
            b.BreakPolarity = TIM_BREAKPOLARITY_LOW; b.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
            if (HAL_TIMEx_ConfigBreakDeadTime(&tim[i], &b) != HAL_OK) Error_Handler();
        }
    }
    TIM_OC_InitTypeDef trigger = {0}; trigger.OCMode = TIM_OCMODE_PWM2; trigger.Pulse = 4080;
    HAL_TIM_PWM_ConfigChannel(&tim[0], &trigger, TIM_CHANNEL_4);
    TIM_MasterConfigTypeDef master = {0}; master.MasterOutputTrigger = TIM_TRGO_ENABLE;
    master.MasterOutputTrigger2 = TIM_TRGO2_OC4REF;
    master.MasterSlaveMode = TIM_MASTERSLAVEMODE_ENABLE; HAL_TIMEx_MasterConfigSynchronization(&tim[0], &master);
    /* TIM1 enable TRGO starts TIM8 via ITR0; OC4 TRGO2 independently triggers ADC. Bench alignment pending. */
    TIM_SlaveConfigTypeDef slave = {0}; slave.SlaveMode = TIM_SLAVEMODE_TRIGGER; slave.InputTrigger = TIM_TS_ITR0;
    HAL_TIM_SlaveConfigSynchro(&tim[1], &slave);
    for (unsigned i = 0; i < 2; ++i) {
        spi[i].Instance = i ? SPI3 : SPI1; spi[i].Init.Mode = SPI_MODE_MASTER;
        spi[i].Init.Direction = SPI_DIRECTION_2LINES; spi[i].Init.DataSize = SPI_DATASIZE_8BIT;
        spi[i].Init.CLKPolarity = SPI_POLARITY_LOW; spi[i].Init.CLKPhase = SPI_PHASE_2EDGE;
        spi[i].Init.NSS = SPI_NSS_SOFT; spi[i].Init.BaudRatePrescaler = i ? SPI_BAUDRATEPRESCALER_128 : SPI_BAUDRATEPRESCALER_32;
        spi[i].Init.FirstBit = SPI_FIRSTBIT_MSB;
        if (HAL_SPI_Init(&spi[i]) != HAL_OK) Error_Handler();
    }
    i2c.Instance = I2C1; i2c.Init.Timing = 0x40D32A31; i2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    if (HAL_I2C_Init(&i2c) != HAL_OK) Error_Handler();
    uart.Instance = USART3; uart.Init.BaudRate = 115200; uart.Init.WordLength = UART_WORDLENGTH_8B;
    uart.Init.StopBits = UART_STOPBITS_1; uart.Init.Parity = UART_PARITY_NONE; uart.Init.Mode = UART_MODE_TX_RX;
    uart.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&uart) != HAL_OK) Error_Handler();
    /* DMA and physical bus transactions are not started by this compile probe. */
    (void)bus_buffers;
}
static void flush(lv_display_t *display, const lv_area_t *area, uint8_t *pixels) {
    (void)area;
    const uint8_t *image = pixels + 8; /* LVGL I1 palette precedes row-major bits. */
    memset(oled_pages, 0, sizeof oled_pages);
    for (unsigned y = 0; y < 64; ++y) for (unsigned x = 0; x < 128; ++x)
        if (image[y * 16 + x / 8] & (0x80 >> (x % 8))) oled_pages[(y / 8)*128+x] |= 1 << (y%8);
    ++display_frames;
    /* Flush conversion only; SSD1315 init/address and asynchronous I2C driver are pending. */
    lv_display_flush_ready(display);
}
static void gui_init(void) {
    lv_init(); lv_tick_set_cb(HAL_GetTick);
    lv_display_t *d = lv_display_create(128, 64); lv_display_set_color_format(d, LV_COLOR_FORMAT_I1);
    lv_display_set_buffers(d, drawing, NULL, sizeof drawing, LV_DISPLAY_RENDER_MODE_FULL);
    lv_display_set_flush_cb(d, flush);
    lv_obj_t *screen = lv_screen_active();
    lv_obj_set_style_bg_color(screen, lv_color_black(), 0);
    lv_obj_set_style_text_color(screen, lv_color_white(), 0);
    title = lv_label_create(screen); value = lv_label_create(screen); hint = lv_label_create(screen);
    lv_obj_set_pos(title, 0, 0); lv_obj_set_pos(value, 0, 20); lv_obj_set_pos(hint, 0, 43);
    lv_label_set_text(title, "BALANCE STANDBY"); lv_label_set_text(value, "11.1V  0.0deg");
    lv_label_set_text(hint, "K1:page K2:OK");
}
/* Executed only by emulate.py; never enables clocks, ADCs or motor outputs. */
void probe_emulation_test(void) {
    gui_init(); lv_tick_set_cb(test_tick);
    for (unsigned i = 0; i < 40; ++i) {
        lv_label_set_text_fmt(value, "%lumV %ldmdeg", (unsigned long)(9900+i*70), (long)i*10-200);
        fake_tick += 100; lv_timer_handler();
    }
    lv_mem_monitor_t memory; lv_mem_monitor(&memory);
    emulation_result[1] = memory.total_size;
    emulation_result[2] = memory.free_size;
    emulation_result[3] = memory.max_used;
    emulation_result[4] = display_frames;
    Motor m = {0}; m.kp = 0.3f; m.ki = 5.0f; m.target = 1;
    for (unsigned i = 0; i < 16; ++i) {
        m.angle = i * 0.392699082f;
        m.ia = -sinf(m.angle); m.ib = 0.866025404f*cosf(m.angle)+0.5f*sinf(m.angle);
        current_step(&m, 11.1f, 0.0001f);
        if (fabsf(m.u-0.5f)>0.00002f || fabsf(m.v-0.5f)>0.00002f || fabsf(m.w-0.5f)>0.00002f) {
            emulation_result[0] = 0xBAD1; return;
        }
    }
    m.target = 1000;
    for (unsigned i = 0; i < 100; ++i) current_step(&m, 11.1f, 0.0001f);
    if (m.u<0.079f || m.u>0.921f || m.v<0.079f || m.v>0.921f || m.w<0.079f || m.w>0.921f) {
        emulation_result[0] = 0xBAD2; return;
    }
    emulation_result[0] = 0x600D;
}
void ADC1_2_IRQHandler(void) {
    uint32_t start = DWT->CYCCNT;
    if (__HAL_ADC_GET_FLAG(&adc[0], ADC_FLAG_JEOS)) {
        __HAL_ADC_CLEAR_FLAG(&adc[0], ADC_FLAG_JEOS); __HAL_ADC_CLEAR_FLAG(&adc[1], ADC_FLAG_JEOS);
        ++sample_count;
        /* Only retain the computational skeleton; no uncalibrated samples reach PWM. */
        if (!(sample_count & 1)) {
            current_step(&motors[0], measured_bus, 0.0001f);
            current_step(&motors[1], measured_bus, 0.0001f);
        }
        uint32_t elapsed = DWT->CYCCNT - start;
        if (elapsed > control_cycles_max) control_cycles_max = elapsed;
    }
}
extern PCD_HandleTypeDef hpcd_USB_FS;
void USB_LP_IRQHandler(void) { HAL_PCD_IRQHandler(&hpcd_USB_FS); }
void SysTick_Handler(void) { HAL_IncTick(); }
int main(void) {
    HAL_Init(); SystemClock_Config(); peripherals();
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk; DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    MX_USB_Device_Init(); gui_init();
    uint32_t next = 0;
    for (;;) {
        uint32_t now = HAL_GetTick();
        if ((int32_t)(now - next) >= 0) {
            next = now + 100;
            attitude = attitude_step(gyro_sample, accel_angle_sample, 0.1f);
            lv_label_set_text_fmt(value, "%lumV %ldmdeg", (unsigned long)(measured_bus*1000), (long)(attitude*1000));
            lv_timer_handler();
        }
    }
}
