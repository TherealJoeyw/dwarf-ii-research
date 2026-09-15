# Dwarf II Software Internals

Community documentation of the DwarfLab Dwarf II smart telescope software internals, gathered via SSH and network analysis. This repo aims to document the hardware, software, and network interface for developers building third-party tools.

> **Security notice:** The Dwarf II ships with default SSH credentials and a default WiFi hotspot password. Do not connect your telescope to public or untrusted networks. See the Security section below.

---

## Hardware

**SOC:** Rockchip RV1126 (identified from hostname `RV1126_RV1109` visible on the network)

- CPU: Quad-core ARM Cortex-A7 @ 1.5GHz + RISC-V MCU @ 400MHz
- NPU: 2.0 TOPS, supports INT8/INT16
- GPU: 2D graphics engine + Rockchip RGA (image scaling/rotation accelerator)
- VPU: 4K H.264/H.265 encode and decode
- RAM: ~1.8GB (1865740 kB total)
- Sensor: Sony IMX415 Starvis (8MP telephoto, 2MP wide)

---

## Software

**OS:** Linux 4.19.111 (kernel built 2023-02-02, `armv7l`)

**Build info:** Source paths in the binary reference `/home/liangxin/data_ex/dwarf2/DWARF2_V2/`, indicating the firmware was built on a developer machine belonging to someone named Liangxin.

**Key processes running:**
- `/usr/bin/dwarf2` — main application (Tinyphoton/DwarfLab app)
- `rknn_server` — Rockchip NPU inference server
- `nginx` — HTTP server
- `dropbear` — lightweight SSH server
- `wpa_supplicant` — WiFi management
- `hostapd` — WiFi hotspot
- `dnsmasq` — DNS/DHCP for hotspot mode
- `vsftpd` — FTP server
- `avahi-daemon` — mDNS/Bonjour
- `bsa_server` — Bluetooth stack

---

## Filesystem Layout

| Partition | Mount | Size | Notes |
|-----------|-------|------|-------|
| `/dev/root` | `/` | 440MB | Root filesystem, 73% full |
| `/dev/mmcblk2p1` | `/mnt/sdcard` | XGB | SD card — user images stored here |
| `/dev/mmcblk0p8` | `/oem` | 2.0GB | DwarfLab application and assets |
| `/dev/mmcblk0p9` | `/userdata` | 3.9GB | User data partition |

### Key directories

`/oem/Astrometry/` — Astrometry.net plate solving data
- `data/index-4110.fits` — star catalogue index (telephoto FOV scale)
- `data/index-4111.fits` — star catalogue index (wide FOV scale)
- `test_vega.jpeg` — test image used during development

`/oem/model/` — NPU AI models
- `siamrpn_backbone_NHWC_288.rknn`
- `siamrpn_rpn.rknn`
- `siamrpn_template_NHWC.rknn`
- `siamrpn_template_NHWC_128.rknn`
- `siamrpn_track.rknn`

These are SiamRPN (Siamese Region Proposal Network) models used for real-time object tracking. The binary also references YOLO v5/v6/v7/v8 model support.

`/oem/usr/` — application binaries
`/oem/etc/` — configuration files
`/oem/wifi/` — WiFi configuration

---

## Network

### Open ports (confirmed via Fing and netstat)

| Port | Service | Notes |
|------|---------|-------|
| 21 | FTP (vsftpd) | SD card file access |
| 22 | SSH (dropbear) | Root shell access |
| 53 | DNS (dnsmasq) | Used in hotspot mode |
| 80 | HTTP (nginx) | Web interface, SD card browser |
| 1935 | RTMP | Live video stream |
| 5037 | ADB | Android Debug Bridge (localhost only) |
| 5555 | Telescope control API | WebSocket, protobuf format |
| 8082 | Unknown | HTTP, returns 404 on root |
| 8092 | Unknown | Likely WebSocket endpoint |
| 9900 | Telescope control API | WebSocket — confirmed in source code |

### SD card HTTP access

Files on the SD card are accessible via HTTP at:

```
http://<DWARF_IP>/sdcard/
```

This can be used to pull captured images without using FTP or SSH.

### WebSocket API

The main control API uses WebSockets with binary protobuf encoding. The WebSocket URL is:

```
ws://<DWARF_IP>:9900
```

The protocol uses a `WsPacket` wrapper with `cmd` and `data` fields. See the [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) organisation and [stevejcl/dwarf_python_api](https://github.com/stevejcl/dwarf_python_api) for community API documentation and Python bindings.

A keep-alive ping is required: send both a WebSocket ping frame and a text `"ping"` message. The telescope responds with `"pong"`.

### HTTP API routes (extracted from binary strings)

The following HTTP routes were identified from strings in `/usr/bin/dwarf2`:

- `/shootingMode/getSupportedShootingModes`
- `/api/main/status`
- Album management routes
- Firmware version route
- Device info and reset routes
- Log download route
- File MD5 check route
- Parameter config route

---

## Security

> **Warning:** The Dwarf II ships with the same default credentials on every unit.

**Default WiFi hotspot password:** `DWARF_12345678`

**Default SSH credentials:** `root` / `rockchip`

SSH is open on port 22 and grants full root shell access. Anyone on the same network as the telescope can log in without any prior knowledge of your specific device.

**Recommendations:**
- Do not connect the Dwarf II to public WiFi networks
- Do not use the telescope's hotspot in public locations
- Consider changing the SSH root password via `passwd` if you need extra security on trusted networks

---

## Contributing

This is a community effort. If you find anything not documented here, PRs and issues are welcome.

---

## Related projects

- [DwarfTelescopeUsers](https://github.com/DwarfTelescopeUsers) — community GitHub organisation
- [stevejcl/dwarf_python_api](https://github.com/stevejcl/dwarf_python_api) — Python API library
- [stevejcl/dwarfium](https://github.com/stevejcl/dwarfium) — Stellarium integration
- [grosseruser/dwarf2-html](https://github.com/grosseruser/dwarf2-html) — web frontend for the Dwarf II
