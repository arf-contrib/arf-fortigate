Example scripts to start populating address objects, address object groups, and security profiles in a brand-new ADOM.

Naming Conventions:
- **SS** indicates a **S**hip-**S**pecific file. These will reflect the example RV Four-Oh Four config, but should be updated for your own environment.
- **X** Indicates a file that's not normally  e**X**ecuted. These are only run when making a new ADOM, or if the list has been updated.

The names of these objects are significant as they are referenced in two other locations:
- Policy Packages (used as source and/or destination addresses)
- SDWAN Rules (used as source address objects).

In FortiManager, these are added to Device Manager -> Scripts -> (Create New or Edit). When running, the target is "ADOM Database"
