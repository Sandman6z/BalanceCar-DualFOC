#include "usbd_cdc_if.h"
#include "usb_device.h"
#include <string.h>
extern USBD_HandleTypeDef hUsbDeviceFS;

static uint8_t rx[APP_RX_DATA_SIZE], tx[APP_TX_DATA_SIZE];
static uint8_t line_coding[7] = {0x00, 0xc2, 0x01, 0, 0, 0, 8};
static int8_t init(void) {
    USBD_CDC_SetTxBuffer(&hUsbDeviceFS, tx, 0);
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, rx);
    return USBD_OK;
}
static int8_t deinit(void) { return USBD_OK; }
static int8_t control(uint8_t cmd, uint8_t *data, uint16_t length) {
    if (length >= 7 && cmd == CDC_SET_LINE_CODING) memcpy(line_coding, data, 7);
    if (length >= 7 && cmd == CDC_GET_LINE_CODING) memcpy(data, line_coding, 7);
    return USBD_OK;
}
static int8_t receive(uint8_t *data, uint32_t *length) {
    /* Compile probe deliberately accepts no motor commands. */
    (void)data; (void)length;
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, rx);
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
    return USBD_OK;
}
static int8_t complete(uint8_t *data, uint32_t *length, uint8_t ep) {
    (void)data; (void)length; (void)ep; return USBD_OK;
}
USBD_CDC_ItfTypeDef USBD_Interface_fops_FS = {init, deinit, control, receive, complete};
