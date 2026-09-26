# Dwarf II Software Internals

 Documentation of the DwarfLab Dwarf II smart telescope internals, gathered via SSH and network analysis. The goal is to give developers building third-party tools a clear picture of what is running on the device and how to talk to it.

This page was written with the assistance of anthropic's Claude sonnet 4.6 model however I manually reviewed it , as you can see by the edit history 

Last updated: September 26th 2026

> **Note:** The Dwarf II ships with default credentials and an open network interface that makes it easy to access and extend. However this is also a security vulnerability. See the [Default Credentials](#default-credentials) section and the below dropdown for details.

<details>
<summary>⚠️ IMPORTANT — Plain English Security Information — please read before use</summary>

## How secure is the Dwarf II?

### Assume anyone within about 50 metres of you has the same level of access to your telescope as you do. That is roughly the security situation with the default settings.
### It is also worth knowing that the level of access available to anyone on the same network could, in theory, be used to remotely and permanently damage the device beyond repair ,not something the researcher has done or recommends in any way, but a real potential consequence of leaving the default settings unchanged.

The telescope creates its own WiFi network with a password that is identical on every Dwarf II ever sold. If someone nearby knows that password , and it was publicly available online even before I made this repository, they can connect to your telescope without you knowing. Once connected they can see everything on the SD card, take control of the motors and camera, and in some configurations retrieve the password to every WiFi network it has been connected to since it was last factory reset.

If you plug it into your home network instead of using its own hotspot, anyone else already on that network has the same access. This includes family members, housemates, and any guests you have given your WiFi password to.

The built-in remote access tools use the same login details on every unit worldwide. There is no notification or log entry that would tell you if someone else had connected, however this repository contains information that could assist in the creation of such a notification tool.

**What you should do:**

- Open the DwarfLab app, go to Me > My Device > Device Password, and change the device password to something longer than 8 letters and/or numbers before you use it anywhere outside your home
- Do not connect it to public WiFi, hotel WiFi, or any shared network.
- If you take it to a star party or any public event, assume the default password is known to other people there and change it first.
- If you do connect it to your home network, be aware that this is less secure than using its own hotspot

</details>

<details>
<summary>Legal notices</summary>

For the purposes of this document, "the researcher" , "the author" and similar terms refer to Z.A. Whyman / J.A. Whyman (ORCID: [0009-0004-1895-0968](https://orcid.org/0009-0004-1895-0968)).

### Jurisdiction and applicable law

This research was conducted in England and Wales and is governed by English law.

### Interoperability research

This repository contains original interoperability research conducted under Section 50B of the Copyright, Designs and Patents Act 1988 (CDPA), which permits decompilation of a computer program for the purpose of obtaining information necessary to create an independent program capable of interoperability with it. Any contract terms that try to ban or restrict permitted decompilation are void under Section 296A of the Act. The decompilation was limited to obtaining interface information and did not exceed what was necessary for that purpose. The information obtained has not been used for any purpose other than the creation and facilitation of the creation of interoperable software, and has not been supplied to any third party except as permitted under Section 50B(3). This research is also consistent with Article 6 of EU Directive 2009/24/EC on the legal protection of computer programs and its UK retained equivalent.

### Ownership and authorisation

All research was conducted on a device lawfully acquired and owned by the researcher. Network interface analysis was conducted exclusively on a private network and device under the researcher's own control or one that the author is lawfully authorised to use. No third-party devices, networks, or accounts were unlawfully accessed at any time. No circumvention of access controls was required or performed. All interfaces documented here are accessible using the device's default factory configuration as shipped by the manufacturer or when settings are changed in the app.

### Permitted acts

Section 50A CDPA permits the making of back-up copies of lawfully obtained software. Section 296ZE CDPA preserves permitted acts in relation to technical measures and prevents copyright owners from using technological protection measures to prevent lawful acts including those permitted under Section 50B. This research falls within these permitted acts.

### Use of AI assistance

This research was conducted with the assistance of Claude (Sonnet 4.6), a large language model developed by Anthropic. Claude assisted with interpretation of decompiled code, protocol analysis, Python scripting, and drafting of this documentation. All findings were verified by the researcher through direct empirical testing on the device. The researcher takes full responsibility for the accuracy of the content.

The use of AI assistance in research and documentation does not, in the researcher's view, affect the legal status of this work. The interoperability permissions under Section 50B CDPA attach to the person lawfully entitled to use the program, not to the tools used in the analysis. The researcher is that person and directed the analysis throughout. Output generated with AI assistance is not currently afforded copyright protection in the UK under the Intellectual Property Office's current guidance, meaning the documentation in this repository is either owned by the researcher as author of the overall work or exists without copyright protection — in either case it is freely available for use. Anthropic's terms of service permit use of Claude for research and documentation tasks of this nature.

### No proprietary assets redistributed

No proprietary source code, compiled binaries, firmware images, or other copyrighted assets belonging to DwarfLab, Tinyphoton Ltd, Rockchip, or any other party other than the author are reproduced or redistributed in this repository. Command numbers, field names, and protobuf schema information derived from decompilation are reproduced only to the extent necessary to document communication interfaces for interoperability purposes.

### Database rights

Star catalogue index files present on the Dwarf 2 device and mobile application (index-4110.fits, index-4111.fits) may be protected as databases under the Copyright and Rights in Databases Regulations 1997. These files are not reproduced or redistributed in this repository. Their existence, location, and purpose are documented for interoperability purposes only.

### Moral rights

The firmware build strings embedded in the shipped firmware incidentally reveal the names of individuals involved in its compilation. These names are reproduced in this repository only as factual technical information necessary for accurate documentation of the firmware's provenance. No identification claim is made against those individuals under Section 77 CDPA, and no derogatory treatment of their work is intended or implied under Section 80 CDPA.

### Trade secrets

The information documented in this repository was obtained through lawful and non-destructive, computational and physical interface with a device owned by the researcher and through decompilation permitted under Section 50B CDPA. No information was obtained through any breach of confidence, misappropriation, or any act that would constitute unlawful acquisition under the Trade Secrets (Enforcement, etc.) Regulations 2018. The researcher did not have access to any information belonging to DwarfLab, Tinyphoton Ltd or any associated entity beyond what was discoverable through lawful analysis of the shipped product, the software contained within it, its associated Android mobile phone application, and information already lawfully public on the internet as of *26th September 2026*.

### Intellectual property exhaustion

Under the doctrine of exhaustion of intellectual property rights, DwarfLab's and Tinyphoton Ltd's intellectual property rights in the software installed on the device are exhausted with respect to the researcher's lawful use of that copy following its sale. The SSH access, network analysis, and runtime observation documented here constitute use of a lawfully purchased copy and do not infringe any intellectual property right that has not been exhausted by the first sale.

### Security disclosures

This documentation does not constitute a formal security advisory. Vulnerabilities and security-relevant behaviours noted in this repository (including but not limited to: SSH root access with default credentials common to all units, plaintext storage and logging of WiFi credentials, unauthenticated REST API access, and FTP anonymous read access to the SD card) are described accurately as behaviours present in the device's default shipped configuration. These behaviours were not introduced by this research. The researcher did not exploit these vulnerabilities against any third party.

## The author recommends that DwarfLab review the security posture of the device's default network configuration. The specific remediation approach is left to DwarfLab's discretion, however the author suggests that a developer mode or per-interface toggle behind an appropriate warning screen in the phone app would strike a reasonable balance between improving security for general consumers without removing the legitimate ability of technically capable owners to access their own devices. The Dwarf II is an excellent hardware platform and the author believes a thriving open source third-party software ecosystem would be of significant benefit to both the community and to DwarfLab . The author respectfully requests that any security measures taken do not prevent the creation of third-party interface and control software, and remain consistent with owners' rights under Section 50B CDPA and the right to repair principles outlined above.

### Public interest

The security findings documented in this repository are published in the public interest. Purchasers of the Dwarf II have a legitimate interest in understanding the security posture of a networked device operating on their home network and connecting to their personal devices. Publication of accurate factual information about a matter of public interest is a defence to any claim in defamation under Section 4 of the Defamation Act 2013. The researcher believes all statements of fact in this repository to be true and has taken reasonable care to verify them.

### Acknowledgement request

If DwarfLab or Tinyphoton Ltd address any of the security issues documented in this repository in a future firmware release, the researcher requests acknowledgement in the relevant release notes or security advisory as the original documenting researcher. Contact: Z.A. Whyman, ORCID [0009-0004-1895-0968](https://orcid.org/0009-0004-1895-0968). 

### Unjust enrichment

The researcher reserves the right to seek acknowledgement for any findings, methodologies, or documented interfaces from this repository that are incorporated into official DwarfLab or Tinyphoton Ltd products, documentation, or firmware releases. Incorporation of this research into a commercial product without acknowledgement may give rise to a claim in unjust enrichment under the English common law doctrine of unjust enrichment, as developed in *Lipkin Gorman v Karpnale Ltd* [1991] 2 AC 548 and *Benedetti v Sawiris* [2013] UKSC 50.
*(In plain English: British law says that if DwarfLab or anyone associated with them benefits from this research, they are supposed to credit me.)*

### Public interest and responsible disclosure

This research serves a public interest function consistent with the principles of responsible disclosure recognised by the UK National Cyber Security Centre (NCSC) and the Information Commissioner's Office (ICO). The vulnerabilities documented here were not exploited against any third party. The researcher has not been contacted by DwarfLab or Tinyphoton Ltd regarding these findings prior to publication. Publication is in the public interest as it enables purchasers of the Dwarf II to make informed decisions about the security posture of a networked device operating on their home network.

### Cyber Resilience Act

The security issues documented in this repository — including default credentials common to all units, plaintext storage and logging of WiFi credentials, and unauthenticated network APIs — are directly relevant to manufacturers' obligations under the EU Cyber Resilience Act (Regulation (EU) 2024/2847), which imposes security requirements on manufacturers of products with digital elements placed on the EU market. The researcher believes publication of these findings serves the accountability purposes of the CRA and any equivalent UK legislation. Nothing in this repository constitutes legal advice regarding DwarfLab's or Tinyphoton Ltd's compliance obligations.

### Right to repair

This research is consistent with the principles underlying the EU Right to Repair Directive (Directive (EU) 2024/1799) and emerging UK right to repair policy, which support the right of owners to access, understand, and maintain the devices they have purchased. Documenting the software interfaces of a lawfully owned device for the purpose of building interoperable tools and maintaining independent access to its functions is precisely the kind of activity these frameworks are designed to protect.

### Disclaimer

This repository is provided for educational and interoperability purposes only. The researcher accepts no liability for any damage, data loss, or other consequences arising from use of the information contained herein. Use of this information to access devices you do not own or have permission to access may constitute an offence under the Computer Misuse Act 1990.

# (In plain English: what I did here is not only legal but actively encouraged under UK and EU law.)

</details>



## What can I do with this?

You do not need to be an embedded linux developer to get something useful out of this. Here are some things anyone could do with a Dwarf II beyond the official app:

**Browse and download your photos without the app**
Open a web browser on any device connected to the same network as your telescope and go to `http://192.168.X.X/sdcard/` (replace with your telescope's IP). You will see all your captured images and can download them directly.

**Use it as a PTZ camera or wildlife cam**
The Dwarf II has pan/tilt motors and a decent sensor. You can point it at a bird feeder, a garden, or anything else and control it remotely from your phone via the DwarfLab app. No astronomy required.

**Host a custom web interface**
nginx is already running and serving files from `/userdata/www/`. The default page at `http://192.168.X.X/` just says "Success". You can replace `index.html` with your own HTML/JS app and get a persistent browser-based controller accessible from any device on the network, no app install required. Changes survive reboots since `/userdata` is on persistent storage. Firmware updates may overwrite this folder, so you would need to re-deploy after updating. (alternatively and more easily , you can put it on the root directory of the SD card and open it in a browser)

**Stream the live view to OBS or VLC** Both cameras can in theory be streamed live to any MJPEG-capable player without the official app. See the "Live streaming without the app" section for more info. The stream in theory works in VLC (Media > Open Network Stream), OBS (Browser source or Media source), ffplay, and any HTTP client that can handle multipart JPEG.

**Access the SD card over FTP**
Connect to `ftp://192.168.X.X` with anonymous login, no password needed. This gives you full read access to the SD card, including all your captured images and session data.

**Pull session metadata and location data**
The app keeps a SQLite database at `/sdcard/DWARF_II/data/device.db` which is accessible via HTTP or FTP without any credentials. It contains target names, RA/Dec coordinates, GPS location, exposure settings, and file hashes for every session. Useful for building your own logging or cataloguing tools.

**Get a root shell**
SSH is open on port 22. The default credentials are `root` / `rockchip`. This gives you a full Linux shell on the Rockchip RV1126 SoC running the telescope. See the sections below for what you can do with it.

**Run custom AI models on the NPU**
The Rockchip NPU is directly accessible via the `rknn_inference` command line tool over SSH. Any model converted to RKNN format can be run at 50-70 FPS on the device itself, without any external compute. Potential uses include bird species classification, custom object detection, or astronomical object recognition. Rockchip maintain an official model zoo at [airockchip/rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) with pre-converted models ready to run.

---

---

## Live streaming without the app

Both cameras can be streamed live without the official app. The stream requires an active WebSocket V2 session — if the session closes, the stream stops within about 60 seconds.

Stream URLs (MJPEG):
- Telephoto: `http://<device-ip>:8092/mainstream`
- Wide angle: `http://<device-ip>:8092/secondstream`

These work in VLC, ffplay, OBS, or any MJPEG-capable player.

The required WebSocket command sequence to activate the stream:

1. Connect to `ws://<device-ip>:9900/?client_id=<any-uuid>`
2. Send `CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA` (cmd 16404, module 14) with payload `ReqEnterCamera { client_param: ClientParams { encode_type: 1 } }`
3. Send `CMD_CAMERA_TELE_SET_RTSP_BITRATE_TYPE` (cmd 10042, module 1) with payload `{ bitrate_type: 1 }` for telephoto, or `CMD_CAMERA_WIDE_SET_RTSP_BITRATE_TYPE` (cmd 12032, module 2) for wide
4. Send `CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE` (cmd 10039, module 1) for telephoto, or `CMD_CAMERA_WIDE_GET_EXP_MODE` (cmd 12003, module 2) for wide
5. Send `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` (cmd 10050, module 1) with payload `{ level: 1 }` for telephoto, or `CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY` (cmd 12036, module 2) for wide
6. Keep the WebSocket session alive with a `"ping"` text message every 5 seconds
7. Connect to `http://<device-ip>:8092/mainstream` or `/secondstream`

A ready-to-run Python script `dwarf_stream.py` in this repo handles the full sequence and opens the stream automatically. It requires `pip install websocket-client` and ffmpeg installed on the host machine.

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
| Sensor | Sony IMX415 Starvis — 8MP telephoto, Sunplus SPCA2281 - 2MP wide |
| Lens module | YT10092 with IR0147-28IRC lens, F2.0 aperture |

---

## Software

**OS:** Linux 4.19.111, kernel built 2023-02-02, `armv7l`

**Build info:** The kernel version string reveals the firmware was compiled by a user named `hfx` on a machine called `hfx-RESCUER-R720-15IKBN`, which is a Lenovo Rescuer R720 gaming laptop. Strings in the main application binary reference `/home/liangxin/data_ex/dwarf2/DWARF2_V2/`, suggesting the app was built on a separate machine belonging to a developer named Liangxin. 

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

The `dwarf2` process uses an internal message bus with numeric cmd IDs. These correspond directly to the WebSocket V2 API cmd numbers on port 9900 (see the "WebSocket V2 API (protobuf)" section below). The following cmd numbers have been observed from log analysis and confirmed via APK decompilation:

| Cmd | Name | Module |
|-----|------|--------|
| 10050 | CMD_CAMERA_TELE_SET_PREVIEW_QUALITY | MODULE_CAMERA_TELE |
| 11040 | CMD_ASTRO_GET_QUICK_SET_LIST | MODULE_ASTRO |
| 12022 | CMD_CAMERA_WIDE_PHOTOGRAPH | MODULE_CAMERA_WIDE |
| 12036 | CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY | MODULE_CAMERA_WIDE |
| 13010 | CMD_SYSTEM_SET_LOCATION | MODULE_SYSTEM |
| 16405 | CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO | MODULE_TASK_CENTER |

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
| 1935 | TCP | RTMP | Rockchip BSP leftover — not used by the DwarfLab app, see below |
| 5037 | TCP | ADB | Localhost only |
| 5555 | TCP | ADB (adbd) | Android Debug Bridge daemon, ADB over TCP, no authentication required |
| 8082 | TCP | HTTP REST API | JSON, POST endpoints, no authentication |
| 8092 | TCP | HTTP media server | MJPEG camera streams — confirmed working, see "Live streaming without the app" |
| 9900 | TCP/UDP | Control API | WebSocket — confirmed in binary strings |

### ADB access

Port 5555 runs `adbd`, the Android Debug Bridge daemon, confirmed by cross-referencing `/proc/<pid>/cmdline` against the socket inode in `/proc/net/tcp`. No authentication is required.

Connect using [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools):

```
adb connect <ip>:5555
adb shell
```

This gives a root shell without needing SSH credentials, and is an alternative access path if the SSH password has been changed. `adb pull` can also be used for bulk file transfer from the SD card, which is faster than FTP for large amounts of data.

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

Port 8092 is an HTTP server serving MJPEG camera streams and a time-sync endpoint. All endpoints are at `http://DWARF-IP:8092`.

The MJPEG stream endpoints are confirmed working:
- `GET /mainstream` — telephoto camera (480x270, 30fps)
- `GET /secondstream` — wide angle camera

These are served on port 8092, not RTSP. The server sends a multipart MJPEG response with boundary `--dwarf`. The stream is activated by the WebSocket command sequence documented in the "Live streaming without the app" section. The device uses `libliveMedia` (LIVE555) internally but the stream is delivered over HTTP, not RTSP.

Additional endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /rawstream` | Raw preview stream |
| `GET /date?date=<yyyy-mm-dd hh:mm:ss>` | Set device UTC time |

### WebSocket control API

The main control API runs on port 9900 over WebSocket with JSON messages:

```
ws://192.168.X.X:9900
```

Messages use an `interface` field (not `cmd`) to identify the command, followed by any parameters for that command:

```json
{"interface": 11203, "ra": 83.82, "dec": -5.39}
```

The device requires an active WebSocket client session before it will respond to commands. The first client to connect is designated the `master client` and assigned a UUID client_id. Third-party clients must complete the WebSocket handshake and send an immediate `"ping"` text message to establish the session. The keep-alive ping must be sent every 5 seconds or the connection is dropped; the device responds with `"pong"`. Send both a WebSocket ping frame and the `"ping"` text message.

#### WebSocket V2 API (protobuf)

The V2 API used by current firmware uses binary protobuf encoding, not JSON. All commands from the official app use this format.

URL format:
```
ws://<device-ip>:9900/?client_id=<uuid>
```

The client_id is any UUID you generate. Generate it once and reuse it across connections. The device automatically assigns master status to the first client that connects.

Keep-alive: send the text message `"ping"` every 5 seconds. The device responds with `"pong"`. Also send a WebSocket protocol ping every 40 seconds.

Close codes: 4409 = normal disconnect, the device sends a generation counter used to reject stale reconnects. 4410 = device rejecting a STA-mode IP connection, do not reconnect.

**WsPacket protobuf structure** (from APK decompilation of com.convergence.dwarflab, September 2026):

| Field | Number | Type | Description |
|-------|--------|------|-------------|
| major_version | 1 | int | Set to 1 |
| minor_version | 2 | int | Set to 8 |
| device_id | 3 | int | Set to 1 |
| module_id | 4 | int | Numeric module ID (see table below) |
| cmd | 5 | int | Command number |
| type | 6 | int | 0=request, 1=response, 2=notification, 3=reply |
| data | 7 | bytes | Protobuf-encoded command payload |
| client_id | 8 | string | Your UUID |

**Module ID values:**

| Value | Module |
|-------|--------|
| 0 | MODULE_NONE |
| 1 | MODULE_CAMERA_TELE |
| 2 | MODULE_CAMERA_WIDE |
| 3 | MODULE_ASTRO |
| 4 | MODULE_SYSTEM |
| 5 | MODULE_RGB_POWER |
| 6 | MODULE_MOTOR |
| 7 | MODULE_TRACK |
| 8 | MODULE_FOCUS |
| 9 | MODULE_NOTIFY |
| 10 | MODULE_PANORAMA |
| 11 | MODULE_ITIPS |
| 12 | MODULE_FACTORY_TEST |
| 13 | MODULE_SHOOTING_SCHEDULE |
| 14 | MODULE_TASK_CENTER |
| 15 | MODULE_PARAM |
| 16 | MODULE_VOICE_ASSISTANT |
| 17 | MODULE_CAMERA_GUIDE |
| 18 | MODULE_DEVICE |

**Command ranges by module:**

| Range | Module |
|-------|--------|
| 10000-10499 | MODULE_CAMERA_TELE |
| 11000-11499 | MODULE_ASTRO |
| 12000-12499 | MODULE_CAMERA_WIDE |
| 13000-13299 | MODULE_SYSTEM |
| 13500-13799 | MODULE_RGB_POWER |
| 14000-14499 | MODULE_MOTOR |
| 14800-14899 | MODULE_TRACK |
| 15000-15199 | MODULE_FOCUS |
| 15200-15499 | MODULE_NOTIFY |
| 15500-15599 | MODULE_PANORAMA |
| 15700-15799 | MODULE_ITIPS |
| 16100-16399 | MODULE_SHOOTING_SCHEDULE |
| 16400-16599 | MODULE_TASK_CENTER |
| 16700-16799 | MODULE_PARAM |
| 16800-16899 | MODULE_VOICE_ASSISTANT |
| 16900-16999 | MODULE_CAMERA_GUIDE |
| 17000-17099 | MODULE_DEVICE |

**Previously observed cmd numbers now identified:**
- 10050 = CMD_CAMERA_TELE_SET_PREVIEW_QUALITY
- 11040 = CMD_ASTRO_GET_QUICK_SET_LIST
- 12022 = CMD_CAMERA_WIDE_PHOTOGRAPH
- 12036 = CMD_CAMERA_WIDE_SET_PREVIEW_QUALITY
- 13010 = CMD_SYSTEM_SET_LOCATION
- 16405 = CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO

#### V1 API command reference

The following interface numbers are confirmed from the [dwarfii_api](https://github.com/DwarfTelescopeUsers/dwarfii_api) npm package (DwarfTelescopeUsers, 2023). These are V1 API numbers for firmware 2.x. The V2 API used by newer firmware uses a different protobuf-based `WsPacket` format as documented above. REST endpoints on port 8082 such as `/deviceInfo` and `/firmwareVersion` are separate and not listed here.

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

### RTMP stream

RTMP on port 1935 is a dead end. APK decompilation of com.convergence.dwarflab confirms the app has no RTMP stream type — it only knows about RTSP (type 1) and JPEG/MJPEG (type 2), defined in `StreamTypeAnn`. The RTMP server on port 1935 is a Rockchip BSP leftover that the DwarfLab application never activates. Use the MJPEG stream on port 8092 instead, as documented in the "Live streaming without the app" section.

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

## Changelog

| Date | Firmware | Changes |
|------|----------|---------|
| 16 September 2026 | 2.2.18 | Initial session — SSH access, hardware identification, filesystem layout, open ports, WebSocket protocol noted, README created |
| 22 September 2026 | 2.2.18 | Shell access confirmed, RV1126 SoC verified, embedded Linux environment documented |
| 26 September 2026 | 2.2.18 | Port 8092 confirmed MJPEG, port 5555 confirmed ADB, NPU models characterised, motor axes confirmed, wide camera hardware ID, GPS EXIF confirmed, REST API on 8082 documented |
| 26 September 2026 | 2.2.18 | APK decompilation — full WebSocket V2 protobuf protocol, complete command table, module ID mapping, MJPEG stream activation confirmed for both cameras, RTMP confirmed dead end, security analysis added |
