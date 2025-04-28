#!/usr/bin/env python3
# Raspberry Pi MQTT Image Processor with Latency Measurement
# Save as mqtt_image_latency.py

import paho.mqtt.client as mqtt
import time
import json
import os
import cv2
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mqtt_image_latency.log"),
        logging.StreamHandler()
    ]
)

# MQTT broker settings (running on this Raspberry Pi)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_IMAGE_FROM_ESP32 = "esp32/image"
MQTT_TOPIC_IMAGE_TO_ESP32 = "raspi/image"

# Image processing settings
IMAGE_DIR = "received_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Global variables for image reception
current_image = bytearray()
received_packets = {}
expected_total_packets = 0
current_timestamp = 0
latency_data = []

# Create MQTT client
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_IMAGE_FROM_ESP32)
    logging.info(f"Subscribed to {MQTT_TOPIC_IMAGE_FROM_ESP32}")

def on_message(client, userdata, msg):
    global current_image, received_packets, expected_total_packets, current_timestamp
    
    try:
        # Find the separator between header and data
        payload = msg.payload
        separator_index = payload.find(b'\n')
        
        if separator_index == -1:
            logging.error("Invalid packet format: no separator found")
            return
        
        # Extract and parse the header
        header_json = payload[:separator_index].decode('utf-8')
        image_data = payload[separator_index + 1:]
        
        header = json.loads(header_json)
        packet_id = header["packetId"]
        total_packets = header["totalPackets"]
        timestamp = header["timestamp"]
        
        logging.info(f"Received packet {packet_id}/{total_packets} from ESP32")
        
        # If this is the first packet of a new image
        if packet_id == 1:
            received_packets = {}
            expected_total_packets = total_packets
            current_timestamp = timestamp
        
        # Store this packet
        received_packets[packet_id] = image_data
        
        # Check if we have received all packets
        if len(received_packets) == expected_total_packets:
            process_complete_image()
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def process_complete_image():
    global received_packets, expected_total_packets, current_timestamp, latency_data
    
    try:
        # Combine all packets to form the complete image
        sorted_packets = [received_packets[i] for i in range(1, expected_total_packets + 1)]
        complete_image_data = b''.join(sorted_packets)
        
        # Calculate reception latency
        reception_time = time.time() * 1000  # current time in milliseconds
        esp32_send_time = current_timestamp
        one_way_latency = reception_time - esp32_send_time
        
        logging.info(f"Image reception latency: {one_way_latency:.2f} ms")
        
        # Save the image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{IMAGE_DIR}/esp32_image_{timestamp}.jpg"
        
        with open(filename, "wb") as f:
            f.write(complete_image_data)
        
        logging.info(f"Saved complete image to {filename}")
        
        # Process the image (apply simple transformation)
        process_and_return_image(filename, complete_image_data)
        
        # Store latency data
        latency_data.append(one_way_latency)
        avg_latency = sum(latency_data) / len(latency_data)
        logging.info(f"Average one-way latency: {avg_latency:.2f} ms")
        
    except Exception as e:
        logging.error(f"Error processing complete image: {e}")

def process_and_return_image(filename, image_data):
    # Load image
    try:
        # Decode image using OpenCV
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logging.error("Failed to decode image")
            return
        
        # Process image - apply a simple effect (grayscale + edge detection)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        processed_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Save processed image
        processed_filename = filename.replace(".jpg", "_processed.jpg")
        cv2.imwrite(processed_filename, processed_img)
        
        # Read processed image as bytes
        with open(processed_filename, "rb") as f:
            processed_image_data = f.read()
        
        # Send processed image back to ESP32
        send_image_to_esp32(processed_image_data)
        
    except Exception as e:
        logging.error(f"Error in image processing: {e}")

def send_image_to_esp32(image_data):
    # Split image into packets and send
    packet_size = 4096  # Max packet size
    total_packets = (len(image_data) + packet_size - 1) // packet_size
    timestamp = int(time.time() * 1000)  # current time in milliseconds
    
    logging.info(f"Sending processed image back to ESP32 ({len(image_data)} bytes in {total_packets} packets)")
    
    for i in range(total_packets):
        packet_id = i + 1
        
        # Create header
        header = {
            "packetId": packet_id,
            "totalPackets": total_packets,
            "timestamp": timestamp
        }
        header_json = json.dumps(header)
        
        # Calculate data for this packet
        start_idx = i * packet_size
        end_idx = min(start_idx + packet_size, len(image_data))
        packet_data = image_data[start_idx:end_idx]
        
        # Combine header and data
        packet = header_json.encode('utf-8') + b'\n' + packet_data
        
        # Send packet
        client.publish(MQTT_TOPIC_IMAGE_TO_ESP32, packet)
        logging.info(f"Sent packet {packet_id}/{total_packets} to ESP32")
        
        # Small delay to avoid overwhelming the ESP32
        time.sleep(0.1)

def main():
    # Set up MQTT callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect to the broker
    logging.info("Connecting to MQTT broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    try:
        # Start the MQTT client loop
        client.loop_forever()
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
        client.disconnect()
    except Exception as e:
        logging.error(f"Error in main loop: {e}")
        client.disconnect()

if __name__ == "__main__":
    main()