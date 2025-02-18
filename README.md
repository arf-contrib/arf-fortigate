# ARF Firewall Project
The ARF Firewall Project is a multi-institution effort to deploy next-generation 
firewalls, logging, and change management across the US Academic Research Fleet. 
Practical solutions to the US Coast Guard cybersecurity mandates are a core part
of this project.  Fortinet's Fortigate/FortiAnalyzer/FortiManager was the platform 
selected. These efforts began in early 2023 and continue to this day. 
This GitHub repository is a collection of scripts, reference configs, and technical
notes based upon practical experience installing and using these devices. Major
components of the repository are:

* reference-arch74 - FortiOS v7.4 CLI configs necessary to get an example installation running. Uses R/V Four-Oh Four as an example.
* fourdaddress - Python script to update & sync Forti address objects/groups
* fourdquota - Simple quota script to ban/throttle devices on the network
