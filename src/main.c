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
#include <string.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/conn.h>
#include <bluetooth/uuid.h>
#include <bluetooth/gatt.h>
#include <bluetooth/scan.h>
#include <sys/byteorder.h>

static void start_scan(void);
static struct bt_scan_cb scan_cb;

/* Scanning for Advertising packets, using the name to check if the device is the target
Will call "scan_filter_match" after finding a match*/
static void start_scan(void)
{
	int err;

	//General scan parameters
	struct bt_le_scan_param scan_param = {
		.type = BT_LE_SCAN_TYPE_PASSIVE,
		.options = BT_LE_SCAN_OPT_FILTER_DUPLICATE,
		.interval = 0x0010,
		.window = 0x0010,
	};

	//Parameters for matching
	struct bt_scan_init_param scan_init = {
		.connect_if_match = 1,
		.scan_param = &scan_param,
		.conn_param = BT_LE_CONN_PARAM_DEFAULT,
	};
	
	//Initiating scan and registering callback functions
	bt_scan_init(&scan_init);
	bt_scan_cb_register(&scan_cb);

	//Name for the target device
	char *target;
	target = "Testname";
	
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

	//Scanning, will connect automatically if a match is found.
	err = bt_scan_start(BT_SCAN_TYPE_SCAN_PASSIVE);
	if (err) {
		printk("Scanning failed to start, err %d\n", err);
	}
	printk("Scanning...\n");
}

//Callback function for a matching name, connection takes place after this function is called  
void scan_filter_match(struct bt_scan_device_info *device_info,
		       struct bt_scan_filter_match *filter_match,
		       bool connectable)
{
	char addr[BT_ADDR_LE_STR_LEN];

	//Get the rssi value
	int rssival = device_info->recv_info->rssi;

	bt_addr_le_to_str(device_info->recv_info->addr, addr, sizeof(addr));
	

	printk("Device found: %s, rssi = %i\n", addr,rssival);
}


//Scanning error
void scan_connecting_error(struct bt_scan_device_info *device_info)
{
	printk("Connection to peer failed!\n");
}


//Declaring callback functions for the scan filter
BT_SCAN_CB_INIT(scan_cb, scan_filter_match, NULL, scan_connecting_error, NULL);


//Connection
static void connected(struct bt_conn *conn, uint8_t err)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
	
	//Checking for errors
	if (err) {
		printk("Failed to connect to %s (%u)\n", addr, err);
		start_scan();
		return;
	}

	printk("Connected: %s\n", addr);

	// bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
}



static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	printk("Disconnected: %s (reason 0x%02x)\n", addr, reason);

	//start_scan();
}


//Declaring connection callback functions
static struct bt_conn_cb conn_callbacks = {
	.connected = connected,
	.disconnected = disconnected,
};


//Callback function after enabling bluetooth
static void ble_ready(int err)
{
	printk("Bluetooth ready\n");

	bt_conn_cb_register(&conn_callbacks);
	start_scan();
}


//Main
void main(void)
{
	int err;

	printk("Bluetooth initialized\n");

	err = bt_enable(ble_ready);
}