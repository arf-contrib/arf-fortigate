 <#Script to get users from MFP for the RV Sikuliaq and create AD accounts

Created July 2024 by Julian Race

#>


#Import required PS Modules - These may need to be installed if moving this script to another host.
Import-Module ActiveDirectory
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

#User-configurable variables-------------------------------------------------------------------------------------------------

#Directories

$logFilePath = "C:\scripts\logs\MFP-OnboardingLog.txt"
$sourcePrefix = "SKQ*" #Files must have this prefix before they will be ingested by script

#Email Config
$smtpServer = "mail.sikuliaq.alaska.edu"
$smtpFrom = "UAF-SKQ-IT-Support@alaska.edu"
$SendTo = "UAF-SKQ-IT-Support@alaska.edu" #Email to send import completion status to

#User OU/Group Config
$UserOU = "OU=Transient,OU=SKQ_Users,DC=ad,DC=sikuliaq,DC=alaska,DC=edu"
#$defaultusergroup = "SKQ_Users"

$DefaultGroups = @("SKQ_Users", "AllowInternetAccess")

# User modifiable parameters
$apiKeyCruiseInfo = '<API KEY HERE>' # for cruise info
$apiKeyParticipants = '<API KEY HERE>' # for cruise participant info
$vesselIcesCode = '33BI'  # the ICES code for RV Sikuliaq
$year = (Get-Date).Year  # get the current year
$orgId = 'grid.70738.3b' # from https://grid.ac/
# Runs a query to return a list of cruises for the year
$qryCruises = "schedule/$year/$vesselIcesCode"



#End User-configurable variables---------------------------------------------------------------------------------------------------


#Functions-----------------------------------------------------------------------------------------

# Function to write to log file and echo to the console
function Write-Log {
    param(
        [string]$message,
        [string]$logFilePath = "C:\scripts\Logs\MFP-OnboardingLog.txt"
    )

    # Get the current timestamp
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    # Create the log entry with timestamp and message
    $logEntry = "$timestamp - $message"

    # Check if the log file exists, if not, create it
    if (-not (Test-Path -Path $logFilePath)) {
        New-Item -ItemType File -Path $logFilePath -Force
    }
    # Append the log entry to the logfile
    $logEntry | Out-File -Append -FilePath $logFilePath

    # Check if the script is run interactively
    if (($Host.Name -eq "ConsoleHost") -or ($Host.Name -eq "Windows PowerShell ISE Host")) {
        # If run interactively, print the message to the console
        Write-Host $logEntry
    }
}



# Function to format date to USA short date format
function Format-Date {
    param (
        [string]$dateStr
    )
    $dateObj = [datetime]::ParseExact($dateStr, "yyyy-MM-ddTHH:mm:ss.ffffff0Z", $null)
    return $dateObj.ToString("MM/dd/yyyy")
}

# Get the current date
$currentDate = Get-Date

# Function to make API request
function MfpApiRequest {
    param (
        [string]$apiKey,
        [string]$apiQuery
    )

    try {
        $apiUrlBase = 'https://mfp.us/API/v1/'
        $headers = @{
            'Content-Type' = 'application/json'
            'x-api-key'    = $apiKey
        }
        $apiUrl = "$apiUrlBase$apiQuery"
        Write-Log("Calling API: " + $apiUrl)

        $response = Invoke-RestMethod -Uri $apiUrl -Headers $headers -Method Get

        return $response
    } catch {
        Write-Output "API call to MFP failed."
        Write-Output $_
        return $null
    }
}


# Function to send welcome email
function Send-WelcomeEmail {
    param (
        [string]$To,
        [string]$Username,
        [string]$Password,
        [string]$FirstName
    )

    $emailBody = @"
Dear $FirstName,<br><br>

Welcome to Sikuliaq!<br><br>

Below you will find your computer account information for your upcoming trip onboard the RV Sikuliaq.  This login will allow you to access the Sikuliaq IT systems on the ship, including internet access.<br>
Please keep this information safe!
If you have any questions or concerns, please email uaf-skq-it-support@alaska.edu or reach out to the Marine Technicians on your cruise.<br><br>

<strong>
Your username is: $Username<br>
Your password is: $Password<br><br>
</strong>
<br>
When you arrive onboard, you can connect to our WiFi network with the following information:<br><br>
<strong>
SSID:   Shipwide<br>
Password:  Frozen`$cience<br>
</strong>
<br>
You will then be prompted to log in to our captive portal with your username and password above.<br>
<br>
Finally, while onboard you may find the Sikuliaq Intranet site useful: <br>
<a href="http://web.sikuliaq.alaska.edu">web.sikuliaq.alaska.edu</a>
<br><br>
Best regards,<br>
RV Sikuliaq IT Department
"@
    Write-Log("Sending email to $To")
    Send-MailMessage -To $To -Subject "RV Sikuliaq Computer Account Info" -Body $emailBody -SmtpServer $smtpServer -From $smtpFrom -BodyAsHtml
}


# Function to send an email with a status of the most recent import
function Send-EmailWithResults {
    param(
        [string]$to,
        [string]$subject,
        [array]$duplicates,
        [array]$NewUsers
    )

    $body = @"
<b>Users successfully created during recent import:</b><br>
$(($NewUsers | ForEach-Object { "Username: $($_.Username), Role: $($_.Role)<br>" }) -join "`r`n")
<br>
<b>Duplicate users found during your recent import:</b><br>
$(($duplicates | ForEach-Object { "Username: $($_.Username), Role: $($_.Role)<br>" }) -join "`r`n")
"@
    
    $mailParams = @{
        From       = $smtpFrom
        To         = $to
        Subject    = $subject
        Body       = $body
        SmtpServer = $smtpServer
    }

       Send-MailMessage -BodyAsHtml @mailParams
}

#Function to generate a random, fun, maritime-themed passphrase. Creates about 500k permutations. Add more words to increase this.

function Get-MaritimePassphrase {
    # List of maritime and ocean science themed words
    $maritimeWords = @(
        "Ocean", "Current", "Wave", "Tide", "Nav", "Buoy", "Whale", "Anchor", "Seabed", "Marine", 
        "Coral", "Light", "Harbor", "Fishery", "Rock", "Sailboat", "Aquatic", "Seashell", 
        "Drift", "Seagull", "Maritime", "Cape", "Aqua", "Surf", "Nautical", "Deepsea", 
        "Fishing", "Shoal", "Estuary", "Magnetic", "Riptide", "Swim", "Cruise", "Atlantis", 
        "Hull", "Pirate", "Binnacle", "Pelagic", "Jetty", "Abyssal", "Ice", "Iceberg", "Bridge", "Deck"
    )

    # Initialize an array to track used words
    $usedWords = @()

    # Generate first word
    $word1 = Get-Random -InputObject $maritimeWords
    $usedWords += $word1

    # Generate the second word, ensuring it is not repeated
    do {
        $word2 = Get-Random -InputObject $maritimeWords
    } while ($usedWords -contains $word2)
    $usedWords += $word2

    # Generate the third word, ensuring it is not repeated
    do {
        $word3 = Get-Random -InputObject $maritimeWords
    } while ($usedWords -contains $word3)
    $usedWords += $word3

    $randomNumber1 = Get-Random -Minimum 1 -Maximum 9
    $randomNumber2 = Get-Random -Minimum 1 -Maximum 9
    $randomNumber3 = Get-Random -Minimum 1 -Maximum 9

    # Concatenate words with hyphens and add a random one-digit number
    $passphrase = "{0}{1}{2}{3}{4}{5}" -f $word1, $randomNumber1, $word2, $randomNumber2, $word3, $randomNumber3

    # Ensure the passphrase is at least 14 characters long and not longer than 20 characters
    while ($passphrase.Length -lt 14 -or $passphrase.Length -gt 20) {
        # Regenerate random words until the passphrase is within the length limit
        # and no word is repeated
        $usedWords = @()
        $word1 = Get-Random -InputObject $maritimeWords
        $usedWords += $word1

        do {
            $word2 = Get-Random -InputObject $maritimeWords
        } while ($usedWords -contains $word2)
        $usedWords += $word2

        do {
            $word3 = Get-Random -InputObject $maritimeWords
        } while ($usedWords -contains $word3)
        $usedWords += $word3


        $randomNumber1 = Get-Random -Minimum 1 -Maximum 9
        $randomNumber2 = Get-Random -Minimum 1 -Maximum 9
        $randomNumber3 = Get-Random -Minimum 1 -Maximum 9

        # Concatenate words with hyphens and add a random one-digit number
        $passphrase = "{0}{1}{2}{3}{4}{5}" -f $word1, $randomNumber1, $word2, $randomNumber2, $word3, $randomNumber3
    }

    # Return the passphrase
    return $passphrase
}

# Function to create a username based on first initial and last name. Concatenates any spaces in last names.
function Generate-Username {
    param(
        [string]$firstName,
        [string]$lastName
    )
    $username = ($firstName[0] + $lastName) -replace ' '
    return $username
}


$ButtonClicked = {
 $selectedIndex = $listBox.SelectedIndex
    if ($selectedIndex -ge 0 -and $selectedIndex -lt $filteredEvents.Count) {
        $selectedEvent = $filteredEvents[$selectedIndex]
        [Windows.Forms.MessageBox]::Show("You have selected the following event:`n" + ($selectedEvent | ConvertTo-Json -Compress))
    } else {
        [Windows.Forms.MessageBox]::Show("Invalid choice. Please select a valid event.")
    }

}

#END FUNCTIONS-------------------------------------------------------------------------------------------------

#Initialize Log for current session w/ line break added
Write-Log("------------ New User Import Session Started ------------")

$mfpCruises = MfpApiRequest -apiKey $apiKeyCruiseInfo -apiQuery $qryCruises

# Filter the MFP cruises for those in the future and format the data
$filteredEvents = @()
foreach ($ship in $mfpCruises) {
    foreach ($event in $ship.Events) {
        $startDate = [datetime]::ParseExact($event.EventStartDate, "yyyy-MM-ddTHH:mm:ss.ffffff0Z", $null)
        if ($startDate -gt $currentDate) {
            $formattedEvent = @{
                "AlternateId" = $event.AlternateId
                "EventName"   = $event.EventName
                "StartDate"   = Format-Date -dateStr $event.EventStartDate
                "EndDate"     = Format-Date -dateStr $event.EventEndDate
                "MFP_ID"      = $event.Event_id
            }
            $filteredEvents += $formattedEvent
        }
    }
}

# Print the formatted output
Write-Output "Available Events:"
for ($i = 0; $i -lt $filteredEvents.Count; $i++) {
    $event = $filteredEvents[$i]
    Write-Output ("{0}. AlternateId: {1}, EventName: {2}, StartDate: {3}, EndDate: {4}" -f ($i + 1), $event.AlternateId, $event.EventName, $event.StartDate, $event.EndDate)
}

# Ask the user to pick an AlternateID
$choice = Read-Host -Prompt "Enter the number corresponding to the AlternateId you wish to use"
$choice = [int]$choice - 1

# Ensure the user's choice is within the valid range
if (0 -le $choice -and $choice -lt $filteredEvents.Count) {
    $selectedEvent = $filteredEvents[$choice]
    Write-Output "`nYou have selected the following event:"
    $selectedEvent | ConvertTo-Json | Write-Output
    <# 
    {
    "StartDate":  "07/27/2024",
    "AlternateId":  "CY24 Inspection",
    "MFP_ID":  2170,
    "EventName":  "Inspection",
    "EndDate":  "07/28/2024"
}
    #>
    
    $CruiseID = $selectedEvent.EventName

    $qryParticipants = "programme/cruise/$($selectedEvent.MFP_ID)/cruiseparticipants"
    $lstParticipants = MfpApiRequest -apiKey $apiKeyParticipants -apiQuery $qryParticipants
    #$lstParticipants | ConvertTo-Json | Write-Output

    #We should have a list object that looks like this:
    <#
        {
        "Firstname":  "Ted",
        "Surname":  "Colburn",
        "Role":  "Engineer",
        "EmailAddress":  "ted@jmsnet.com",
        "Organisation":  null
    },
    {
        "Firstname":  "Thomas",
        "Surname":  "Kelly",
        "Role":  "Scientist",
        "EmailAddress":  "tbkelly@alaska.edu",
        "Organisation":  "University of Alaska"
    }
    #>

    #Now create AD entries based on that list
    
# Collect duplicate users in array
$duplicates = @()

#Collect newly created users in array
$NewUsers = @()
# Iterate through each row in the Excel data
foreach ($row in $lstParticipants) {

    $firstName = $row.Firstname
    $lastName = $row.Surname
    $role = $CruiseID + " - " + $row.Role
    $userEmail = $row.EmailAddress
    $organization = $row.Organisation

    # Generate username
    $username = Generate-Username -firstName $firstName -lastName $lastName

    # Generate unique Passphrase

    $userPassword = Get-MaritimePassphrase

    # Check if the user already exists and add to duplicate array for sending the alert email.

    $existingUser = Get-ADUser -Filter {SamAccountName -eq $username} -ErrorAction SilentlyContinue

    if ($existingUser) {
        # Duplicate user found, add to the list
        $duplicates += [PSCustomObject]@{
            Username = $username
            Role = $role
        }
        
        #Log found duplicates
        Write-Log("Duplicate user found: $username $role")

    }
    elseif (-not $existingUser) {
        # User does not exist, proceed with user creation

        # Create the user in the specified OU
        # Define parameters
        $params = @{
            SamAccountName        = $username
            GivenName             = $firstName
            Surname               = $lastName
            UserPrincipalName     = "$username@sikuliaq.alaska.edu"
            EmailAddress          = $userEmail
            Name                  = "$firstName $lastName"
            Description           = $role
            Company               = $organization
            Enabled               = $true
            AccountPassword       = (ConvertTo-SecureString $userPassword -AsPlainText -Force)
            Path                  = $UserOU
}
        # Create User
        try {
            Write-Log("Creating new user $username")
            New-ADUser @params

            # Add the user to the specified security group
    
            foreach ($Group in $DefaultGroups) {
                Write-Log("Adding user to group: $Group")
                Add-ADGroupMember -Identity $Group -Members $username
            }
            #User created - Add to list
            $NewUsers += [PSCustomObject]@{
                Username = $username
                Role = $role
            }
        
           # Set expiration date for users (1 year from today)
            $expirationDate = (Get-Date).AddYears(1)
            Set-ADUser -Identity $username -AccountExpirationDate $expirationDate
            Write-Log("User expiration date set to $expirationDate")

            # Send welcome email to user using the function

            Send-WelcomeEmail -To $row.EmailAddress -Username $username -Password $userPassword -FirstName $row.Firstname

            #Append log with created users and emails sent
            Write-Log("Successfully created user: $username $role $userEmail")
        }
        catch
        {
            Write-Log("ERROR creating user: $username role: $role email: $userEmail   \n error: $_.Exception.Message")
        }

    }
}

# Send email to admin with status of import
$date = "$(get-date)"
Send-EmailWithResults -to $SendTo -subject "Results of AD user import $date UTC" -duplicates $duplicates -NewUsers $NewUsers

} else {
    Write-Output "Invalid choice. Please run the program again and select a valid number."
}
 
