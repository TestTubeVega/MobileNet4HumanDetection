
<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]




<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

This repo implement a MobileNetV2 NN network for Human Detection purpose; aimed testing different design choice for E6908 Spring 2025

This Repo includes code for 3 tests:

Test 1: ESP32 inference test
- Trained and quantized model deployed on ESP32, testing accuracy and inference speed

Test 2: Raspberry pi 5 inference test
- Trained full model deployed on raspberry pi 5, testing accuracy and inference speed

Test 3: Communication latency test
- Utilized MQTT protocol, testing image sending latency between the two devices
do a search and replace with your text editor for the following: `TestTubeVega`, `MobileNet4HumanDetection`, `twitter_handle`, `linkedin_username`, `email_client`, `email`, `project_title`, `project_description`, `project_license`

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and hardware.
Hardware:
* Xiao ESP32S3
* Raspberry pi 5
* Camera capable for the boards
Software:
* Arduino (for ESP32)
  * ArduinoJson (library in Arduino)
  * PubSubClient (library in Arduino)
* python env (for Raspberry pi)
  * paho-mqtt
  * opencv-python
  * numpy
  * tensorflow
  * matplotlib
  * scikit-learn


<!-- USAGE EXAMPLES -->
## Usage

### Test 1: ESP32 Model inference
The MobileNet v2 inference testing code is in folder ./a6908p_inferencing 
The model is finetuned, deployed and modified from the Edge Pulse.
Usage: import the library definition file in the folder to Arduino, set PSRAM to enable; then it is all set to flash

### Test2: Raspberry pi Model inference
The MobileNet v2 inference testing code is in file MV2forHumanDetect.ipynb notebook

Usage: install the required python packages below
  ```sh
  pip install opencv-python numpy tensorflow matplotlib scikit-learn
  ```
and run the notebook for testing.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Test3: MQTT Communication Latency Test
This test includes 2 sets of code
#### ESP32 code: in /ESP32_MQTT_Profiling folder
Usage: install the following library in Arduino:
- ArduinoJson
- PubSubClient

open the file in the Arduino, change the WIFI name in the top of the file to your testing WIFI name, and then the code is ready to flash.

#### Raspberry pi code: in /Raspi_MQTT_Profiling/mqtt_image_latency2.py
Usage: 
1. connect the raspberry pi to the testing WIFI
2. install and config the mqtt broker
   - Run the following command to upgrade and update your system:
      ```sh
      sudo apt update && sudo apt upgrade
      ```
    - Install the Mosquitto Broker
      ```sh
      sudo apt install -y mosquitto mosquitto-clients
      ```
    - open the mosquitto.conf file.
      ```sh
      sudo nano /etc/mosquitto/mosquitto.conf
      ```
    - Move to the end of the file and add the following two lines:
      ```sh
      listener 1883
      allow_anonymous true
      ```
4. install the required python packages below
  ```sh
  pip install paho-mqtt opencv-python numpy tensorflow matplotlib scikit-learn
  ```
4. run the code in the terminal for testing.
  ```sh
  python3 ./Raspi_MQTT_Profiling/mqtt_image_latency2.py
  ```

<!-- ROADMAP -->
## Roadmap

- [x] model deployment on ESP32
- [x] model deployment on Raspberry pi 5
- [x] Communication latency test
    - [x] MQTT publisher and subscriber code on ESP32
    - [x] MQTT broker, publisher and subscriber code on Raspberry pi 5
    - [x] Timing code on ESP32 for latency profiling

See the [open issues](https://github.com/TestTubeVega/MobileNet4HumanDetection/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>




### Top contributors:

<a href="https://github.com/TestTubeVega/MobileNet4HumanDetection/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=TestTubeVega/MobileNet4HumanDetection" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/TestTubeVega/MobileNet4HumanDetection](https://github.com/TestTubeVega/MobileNet4HumanDetection)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Edge Impulse](https://edgeimpulse.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/TestTubeVega/MobileNet4HumanDetection.svg?style=for-the-badge
[contributors-url]: https://github.com/TestTubeVega/MobileNet4HumanDetection/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TestTubeVega/MobileNet4HumanDetection.svg?style=for-the-badge
[forks-url]: https://github.com/TestTubeVega/MobileNet4HumanDetection/network/members
[stars-shield]: https://img.shields.io/github/stars/TestTubeVega/MobileNet4HumanDetection.svg?style=for-the-badge
[stars-url]: https://github.com/TestTubeVega/MobileNet4HumanDetection/stargazers
[issues-shield]: https://img.shields.io/github/issues/TestTubeVega/MobileNet4HumanDetection.svg?style=for-the-badge
[issues-url]: https://github.com/TestTubeVega/MobileNet4HumanDetection/issues
[license-shield]: https://img.shields.io/github/license/TestTubeVega/MobileNet4HumanDetection.svg?style=for-the-badge
[license-url]: https://github.com/TestTubeVega/MobileNet4HumanDetection/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
