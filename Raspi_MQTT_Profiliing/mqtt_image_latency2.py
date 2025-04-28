#!/usr/bin/env python3
# Raspberry Pi Camera MQTT Image Processing with Latency Tracking
# Save as mqtt_camera_processor.py

import paho.mqtt.client as mqtt
import time
import json
import os
import cv2
import numpy as np
from datetime import datetime
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mqtt_camera_latency.log"),
        logging.StreamHandler()
    ]
)

# MQTT broker settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_IMAGE_FROM_ESP32 = "esp32/image"
MQTT_TOPIC_IMAGE_TO_ESP32 = "raspi/image"
MQTT_TOPIC_LATENCY = "esp32/latency"

# Image storage settings
IMAGE_DIR = "received_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Global variables for image reception
received_packets = {}
expected_total_packets = 0
current_timestamp = 0
current_image_id = 0
latency_data = []

# Create MQTT client
client = mqtt.Client()

# Lock for thread safety
packet_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_IMAGE_FROM_ESP32)
    client.subscribe(MQTT_TOPIC_LATENCY)
    logging.info(f"Subscribed to {MQTT_TOPIC_IMAGE_FROM_ESP32} and {MQTT_TOPIC_LATENCY}")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_IMAGE_FROM_ESP32:
        process_image_packet(msg.payload)
    elif msg.topic == MQTT_TOPIC_LATENCY:
        try:
            stats = json.loads(msg.payload.decode('utf-8'))
            logging.info("Received latency statistics from ESP32:")
            logging.info(f"  Average latency: {stats['avg_latency_ms']:.2f} ms")
            logging.info(f"  Min latency: {stats['min_latency_ms']} ms")
            logging.info(f"  Max latency: {stats['max_latency_ms']} ms")
            logging.info(f"  Measurements: {stats['measurements']}")
            logging.info(f"  Images sent: {stats['images_sent']}")
            logging.info(f"  Images received: {stats['images_received']}")
        except Exception as e:
            logging.error(f"Error processing latency stats: {e}")

def process_image_packet(payload):
    global received_packets, expected_total_packets, current_timestamp, current_image_id
    
    try:
        # Find the separator between header and data
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
        image_id = header.get("imageId", 0)
        
        # Thread-safe updates to shared data
        with packet_lock:
            logging.info(f"Received packet {packet_id}/{total_packets} for image {image_id}")
            
            # If this is the first packet of a new image
            if packet_id == 1 or image_id != current_image_id:
                received_packets = {}
                expected_total_packets = total_packets
                current_timestamp = timestamp
                current_image_id = image_id
            
            # Store this packet
            received_packets[packet_id] = image_data
            
            # Check if we have received all packets
            if len(received_packets) == expected_total_packets:
                # Use a separate thread to process the image
                # so we don't block the MQTT client loop
                image_processor_thread = threading.Thread(
                    target=process_complete_image,
                    args=(dict(received_packets), expected_total_packets, current_timestamp, current_image_id)
                )
                image_processor_thread.start()
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def process_complete_image(packets, total_packets, timestamp, image_id):
    try:
        # Sort packets by ID
        sorted_packets = []
        all_packets_received = True
        
        for i in range(1, total_packets + 1):
            if i in packets:
                sorted_packets.append(packets[i])
            else:
                logging.warning(f"Missing packet {i}/{total_packets} for image {image_id}")
                all_packets_received = False
        
        if not all_packets_received:
            logging.error("Image incomplete - skipping processing")
            return
        
        # Combine all packets to form the complete image
        complete_image_data = b''.join(sorted_packets)
        
        # Calculate reception latency
        reception_time = time.time() * 1000  # current time in milliseconds
        esp32_send_time = timestamp
        one_way_latency = reception_time - esp32_send_time
        
        logging.info(f"Image {image_id} reception latency: {one_way_latency:.2f} ms")
        
        # Save the image
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{IMAGE_DIR}/image_{image_id}_{timestamp_str}.jpg"
        
        with open(filename, "wb") as f:
            f.write(complete_image_data)
        
        logging.info(f"Saved complete image to {filename}")
        
        # Process the image
        start_process = time.time()
        process_and_return_image(filename, complete_image_data, timestamp, image_id)
        process_time = (time.time() - start_process) * 1000
        
        logging.info(f"Image processing time: {process_time:.2f} ms")
        
        # Store latency data
        latency_data.append(one_way_latency)
        if len(latency_data) > 100:  # Keep only the most recent 100 measurements
            latency_data.pop(0)
            
        avg_latency = sum(latency_data) / len(latency_data)
        logging.info(f"Average one-way latency: {avg_latency:.2f} ms")
        
    except Exception as e:
        logging.error(f"Error processing complete image: {e}")

def process_and_return_image(filename, image_data, timestamp, image_id):
    # Load image
    try:
        # Decode image using OpenCV
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logging.error("Failed to decode image")
            return
        
        # Process image - apply a simple effect (for demonstration)
        # Option 1: Edge detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        processed_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Option 2: Add timestamp and image ID
        timestamp_str = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cv2.putText(processed_img, f"Image ID: {image_id}", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(processed_img, f"Time: {timestamp_str}", (10, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Save processed image
        processed_filename = filename.replace(".jpg", "_processed.jpg")
        cv2.imwrite(processed_filename, processed_img)
        logging.info(f"Saved processed image to {processed_filename}")
        
        # Encode processed image as JPEG
        _, processed_jpeg = cv2.imencode('.jpg', processed_img)
        processed_image_data = processed_jpeg.tobytes()
        
        # Send processed image back to ESP32
        send_image_to_esp32(processed_image_data, timestamp, image_id)
        
    except Exception as e:
        logging.error(f"Error in image processing: {e}")

def send_image_to_esp32(image_data, original_timestamp, image_id):
    # Split image into packets and send
    packet_size = 2048  # Match ESP32 packet size
    total_packets = (len(image_data) + packet_size - 1) // packet_size
    send_timestamp = int(time.time() * 1000)  # current time in milliseconds
    
    logging.info(f"Sending processed image back to ESP32 ({len(image_data)} bytes in {total_packets} packets)")
    
    for i in range(total_packets):
        packet_id = i + 1
        
        # Create header
        header = {
            "packetId": packet_id,
            "totalPackets": total_packets,
            "timestamp": original_timestamp,  # Use original timestamp for latency calculation
            "imageId": image_id
        }
        header_json = json.dumps(header)
        
        # Calculate data for this packet
        start_idx = i * packet_size
        end_idx = min(start_idx + packet_size, len(image_data))
        packet_data = image_data[start_idx:end_idx]
        
        # Combine header and data
        packet = header_json.encode('utf-8') + b'\n' + packet_data
        
        # Send packet
        result = client.publish(MQTT_TOPIC_IMAGE_TO_ESP32, packet)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"Sent packet {packet_id}/{total_packets} to ESP32")
        else:
            logging.error(f"Failed to send packet {packet_id}: {result.rc}")
        
        # Small delay to avoid overwhelming the ESP32
        time.sleep(0.05)

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