# Reference Architecture

These files define the Fortigate ship+hub reference architecture, intended for use 
in lab environments by vessel operators considering Fortigate adoption. The 
reference architecture consists of several major components:

## Shipboard Fortigate (physical HA pair)
- Example global device settings
- Management-only root VDOM
- Ship LAN (sh-lan) VDOM
  - VLAN based local networks
  - DHCP services (including reservations)
  - DNS services (including local domain names and DNS logging)
  - Example onboard firewall rules
- Ship WAN (sh-wan) VDOM
  - Reference Performance SLA's and SDWAN rules for use offshore
  - IPSec Tunneled Internet access to redundant shore hub sites
  - Automatic fallback to local Internet access
  - Application Blocking & logging features
  - Quality of Service (upload side)

## Hub Fortigates
- Redundant Hub VDOMs
  - Shoreside IPSec "tunnel catcher", for routing Internet access via a home institution.
  - Quality of Service (download side)
  - Remote Access


# Example Vessel - R/V Four-Oh Four

The R/V Four-Oh Four provides a public example of how the Fortigate setup may be deployed.
Deployment instructions will be written based upon the example LAN, WAN, and Hub connections
that "exist" on the 404. After defining the 404's LAN and WAN connections, we'l go through
the process of building out the necessary Fortigate infrastructure using FortiManager.

## Four-Oh Four onboard LAN config

The 404 has three onboard networks. The ship's wireless network is on VLAN 101 (Public), and
all users (science party, crew, etc) share the same VLAN. This VLAN also has several printers
and Smart TV's that anyone onboard is free to use (for printing or casting). Finally, some
of the ship's office PC's are connected to this network (via a wired connection). This VLAN is
not considered to be secure. All of the ship's instrumentation and science-data related
servers are on VLAN 102. This network is primarily isolated, however, there are a few publicly
accessible resources allowed through the firewall (HTTP data dashboards, SMB file shares).
Finally, the management interfaces for all IT systems are hosted on a third network - VLAN 103.
This includes the Fortigate firewalls, as well as the management interfaces of the onboard
network switches and wireless access points.

VLAN 101 (Public) is not considered secure. While this network does have Internet access by
default, it only has very limited access to the data services. All traffic passing through
these firewall rules is logged for threat / compromised device detection purposes.

VLAN 102 (Data) is considered secure. Only a limited set of devices are allowed on this 
network, and mission-critical computers used during science ops (example, CTD computer)
have their Internet access blocked.

VLAN 103 (ITMgmt) is also considered secure, however, it is a fundamentally different pool of 
devices than the science computers on the Data network. Since there is no practical reason
why, say, a Wifi AP needs to connect to the data acqusision servers, these are isolated 
from each other, so that a vulnerability on one device cannot be exploited and an attacker
cannot easily jump around the ship.

- VLAN 101 - Public Network
  - IP/Netmask: 192.168.101.1 /24
  - DHCP Range: 192.168.101.101 - 192.168.101.199
- VLAN 102 - Data Network
  - IP/Netmask: 192.168.102.1 /24
  - DHCP Range: 192.168.102.101 - 192.168.102.199
- VLAN 103 - IT Management Network
  - IP/Netmask: 192.168.103.1 /24
  - DHCP Range: 192.168.103.1 - 192.168.103.199
- Onboard domain name: fourohfour.local

__NOTE__: .local domain names should not be used in production. They are only intended for use 
in mDNS (multicast DNS) device discovery - think printers, smart TV's, etc. This is a non-standard
use, purely to demonstrate how the Fortigate's internal DNS service is configured. These should 
never be used in production - this does not conform to the DNS standards, and it's impossible to
get SSL certs for a .local domain.

## Four-Oh Four onboard WAN config

- VLAN 11 - (Wired) Shorelink
   - Static IP: 10.72.43.99/24, Static Gateway: 10.72.43.1
   - Download x Upload: 100x100Mbps
   - Available to anyone
- VLAN 12 - 4G Modem
   - DHCP Client
   - Download x Upload: 50x10Mbps (average)
   - Available to anyone
- VLAN 13 - Main VSAT (Ku-band)
   - DHCP Client
   - Download x Upload: 8x8Mbps (CIR)
   - Available to anyone
- VLAN 14 - Backup VSAT (Ka-band)
   - Static IP: 10.87.254.249/28, Static Gateway: 10.87.254.241
   - Download x Upload: 2x2Mbps (CIR)
   - Available to anyone
- VLAN 15 - Iridium Certus (L-Band)
   - DHCP Client
   - Download x Upload: 0.5x0.25Mbps
   - **Only available for specific devices onboard**
- VLAN 16 - Port-side Starlink
   - DHCP Client
   - Download x Upload: 80x15Mbps
   - Available to anyone
- VLAN 17 - Stbd-side Starlink
   - DHCP Client
   - Download x Upload: 80x15Mbps
   - Available to anyone

# Four-Oh Four Setup Process

1. Implementing the reference architecture on the Four-Oh Four.
   - VDOM Layout (Management & Traffic)
   - Designing inter-VDOM links & IPSec tunnels
2. Hardware Setup
   - Set up physical HA pair on the ship, then set up VDOMs
   - Set up management interface on the shipboard Fortigates
   - Set up VDOMs at the two hub sites (primary + backup)
3. FortiManager Setup
   - Create ADOM for FOF
   - Join VDOM's into the ADOM
   - Populate address objects, security profiles, and metadata variables
4. Device Configuration, part I
   - Edit ship-specific CLI templates as needed (**SS** in filename)
   - Deploy all CLI templates that do not require address objects
   - Perform non-template based configuration (DHCP Reservations, populate local DNS database)
5. Policy Packages
   - Import example firewall rules
   - Adjust as needed, and push to the devices
6. Device Configuration, part II
   - Deploy CLI templates that do require address objects (SDWAN Rules)
7. Ongoing Maintenance
   - Change Control
   - Minor version updates
   - Major version updates
