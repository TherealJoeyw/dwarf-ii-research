# Dwarf II Software Internals

Community documentation of the DwarfLab Dwarf II smart telescope internals, gathered via SSH and network analysis. The goal is to give developers building third-party tools a clear picture of what is running on the device and how to talk to it.

This page was written with the assistance of anthropic's Claude sonnet 4.6 model however I manually reviewed it , as you can see by the edit history 

> **Note:** The Dwarf II ships with default credentials and an open network interface that makes it easy to access and extend. However this is also a security vulnerability on public Wi-Fi networks. See the [Default Credentials](#default-credentials) section for details.

---

## What can I do with this?

You do not need to be a developer to get something useful out of this. Here are some things anyone can do with a Dwarf II beyond the official app:

**Browse and download your photos without the app**
Open a web browser on any device connected to the same network as your telescope and go to `http://192.168.X.X/sdcard/` (replace with your telescope's IP). You will see all your captured images and can download them directly.

**Use it as a PTZ camera or wildlife cam**
The Dwarf II has pan/tilt motors and a decent sensor. You can point it at a bird feeder, a garden, or anything else and control it remotely from your phone via the DwarfLab app. No astronomy required.

**Host a custom web interface**
nginx is already running and serving files from `/userdata/www/`. The default page at `http://192.168.X.X/` just says "Success". You can replace `index.html` with your own HTML/JS app and get a persistent browser-based controller accessible from any device on the network, no app install required. Changes survive reboots since `/userdata` is on persistent storage. Firmware updates may overwrite this folder, so you would need to re-deploy after updating.

**Stream the live view to OBS or VLC**
The MJPEG stream on port 8092 works in VLC, OBS, ffplay, or any MJPEG player. It requires an active WebSocket session to activate — see the [Live streaming without the app](#live-streaming-without-the-app) section for the full connection sequence and a ready-to-run Python script.

**Access the SD card over FTP**
Connect to `ftp://192.168.X.X` with anonymous login, no password needed. This gives you full read access to the SD card, including all your captured images and session data.

**Pull session metadata and location data**
The app keeps a SQLite database at `/sdcard/DWARF_II/data/device.db` which is accessible via HTTP or FTP without any credentials. It contains target names, RA/Dec coordinates, GPS location, exposure settings, and file hashes for every session. Useful for building your own logging or cataloguing tools.

**Get a root shell**
SSH is open on port 22. The default credentials are `root` / `rockchip`. This gives you a full Linux shell on the Rockchip RV1126 SoC running the telescope. See the sections below for what you can do with it.

**Run custom AI models on the NPU**
The Rockchip NPU is directly accessible via the `rknn_inference` command line tool over SSH. Any model converted to RKNN format can be run at 50-70 FPS on the device itself, without any external compute. Potential uses include bird species classification, custom object detection, or astronomical object recognition. Rockchip maintain an official model zoo at [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) with pre-converted models ready to run.

---

## Live streaming without the app

The MJPEG stream on port 8092 can be accessed without the official app, but the device requires an active WebSocket session on port 9900 before it will serve frames. If the WebSocket session closes, the stream stops.

**Working stream URLs:**

- Telephoto: `http://<device-ip>:8092/mainstream`
- Wide angle: `http://<device-ip>:8092/secondstream`

These work in VLC, ffplay, OBS, or any MJPEG-capable player once the WebSocket session is active. See `dwarf_stream.py` in this repo for a ready-to-run Python script that handles the full connection sequence and opens the stream automatically. It requires `pip install websocket-client` and ffmpeg.

**Required WebSocket command sequence to activate the stream:**

1. Connect to `ws://<device-ip>:9900/?client_id=<any-uuid>`
2. Send `CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA` (16404) with protobuf payload `ReqEnterCamera { client_param: ClientParams { encode_type: 1 } }`
3. Send `CMD_CAMERA_TELE_SET_RTSP_BITRATE_TYPE` (10042) with payload `{ bitrate_type: 1 }` for telephoto, or `CMD_CAMERA_WIDE_SET_RTSP_BITRATE_TYPE` (12032) for wide angle
4. Send `CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE` (10039) for telephoto, or `CMD_CAMERA_WIDE_GET_EXP_MODE` (12003) for wide angle
5. Send `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` (10050) with payload `{ level: 1 }` for telephoto, or `CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY` (12036) for wide angle
6. Send a `"ping"` text message every 5 seconds to keep the session alive
7. Open `http://<device-ip>:8092/mainstream` (telephoto) or `/secondstream` (wide angle)

Command names and protobuf structures from APK decompilation of `com.convergence.dwarflab` (September 2026). See the WsCmd section for numeric values and module assignments.

---

For developers, the sections below document the hardware, running software, network ports, and APIs in detail.

---

## Hardware

**SOC:** Rockchip RV1126, identified from the hostname `RV1126_RV1109` visible on the network.

> Note: the hostname RV1126_RV1109 appears on the network because both chips share the same firmware image. The Dwarf II uses the RV1126 specifically, confirmed by the 2.0 TOPS NPU output from rknn_server — the RV1109 only has 1.2 TOPS.

| Component | Details |
|-----------|---------|
| CPU | Quad-core ARM Cortex-A7 @ 1.5GHz + RISC-V MCU @ 400MHz |
| NPU | 2.0 TOPS, INT8/INT16 |
| GPU | 2D graphics engine + Rockchip RGA accelerator |
| VPU | 4K H.264/H.265 encode and decode |
| RAM | ~1.8GB |
| Sensor | Sony IMX415 Starvis — 8MP telephoto, 2MP wide |
| Lens module | YT10092 with IR0147-28IRC lens, F2.0 aperture |

---

## Software

**OS:** Linux 4.19.111, kernel built 2023-02-02, `armv7l`

**Build info:** The kernel version string reveals the firmware was compiled by a user named `hfx` on a machine called `hfx-RESCUER-R720-15IKBN`, which is a Lenovo Rescuer R720 gaming laptop. Strings in the main application binary reference `/home/liangxin/data_ex/dwarf2/DWARF2_V2/`, suggesting the app was built on a separate machine belonging to a developer named Liangxin. The legal entity behind DwarfLab is Tinyphoton Ltd.

**Firmware version:** 2.2.18, app version 2.6 (from `/userdata/cfg/default_params_configs.yaml`)

**Key processes:**

| Process | Role |
|---------|------|
| `/usr/bin/dwarf2` | Main DwarfLab application |
| `rknn_server` | Rockchip NPU inference server — runs in a loop, restarts on crash |
| `nginx` | HTTP server |
| `dropbear` | SSH server |
| `wpa_supplicant` | WiFi client management |
| `hostapd` | WiFi hotspot |
| `dnsmasq` | DNS/DHCP for hotspot mode |
| `vsftpd` | FTP server — anonymous access to SD card |
| `avahi-daemon` | mDNS/Bonjour |
| `bsa_server` | Bluetooth stack |
| `adbd` | Android Debug Bridge daemon — port 5037 localhost only |

A `voiceAssistant.cpp` exists in the source tree. However, no physical microphone is present on the device — the only ALSA device is a software loopback. The wide angle camera module is a Sunplus SPCA2281 (USB ID 0c45:64ab) which supports audio capture in some configurations, but no audio capture device is registered in this firmware. The voice assistant is likely dead code or planned for a future hardware revision.

The device has RGB LEDs controlled by `rgbPower.cpp` and `rgbPower_driver.cpp`. LEDs activate on WebSocket client connection. Battery level is reported as a percentage via UART from the power management hardware (observed: `ele = 45` = 45% battery).

### Internal message bus

The `dwarf2` process uses an internal message bus with numeric cmd IDs. The following cmd numbers have been observed from log analysis:

| Cmd | Module | Name | Description |
|-----|--------|------|-------------|
| 10050 | MODULE_CAMERA_TELE | `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` | Set telephoto preview quality |
| 11040 | MODULE_ASTRO | `CMD_ASTRO_GET_QUICK_SET_LIST` | Astro subsystem message |
| 12022 | MODULE_CAMERA_WIDE | `CMD_CAMERA_WIDE_PHOTOGRAPH` | Take photo (wide angle = type 1) |
| 12036 | MODULE_CAMERA_WIDE | `CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY` | Set wide angle preview quality |
| 13010 | MODULE_SYSTEM | `CMD_SYSTEM_SET_LOCATION` | Set device location (fires continuously with GPS data) |
| 16405 | MODULE_TASK_CENTER | `CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO` | Get device state info from task center |

Command names resolved from APK decompilation of `com.convergence.dwarflab` (September 2026). These are internal bus cmd IDs, distinct from the WebSocket interface numbers on port 9900. MODULE_TASK_CENTER covers cmd range 16400-16599; the module name is not the same as the `module_id` field in `WsPacket` — see the WsPacket section below.

### Motor system

The two stepper motors communicate with the main SoC via UART. Motor parameters logged on each movement include speed (degrees/second), frequency (steps/second), pulse count, direction, resolution (microsteps), and ramp. Confirmed motor assignments, verified empirically by observing log output during manual movement:

- Motor 1 — azimuth (spin/left-right rotation)
- Motor 2 — altitude (pitch/up-down tilt)

The `serviceJoystick` function handles joystick input but will reject commands with "INVALID CMD: motor busy!" if a move is already in progress.

---

## Filesystem

| Partition | Mount | Size | Notes |
|-----------|-------|------|-------|
| `/dev/root` | `/` | 440MB | Root filesystem, 73% full |
| `/dev/mmcblk2p1` | `/mnt/sdcard` | 60GB | SD card, user images stored here |
| `/dev/mmcblk0p8` | `/oem` | 2.0GB | DwarfLab application and assets |
| `/dev/mmcblk0p9` | `/userdata` | 3.9GB | User data |

### Notable directories

**`/oem/Astrometry/`** — plate solving data
- `data/index-4110.fits` — star catalogue index, telephoto FOV scale
- `data/index-4111.fits` — star catalogue index, wide FOV scale
- `test_vega.jpeg` — development test image left in shipping firmware

**`/oem/model/`** — NPU models for object tracking
- `siamrpn_backbone_NHWC_288.rknn`
- `siamrpn_rpn.rknn`
- `siamrpn_template_NHWC.rknn`
- `siamrpn_template_NHWC_128.rknn`
- `siamrpn_track.rknn`

These are SiamRPN (Siamese Region Proposal Network) models. The binary also references YOLO v5/v6/v7/v8 support. Inference runs at 50-70 FPS on the NPU via `rknn_inference`.

SiamRPN works by running two parallel neural networks one processes a template of the target object captured when tracking begins, the other processes each new camera frame. The outputs are compared to locate the target and produce a bounding box. The model is split into separate files because the template branch only needs to run once, while the search and RPN branches run on every frame.

**`/oem/etc/iqfiles/`** — ISP image quality tuning files
- `imx415_YT10092_IR0147-28IRC-8M-F20.xml` — full ISP tuning for the Sony IMX415 in normal mode, including noise reduction curves, colour correction matrices, gamma tables, sharpening parameters, white balance coefficients, and exposure control curves
- `binning/imx415_YT10092_IR0147-28IRC-8M-F20.xml` — same tuning for 2x2 binning mode, used during astrophotography

These files represent DwarfLab's proprietary sensor tuning and are not redistributed here, but anyone with SSH access can pull them directly from the device.

**`/oem/usr/bin/`** — Rockchip media test binaries including RTSP streaming tools, dual camera test utilities, and NPU test programs

**`/oem/usr/share/rknn_model/`** — additional NPU models shipped with the firmware
- `ssd_inception_v2_rv1109_rv1126.rknn` — pre-converted SSD Inception V2 object detection model, purpose in the application unknown

**`/oem/wifi/`** — WiFi configuration including hostapd.conf

**`/userdata/cfg/`** — user configuration
- `params_config.json` — current camera parameters
- `default_params_configs.yaml` — full parameter definitions with ranges, shooting modes, and firmware version
- `ble_wifi.conf` — device name, hotspot SSID/password, and connected WiFi credentials stored in plaintext
- `wpa_supplicant.conf` — WiFi connection config
- `zlog.conf` — logging configuration

**`/userdata/dark/`** — dark frame calibration images

**`/userdata/www/`** — nginx web root. Contains a single `index.html` saying "Success". Replace with your own HTML to host a custom web interface that survives reboots. Firmware updates may overwrite this folder, so you would need to re-deploy after updating.

**`/userdata/log/`** — application logs
- `dwarf2.log` — main app log, rotates at 2MB keeping 5 files. Contains connected WiFi SSID and password in plaintext on every boot
- `ble_wifi/ble_wifi.log` — Bluetooth/WiFi setup log

**`/userdata/shooting_schedule/`** — saved shooting schedules

**`/system/model/`** — additional undocumented NPU models
- `model_critic.rknn` — sharpness scoring model. Takes a 224x224 RGB input, outputs a single scalar value (confirmed: sharp image scores ~9.86, blurred image scores ~0). Architecture: 10x ConvolutionReluPoolingLayer2 → PoolingLayer2 → 2x FullyConnectedReluLayer. Used to score and select frames during live stacking.
- `model_autofocus.rknn` — autofocus quality model. Same architecture as model_critic (10x ConvolutionReluPoolingLayer2 → PoolingLayer2 → 2x FullyConnectedReluLayer), different weights. Takes a 224x224 input, outputs 4 values (confirmed: ~179, ~177, ~174, ~12 on a test image, stable across sharp and blurred inputs). Output likely represents focus quality across spatial regions rather than motor position.
- `ufoseg.rknn` — segmentation model. Architecture: ConvolutionReluPoolingLayer2 blocks with two bilinear upsampling layers (resize_bilinear_U8toU8_SAME_2x) and a final ActivationLayer — an encoder-decoder (U-Net style) structure that produces a spatial mask rather than a scalar or vector output. Runs at ~18 FPS vs ~60 FPS for the other two models. Output indices shift between clean and contaminated frames, consistent with satellite trail or moving object detection and masking during stacking.

Input size confirmed as 224x224 for all three via `rknn_inference` testing. Sizes above 256x256 cause a segmentation fault in the test tool.

**`/rockchip_test/`** — Rockchip BSP test scripts for CPU, GPU, NPU, camera, audio, and WiFi. Not used in normal operation but left in the firmware. Includes `rknn_inference` and a VGG16 test model.

### SD card layout

The SD card is mounted at `/mnt/sdcard/`. Images are stored under `/mnt/sdcard/DWARF_II/`.

Each capture is stored twice — once for the telephoto camera (`DWARF_TELE_*`) and once for the wide angle (`DWARF_WIDE_*`) — plus a Thumbnail copy, so effectively three copies of every image.

Deleting images in the DwarfLab app does not reliably remove them from the SD card.

---

## Network

### Open ports

| Port | Protocol | Service | Notes |
|------|----------|---------|-------|
| 21 | TCP | FTP (vsftpd) | Anonymous read access to SD card |
| 22 | TCP | SSH (dropbear) | Root shell, default credentials root/rockchip |
| 53 | TCP/UDP | DNS (dnsmasq) | Active in hotspot mode |
| 67 | UDP | DHCP (dnsmasq) | Active in hotspot mode |
| 80 | TCP | HTTP (nginx) | Web interface and SD card browser |
| 1935 | TCP | RTMP | BSP leftover — not used by DwarfLab app, see below |
| 5037 | TCP | ADB | Localhost only |
| 5555 | TCP | ADB (adbd) | Android Debug Bridge daemon, ADB over TCP, no authentication required |
| 8082 | TCP | HTTP REST API | JSON, POST endpoints, no authentication |
| 8092 | TCP | HTTP media server | Camera streams and time sync — stream format unconfirmed |
| 9900 | TCP/UDP | Control API | WebSocket — confirmed in binary strings |

### ADB access

Port 5555 runs `adbd`, the Android Debug Bridge daemon, confirmed by cross-referencing `/proc/<pid>/cmdline` against the socket inode in `/proc/net/tcp`. No authentication is required. ADB connection is confirmed working via direct testing.

Connect using [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools):

```
adb connect <ip>:5555
adb shell
```

This gives a root shell identical to SSH — no additional packages or capabilities beyond what SSH provides. It is a useful backup access method if the SSH password has been changed. `adb pull` can also be used for bulk file transfer from the SD card, which is faster than FTP for large amounts of data. `adb logcat` gives a live stream of Android/system log output from the device.

### HTTP REST API

Port 8082 serves a JSON REST API from the main `dwarf2` process directly, not a separate service. All endpoints are at `http://DWARF-IP:8082`.

Responses include a `code` field where `0` means success and `-1` indicates missing or invalid parameters.

All confirmed working endpoints require `POST` with `Content-Type: application/json`. An empty JSON body (`{}`) is sufficient for most of them.

> **Security note:** The `/deviceInfo` endpoint returns the connected WiFi password in plaintext to anyone who can reach port 8082. There is no authentication on this port.

#### Confirmed working endpoints

| Endpoint | Returns |
|----------|---------|
| `POST /deviceInfo` | Device name, MAC address, BLE service ID, AP and STA IP addresses, SD card info, WiFi SSID and password in plaintext, current WiFi mode |
| `POST /firmwareVersion` | Major, minor, patch version numbers |
| `POST /getResetState` | Factory default device name and password, and whether the device has been factory reset |
| `POST /shootingMode/getSupportedShootingModes` | Full list of shooting modes with IDs and associated shooting technology IDs |
| `POST /album/list/mediaCounts` | Count of media by type (type IDs: 0–5, exact type names unknown) |
| `POST /album/astro/fitsList` | Empty response — likely requires session parameters |
| `POST /shootingMode/getParamAndSetting` | Current shooting mode parameters and settings |
| `POST /album/list/mediaInfos` | Media file info list |

Shooting mode IDs returned by `/shootingMode/getSupportedShootingModes`:

| ID | Mode |
|----|------|
| 1 | Normal |
| 2 | DSO |
| 3 | Sun/Moon |
| 6 | Auto Tracking |
| 7 | Panorama |
| 8 | Sun |
| 9 | Moon |
| 10 | Planet |

#### Endpoints returning 501 Not Implemented

These may require GET rather than POST, or may be unimplemented in firmware 2.2.18. `/getDefaultParamsConfig` is confirmed as GET and returns a name/version response with empty `cameras` and `featureParams` arrays.

- `GET /getDefaultParamsConfig`
- `/logInfo`
- `/downloadLog`
- `/checkMd5`

### HTTP media server (port 8092)

Port 8092 is an HTTP server serving camera streams and a time-sync endpoint, confirmed from the [dwarfii_api](https://github.com/DwarfTelescopeUsers/dwarfii_api) source. All endpoints are at `http://DWARF-IP:8092`.

| Endpoint | Description |
|----------|-------------|
| `GET /mainstream` | Telephoto camera stream (confirmed working) |
| `GET /secondstream` | Wide angle camera stream (confirmed working) |
| `GET /thirdstream` | Wide angle camera stream (alternate path — returns empty without active app session) |
| `GET /rawstream` | Raw preview stream |
| `GET /date?date=<yyyy-mm-dd hh:mm:ss>` | Set device UTC time |

The telephoto stream (`/mainstream`) is confirmed to serve `multipart/x-mixed-replace` with boundary `dwarf` — standard MJPEG over HTTP. The confirmed working wide angle URL is `/secondstream`. Both streams require an active WebSocket session on port 9900 — see [Live streaming without the app](#live-streaming-without-the-app) for the activation sequence.

### WebSocket control API

> **Source note:** Connection details and command names in this section were obtained by APK decompilation of `com.convergence.dwarflab` (version available on APKPure, September 2026), supplemented by the existing [dwarfii_api](https://github.com/DwarfTelescopeUsers/dwarfii_api) community documentation.

The main control API runs on port 9900 over WebSocket. The full URL format includes a `client_id` query parameter:

```
ws://<device-ip>:9900/?client_id=<uuid>
```

The `client_id` is a random UUID generated once by the app and persisted in MMKV storage under key `data_default_client_id` in the `device` store. For third-party clients, generate any valid UUID (v4 recommended) and reuse it across connections to the same device.

**Master client:** The device automatically assigns master status to the first client that connects based on the `client_id` in the URL. You can also claim it explicitly by sending `CMD_SYSTEM_SET_MASTER` (cmd 13004) after connecting.

**Keep-alive:** Send a `"ping"` text message every 5 seconds; the device responds with `"pong"`. The WebSocket protocol-level ping interval is 40 seconds. Send both.

**Close codes:**
- `4409` — Normal disconnect. The device sends a generation counter used to reject stale reconnects. Reconnect normally.
- `4410` — Device is rejecting a STA-mode IP connection. No reconnect should be attempted.

#### WsPacket protobuf structure

The V2 API (current firmware) uses a protobuf-encoded `WsPacket` for all messages. Full field list from `BaseProto.WsPacket`:

| Field | Name | Type |
|-------|------|------|
| 1 | `major_version` | int |
| 2 | `minor_version` | int |
| 3 | `device_id` | int |
| 4 | `module_id` | int |
| 5 | `cmd` | int |
| 6 | `type` | int |
| 7 | `data` | bytes |
| 8 | `client_id` | string |

The `module_id` field is derived from the `cmd` value using the module ranges listed in the WsCmd section below. The `data` field carries the command-specific protobuf payload.

The `type` field (field 6) indicates message direction: `0` = request, `1` = response, `2` = notification, `3` = reply.

#### V1 API command reference

The following interface numbers are confirmed from the [dwarfii_api](https://github.com/DwarfTelescopeUsers/dwarfii_api) npm package (DwarfTelescopeUsers, 2023). These are V1 API numbers for firmware 2.x. The V2 API used by newer firmware uses the protobuf-based `WsPacket` format described above and may differ. REST endpoints on port 8082 such as `/deviceInfo` and `/firmwareVersion` are separate and not listed here.

Most commands require a `camId` parameter: `0` for telephoto, `1` for wide angle.

| Interface | Name | Description |
|-----------|------|-------------|
| 10000 | `turnOnCameraCmd` | Start camera preview |
| 10001 | `setExposureModeCmd` | Set exposure mode (0=auto, 1=manual) |
| 10003 | `setExposureValueCmd` | Set exposure value |
| 10004 | `setGainModeCmd` | Set gain mode |
| 10005 | `setGainValueCmd` | Set gain value |
| 10006 | `takePhotoCmd` | Take photo (0=single, 1=continuous) |
| 10007 | `startRecordingCmd` | Start video recording |
| 10009 | `stopRecordingCmd` | Stop video recording |
| 10011 | `takeAstroPhotoCmd` | Start RAW astro capture |
| 10014 | `numberRawImagesCmd` | Query number of RAW images taken |
| 10015 | `stopAstroPhotoCmd` | Stop RAW astro capture |
| 10016 | `previewImageQuality` | Set preview image quality |
| 10017 | `turnOffCameraCmd` | Stop camera preview |
| 10018 | `startTimelapseCmd` | Start timelapse |
| 10019 | `stopTimelapseCmd` | Stop timelapse |
| 10020 | `setRAWPreviewCmd` | Switch RAW preview source (0=continuous superimpose, 1=single 15s, 2=single composite) |
| 10022 | `statusWorkingStateTelephotoCmd` | Get telephoto working state |
| 10023 | `numberSuperImposedImages` | Query number of stacked frames |
| 10026 | `takeAstroDarkFramesCmd` | Take dark calibration frames |
| 10027 | `queryShotFieldCmd` | Query shot field |
| 10100 | `startMotionCmd` | Start motor (1=spin, 2=pitch) |
| 10101 | `stopMotionCmd` | Stop motor |
| 10103 | `startPanoCmd` | Start panoramic capture |
| 10106 | `stopPanoCmd` | Stop panoramic capture |
| 10107 | `setSpeedCmd` | Set motor speed |
| 10108 | `setDirectionCmd` | Set motor direction (0=anticlockwise, 1=clockwise) |
| 10109 | `setSubdivideCmd` | Set motor microstep subdivide |
| 10203 | `setIRCmd` | Set IR filter (0=IR cut, 3=IR pass) |
| 10204 | `setBrightnessValueCmd` | Set brightness |
| 10205 | `setContrastValueCmd` | Set contrast |
| 10206 | `setSaturationValueCmd` | Set saturation |
| 10207 | `setHueValueCmd` | Set hue |
| 10208 | `setSharpnessValueCmd` | Set sharpness |
| 10211 | `autofocusCmd` | Autofocus (0=global, 1=area) |
| 10212 | `setWhiteBalanceModeCmd` | Set white balance mode |
| 10213 | `setWhiteBalanceScenceCmd` | Set white balance scene preset |
| 10214 | `setWhiteBalanceColorCmd` | Set white balance colour temperature |
| 10215 | `statusTelephotoCmd` | Get telephoto ISP status |
| 10216 | `statusIRTelephotoCmd` | Get IR status |
| 10217 | `statusWideangleCmd` | Get wide angle ISP status |
| 11004 | `shutDownCmd` | Shut down device |
| 11011 | `dwarfChargingStatusCmd` | Get charging status |
| 11200 | `traceInitCmd` | Initialise tracking |
| 11201 | `startTrackingCmd` | Start object tracking |
| 11202 | `stopTrackingCmd` | Stop object tracking |
| 11203 | `startGotoCmd` | Goto target (RA/Dec or planet index) |
| 11205 | `calibrateGotoCmd` | Calibrate goto (requires lat/lon/date) |
| 11405 | `microsdStatusCmd` | Get MicroSD card status |
| 11407 | `systemStatusCmd` | Get system status |
| 11409 | `microsdAvailableCmd` | Get MicroSD available space |
| 11410 | `dwarfSoftwareVersionCmd` | Get software version |

The API does not appear to respond to status queries without an active app session — further investigation needed.

See [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) and [stevejcl/dwarf_test_apiV2](https://github.com/stevejcl/dwarf_test_apiV2) for community API documentation and Python bindings.

### WsCmd command modules

The `WsCmd` enum from the decompiled APK defines all commands and their module assignments by numeric range. The `module_id` field in `WsPacket` carries the numeric module ID, not the name.

| Cmd range | Module name | module_id value |
|-----------|-------------|-----------------|
| — | `MODULE_NONE` | 0 |
| 10000–10499 | `MODULE_CAMERA_TELE` | 1 |
| 12000–12499 | `MODULE_CAMERA_WIDE` | 2 |
| 11000–11499 | `MODULE_ASTRO` | 3 |
| 13000–13299 | `MODULE_SYSTEM` | 4 |
| 13500–13799 | `MODULE_RGB_POWER` | 5 |
| 14000–14499 | `MODULE_MOTOR` | 6 |
| 14800–14899 | `MODULE_TRACK` | 7 |
| 15000–15199 | `MODULE_FOCUS` | 8 |
| 15200–15499 | `MODULE_NOTIFY` | 9 |
| 15500–15599 | `MODULE_PANORAMA` | 10 |
| 15700–15799 | `MODULE_ITIPS` | 11 |
| — | `MODULE_FACTORY_TEST` | 12 |
| 16100–16399 | `MODULE_SHOOTING_SCHEDULE` | 13 |
| 16400–16599 | `MODULE_TASK_CENTER` | 14 |
| 16700–16799 | `MODULE_PARAM` | 15 |
| 16800–16899 | `MODULE_VOICE_ASSISTANT` | 16 |
| 16900–16999 | `MODULE_CAMERA_GUIDE` | 17 |
| 17000–17099 | `MODULE_DEVICE` | 18 |

Named commands from the decompile, including those required for stream activation:

| Cmd | Name |
|-----|------|
| 10039 | `CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE` |
| 10042 | `CMD_CAMERA_TELE_SET_RTSP_BITRATE_TYPE` |
| 10050 | `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` |
| 12003 | `CMD_CAMERA_WIDE_GET_EXP_MODE` |
| 12032 | `CMD_CAMERA_WIDE_SET_RTSP_BITRATE_TYPE` |
| 12036 | `CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY` |
| 13004 | `CMD_SYSTEM_SET_MASTER` |
| 13010 | `CMD_SYSTEM_SET_LOCATION` |
| 15234 | `CMD_NOTIFY_STREAM_TYPE` |
| 16404 | `CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA` |
| 16405 | `CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO` |

`CMD_NOTIFY_STREAM_TYPE` (15234) carries a `StreamType` protobuf with field 1 `stream_type` (int) and field 2 `cam_id` (int, 0=telephoto, 1=wide angle). The device sends this to notify the app when the active stream format changes. See stream type values in the RTMP/stream types section below.

### HTTP API routes

The following routes were identified from strings in `/usr/bin/dwarf2`:

- `/api/main/status`
- `/shootingMode/getSupportedShootingModes`
- Album management routes
- Firmware version route
- Device info and reset routes
- Log download route
- File MD5 check route
- Parameter config route

### SD card HTTP access

The SD card is browsable over HTTP without authentication:

```
http://192.168.X.X/sdcard/
```

This includes all captured images and a SQLite database at `/sdcard/DWARF_II/data/device.db`. The database contains:

- File paths and thumbnails for all captures
- Target name, RA and Dec for astro sessions
- GPS coordinates (latitude and longitude) for every imaging session
- Exposure settings, gain, temperature, and MD5 hashes of FITS files

Note: `device.db` displays a timestamp of 01-Jan-2038 due to a Unix timestamp overflow bug in the firmware.

### RTMP (dead end)

RTMP on port 1935 is a dead end. APK decompilation of `com.convergence.dwarflab` confirms the app has no RTMP stream type — only RTSP (1) and JPEG/MJPEG (2), defined in `StreamTypeAnn`. The RTMP server process visible on port 1935 is almost certainly a Rockchip BSP leftover that the DwarfLab application never activates. Use the MJPEG stream on port 8092 instead.

### Stream types

The app's `StreamTypeAnn` enum defines the stream types the device can operate in:

| Value | Name | Description |
|-------|------|-------------|
| 0 | `NONE` | No active stream |
| 1 | `RTSP` | RTSP stream |
| 2 | `JPEG` | MJPEG over HTTP |

The device notifies the app of stream type changes via `CMD_NOTIFY_STREAM_TYPE` (15234), carrying a `StreamType` protobuf with `stream_type` (int, field 1) and `cam_id` (int, field 2; 0=telephoto, 1=wide angle). The confirmed MJPEG stream on port 8092 corresponds to stream type 2 (`JPEG`).

### NPU inference

The NPU is directly accessible from the command line over SSH:

```
/rockchip_test/npu/rknn_inference <model.rknn> <image.jpg> <count>
```

Benchmarked at 14-16ms per inference (62-71 FPS) without I/O, and 19-21ms (47-52 FPS) with I/O, using the built-in SiamRPN backbone model on a 288x288 JPEG. Any model converted to RKNN format can be run this way. Potential use cases include bird species classification, custom object detection, or astronomical object recognition running entirely on the device.

Rockchip maintain an official model zoo at [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) with pre-converted RKNN models for object detection, image classification, pose estimation, OCR, and more. These can be dropped onto the telescope and run directly without any conversion step.

---

## Default credentials

The Dwarf II ships with the same default credentials on every unit, which is what makes it so easy to access and extend. The main thing to be aware of is that you should not connect it to public WiFi in STA mode (hotel networks, coffee shop WiFi etc.), since other devices on that network could access the telescope. Using the telescope's own hotspot is fine since you control the password.

**Default WiFi hotspot SSID:** `DWARF_<last 6 of MAC>` (unique per device)

**Default WiFi hotspot password:** `DWARF_12345678` (same on every unit)

**Default SSH credentials:** `root` / `rockchip` (same on every unit)

**FTP:** anonymous login, no password required

The hotspot password can be changed in the app under Settings > Device Password, which also updates the Bluetooth password. The SSH root password can be changed with `passwd` over SSH. Neither is required for normal use on a home network.

One thing worth knowing: the connected WiFi password is logged in plaintext to `/userdata/log/dwarf2.log` and stored in `/userdata/cfg/ble_wifi.conf`. Both are accessible over FTP. This is only relevant if you connect the telescope to your home network in STA mode and someone else can reach it on that network.

> **Privacy note:** Every photo taken by the Dwarf II has GPS coordinates written into the EXIF data automatically, accurate to approximately street level. This applies to all photo types including normal photos, astro captures, and thumbnails. The coordinates are stored in the SQLite database at `/sdcard/DWARF_II/data/device.db` and are also accessible via FTP and HTTP without authentication.

---

## Contributing

This is a community effort. PRs and issues are welcome. If you find something not documented here, please open an issue or PR.

---

## Related projects

- [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) — community GitHub organisation
- [stevejcl/dwarf_test_apiV2](https://github.com/stevejcl/dwarf_test_apiV2) — Python test program for API V2
- [DwarfTelescopeUsers/dwarfii_api](https://github.com/DwarfTelescopeUsers/dwarfii_api) — JavaScript API wrapper library (V1)
- [stevejcl/dwarfium](https://github.com/stevejcl/dwarfium) — Stellarium integration
- [grosseruser/dwarf2-html](https://github.com/grosseruser/dwarf2-html) — web frontend for the Dwarf II
- [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) — pre-converted RKNN models ready to run on the NPU
- [API V2 documentation](https://tinyphoton.feishu.cn/docx/GBkcdldTIo3SrdxFJDscYVYDnvf) — official DwarfLab WebSocket API docs
