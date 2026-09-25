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
An RTMP server is running on port 1935. Try `rtmp://192.168.X.X/live` in VLC (Media > Open Network Stream) or as a media source in OBS. This has not been fully confirmed to work outside the official app — see the Network section for details.

**Access the SD card over FTP**
Connect to `ftp://192.168.X.X` with anonymous login, no password needed. This gives you full read access to the SD card, including all your captured images and session data.

**Pull session metadata and location data**
The app keeps a SQLite database at `/sdcard/DWARF_II/data/device.db` which is accessible via HTTP or FTP without any credentials. It contains target names, RA/Dec coordinates, GPS location, exposure settings, and file hashes for every session. Useful for building your own logging or cataloguing tools.

**Get a root shell**
SSH is open on port 22. The default credentials are `root` / `rockchip`. This gives you a full Linux shell on the Rockchip RV1126 SoC running the telescope. See the sections below for what you can do with it.

**Run custom AI models on the NPU**
The Rockchip NPU is directly accessible via the `rknn_inference` command line tool over SSH. Any model converted to RKNN format can be run at 50-70 FPS on the device itself, without any external compute. Potential uses include bird species classification, custom object detection, or astronomical object recognition. Rockchip maintain an official model zoo at [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) with pre-converted models ready to run.

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
| 1935 | TCP | RTMP | Live video — unconfirmed, see below |
| 5037 | TCP | ADB | Localhost only |
| 5555 | TCP | Control API | WebSocket, protobuf |
| 8082 | TCP | Unknown | HTTP, returns 404 on root |
| 8092 | TCP | Unknown | Likely WebSocket |
| 9900 | TCP/UDP | Control API | WebSocket — confirmed in binary strings |

### WebSocket control API

The main control API runs on port 9900 over WebSocket with binary protobuf encoding:

```
ws://192.168.X.X:9900
```

Messages use a `WsPacket` wrapper with `cmd` and `data` fields. A keep-alive is required: send both a WebSocket ping frame and a `"ping"` text message; the device responds with `"pong"`.

See [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) and [stevejcl/dwarf_python_api](https://github.com/stevejcl/dwarf_python_api) for community API documentation and Python bindings.

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

### RTMP stream (unconfirmed)

An RTMP server is running on port 1935. The application name is `live`:

```
rtmp://192.168.X.X/live
```

Attempts to connect via VLC and other tools have been unsuccessful outside of the official app. The stream may only be active when the DwarfLab app is connected. If it does work, it can be pulled into OBS for live streaming or used as a wildlife/birdwatching webcam without the app. Further investigation needed.

### Video stream endpoints (unconfirmed)

The binary references `GET /mainstream` and `GET /secondstream`, likely the telephoto and wide angle camera streams respectively. The binary uses `libliveMedia` (LIVE555) and references `sendCamTeleStream` and `sendCamWideStream`, suggesting RTSP is involved. Attempts to access these over HTTP and RTSP on all known ports have been unsuccessful. Further investigation needed.

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

---

## Contributing

This is a community effort. PRs and issues are welcome. If you find something not documented here, please open an issue or PR.

---

## Related projects

- [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) — community GitHub organisation
- [stevejcl/dwarf_python_api](https://github.com/stevejcl/dwarf_python_api) — Python API library
- [stevejcl/dwarfium](https://github.com/stevejcl/dwarfium) — Stellarium integration
- [grosseruser/dwarf2-html](https://github.com/grosseruser/dwarf2-html) — web frontend for the Dwarf II
- [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) — pre-converted RKNN models ready to run on the NPU
- [API V2 documentation](https://tinyphoton.feishu.cn/docx/GBkcdldTIo3SrdxFJDscYVYDnvf) — official DwarfLab WebSocket API docs
