/* main.c - Application main entry point */

/*
 * Copyright (c) 2015-2016 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/types.h>
#include <stddef.h>
#include <errno.h>
#include <zephyr.h>
#include <sys/printk.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <device.h>
#include <devicetree.h>
#include <drivers/uart.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/conn.h>
#include <bluetooth/scan.h>
#include <sys/byteorder.h>

#define RECEIVE_BUFF_SIZE 11
#define RECEIVE_TIMEOUT 100
#define SLEEP_TIME_MS   1000

static void config_scan(void);
void change_name(void);
void change_instruction(uint8_t inst);
static struct bt_scan_cb scan_cb;

//Main functionalities of the program
enum instruction_type {
	/** @brief Turn passive scanning on. 
	 * 
	*/
	PASSIVE_SCAN_ON,
	/**
	 * @brief Turn active scanning on.
	 *
	 */
	ACTIVE_SCAN_ON,
	/**
	 * @brief Turn off scanning.
	 *
	 */
	SCAN_OFF,
	/**
	 * @brief Change the name of the target device.
	 *
	 */
	CHANGE_TARGET_NAME,
	/**
	 */
};

static uint8_t rx_buf[RECEIVE_BUFF_SIZE] ={0};
static uint8_t newbuf[10] ={0};
static enum instruction_type instruction;
K_SEM_DEFINE(instance_monitor_sem, 0, 1);


/* Scanning for Advertising packets, using the name to check if the device is the target*/
static void config_scan(void)
{
	int err;

	//Name has to be maximum 8 bytes
	char *target = "Default";

	//General scan parameters
	struct bt_le_scan_param scan_param = {
		.type = BT_LE_SCAN_TYPE_PASSIVE,
		.options = BT_LE_SCAN_OPT_FILTER_DUPLICATE,
		.interval = 0x0010,
		.window = 0x0010,
	};

	//Parameters for matching
	struct bt_scan_init_param scan_init = {
		.connect_if_match = 0,
		.scan_param = &scan_param,
		.conn_param = BT_LE_CONN_PARAM_DEFAULT,
	};
	
	//Initializing scan and registering callback functions
	bt_scan_init(&scan_init);
	bt_scan_cb_register(&scan_cb);
	
	// Add the target name to the filter
	err = bt_scan_filter_add(BT_SCAN_FILTER_TYPE_NAME, target);
	if (err) {
		printk("Scanning filters cannot be set\n");
		return;
	}

	//Enable the filter. The flag is set to false as there is only one filter.
	err = bt_scan_filter_enable(BT_SCAN_NAME_FILTER, false);
	if (err) {
		printk("Filters cannot be turned on\n");
	}
}

//Callback function for a matching name
void scan_filter_match(struct bt_scan_device_info *device_info,
		       struct bt_scan_filter_match *filter_match,
		       bool connectable)
{
	char addr[BT_ADDR_LE_STR_LEN];
	
	//Get the address in a string
	bt_addr_le_to_str(device_info->recv_info->addr, addr, sizeof(addr));
	
	//printk("Device found: %s, rssi = %i\n", addr,rssival);
	printk("%i\n",device_info->recv_info->rssi);
}

//Scanning error
void scan_connecting_error(struct bt_scan_device_info *device_info)
{
	printk("Connection to peer failed!\n");
}

//Callback function if no match is found
void scan_filter_no_match(struct bt_scan_device_info *device_info, bool connectable){
}


//Declaring callback functions for the scan filter
BT_SCAN_CB_INIT(scan_cb, scan_filter_match, scan_filter_no_match, scan_connecting_error, NULL);


//Callback function after enabling bluetooth
static void ble_ready(int err)
{
	printk("Bluetooth ready\n");
}


//Handle instructions from the controlller
void change_instruction(uint8_t inst){

	int err;
	char casename[2];
	err = snprintf(casename,2,"%c",inst);

	//Start passive scanning
	if (strcmp(casename,"p") == 0){
		instruction = PASSIVE_SCAN_ON;
	}

	//Start active scanning 
	else if (strcmp(casename,"a") == 0){
		instruction = ACTIVE_SCAN_ON;
	}
	
	//Stop scanning 
	else if (strcmp(casename,"s") == 0){
		instruction = SCAN_OFF;
	}

	//Change name
	else if (strcmp(casename,"c") == 0){
		instruction = CHANGE_TARGET_NAME;
	}


	//Give access to the main thread
	k_sem_give(&instance_monitor_sem);
}


//Funtion to change the name of the target device
void change_name(void){

	char namebuf[9];
	int temp;

	// Decode name into utf-8
	temp = snprintf(namebuf,9,"%c%c%c%c%c%c%c%c"\
	,newbuf[2],newbuf[3],newbuf[4],newbuf[5],newbuf[6],newbuf[7],newbuf[8],newbuf[9]);

	bt_scan_filter_remove_all();
	int err;
	// Add the target name to the filter
	err = bt_scan_filter_add(BT_SCAN_FILTER_TYPE_NAME, namebuf);
	if (err) {
		printk("Scanning filters cannot be set\n");
		return;
	}

	//Clear the pointers
	memset(namebuf,0,9);
	memset(newbuf,0,10);
}

//Handling the UART events
static void uart_cb(const struct device *dev, struct uart_event *evt, void *user_data)
{
	switch (evt->type)
	{
	case UART_RX_RDY:

		if(evt->data.rx.len<1){
			break;
		}

		//Save new values
		for (int i = evt->data.rx.offset; i < ((evt->data.rx.len + evt->data.rx.offset)-1); i++)
		{
		newbuf[i - evt->data.rx.offset] = evt->data.rx.buf[i];
		}

		change_instruction(newbuf[1]);
		break;

	case UART_RX_DISABLED:
		uart_rx_enable(dev ,rx_buf,sizeof rx_buf,RECEIVE_TIMEOUT);
		break;

	default:
		break;
	}
}


//Main
void main(void)
{
	int err;

	//Initializing UART
	const struct device *uart= device_get_binding(DT_LABEL(DT_NODELABEL(uart0)));
		if (uart == NULL){
			printk("Could not find  %s!\n\r", DT_LABEL(DT_NODELABEL(uart0)));
		return;
		}
	err = uart_callback_set(uart, uart_cb, NULL);
		if (err){
			printk("could not enable callback error %i\n",err);
			return;
		}
	err = uart_rx_enable(uart ,rx_buf,sizeof rx_buf,RECEIVE_TIMEOUT);
		if (err){
			return;
		}

	//Initializing Bluetooth
	err = bt_enable(ble_ready);
		if (err) {
			printk("Cold not enable Bluetooth\n");
		}
	printk("Bluetooth initialized\n");

	//Initializing the scanning module
	config_scan();

	//Wait for instructions
	while (1){
		
		//Wait for the new instruction
		k_sem_take(&instance_monitor_sem, K_FOREVER);

		switch (instruction)
		{
		//Star passive scanning
		case PASSIVE_SCAN_ON:
			err = bt_scan_start(BT_SCAN_TYPE_SCAN_PASSIVE);
			if (err == -EALREADY)
			{
				printk("Scanning already enable \n");
				break;
			}
			else if (err) {
				printk("Scanning failed to start, err %d\n", err);
			}
			break;
		
		//Start active scanning
		case ACTIVE_SCAN_ON:
			err = bt_scan_start(BT_SCAN_TYPE_SCAN_ACTIVE);
			if (err == -EALREADY)
			{
				printk("Scanning already enable \n");
				break;
			}
			else if (err) {
				printk("Scanning failed to start, err %d\n", err);
			}
			break;

		//Stop scanning
		case SCAN_OFF:
			err = bt_scan_stop();
			if (err == -EALREADY) {
				printk("Scanning is not on");
				break;
			}
			else if (err){
				printk("Scanning failed to stop, err %d\n", err);
			}
			
			printk("Scanning has stopped \n");
			break;
		
		//Change the device name
		case CHANGE_TARGET_NAME:
			change_name();
			break;

		default:
			break;
		}
		
	}	
}

