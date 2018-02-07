
Function Invoke-SiteKick {
    <#
    .SYNOPSIS
        Tool for enumerating basic information from websites.
        Author: Jake Miller (@LaconicWolf)

    .DESCRIPTION
        Reads a text file of URLs (one per line) and uses Invoke-WebRequests to 
        attempt to visit the each URL. Returns information regarding any
        redirect, the site Title (if <title> tags are present), and Server type
        (if the server header is present). Can be output to a CSV file.  
         
    .PARAMETER UrlFile
        Mandatory. The file path to the text file containing URLs, one per line.

    .PARAMETER Proxy
        Optional. Send requests through a specified proxy. 
        Example: -Proxy http://127.0.0.1:8080
    
    .PARAMETER CSV
        Optional. Write the output to a CSV file. Will append if the filepath 
        specified already exists.
        
    .PARAMETER Threads
        Optional. Specify number of threads to use. Default is 1.
        
    .PARAMETER Info
        Optional. Increase output verbosity. 

    .EXAMPLE
        PS C:\> Invoke-SiteKick -UrlFile urls.txt -CSV result.csv -Threads 10
        
        [*] Loaded 5 URLs for testing

        [+] File has been written to result.csv

        Title       URL                        Server   RedirectURL            
        -----       ---                        ------   -----------            
        LAN         192.168.0.1                         http://192.168.0.1     
        LAN         https://192.168.0.1/                                       
        LaconicWolf http://www.laconicwolf.net AmazonS3 http://laconicwolf.net/
    #>

    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)]
        $UrlFile,
    
        [Parameter(Mandatory = $false)]
        $Proxy,
    
        [Parameter(Mandatory = $false)]
        $CSV,

        [Parameter(Mandatory = $false)]
        $Threads=1,
        
        [Parameter(Mandatory = $false)]
        [switch]
        $RandomAgent,

        [Parameter(Mandatory = $false)]
        [switch]
        $Info
    )

    # read the url file
    if (Test-Path -Path $UrlFile) { $URLs = Get-Content $UrlFile }
    else {
        Write-Host "`n[-] Please check the URLFile path and try again." -ForegroundColor Yellow
        return
    }

    Write-Host "`n[*] Loaded" $URLs.Length "URLs for testing`n"

    # script that each thread will run
    $ScriptBlock = {
        Param (
            $Url,
            $Proxy,
            $Info
        )

# ignore HTTPS certificate warnings
add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

    
    Function _Get-RandomAgent {
        <#
        .DESCRIPTION
            Helper function that returns a random user-agent.
        #>

        $num = Get-Random -Minimum 1 -Maximum 5
        if($num -eq 1) {
            $ua = [Microsoft.PowerShell.Commands.PSUserAgent]::Chrome
        } 
        elseif($num -eq 2) {
            $ua = [Microsoft.PowerShell.Commands.PSUserAgent]::FireFox
        }
        elseif($num -eq 3) {
            $ua = [Microsoft.PowerShell.Commands.PSUserAgent]::InternetExplorer
        }
        elseif($num -eq 4) {
            $ua = [Microsoft.PowerShell.Commands.PSUserAgent]::Opera
        }
        elseif($num -eq 5) {
            $ua = [Microsoft.PowerShell.Commands.PSUserAgent]::Safari
        }
        return $ua
    }

    # initializes an empty array to store the site's data
    $SiteData = @()

    # sets a random user-agent
    $UserAgent = _Get-RandomAgent

    if ($Info) {Write-Host "`n[*] Checking $URL"}

    # send request to url
    if ($Proxy) {
        Try {
            $Response = Invoke-WebRequest -Uri $URL -UserAgent $UserAgent -Method Get -Proxy $Proxy
        }
        Catch {
            if ($Info) {"[-] Unable to connect to $URL"}
            continue
        }
    }
    else {
        Try {
            $Response = Invoke-WebRequest -Uri $URL -UserAgent $UserAgent -Method Get
        }
        Catch {
            if ($Info) {"[-] Unable to connect to $URL"}
            continue
        }
    }

    # examine response to compare current url and requested url
    if ($Response.BaseResponse.ResponseUri.OriginalString -ne $URL) {
        $RedirectedUrl = $Response.BaseResponse.ResponseUri.OriginalString
    }
    else {
        $RedirectedUrl = ""
    }

    # examines parsed html and extracts title if available
    if ($Response.ParsedHtml.title) {
        $Title = $Response.ParsedHtml.title
    }
    else {
        $Title = ""
    } 

    # examines response headers and extracts the server value if avaible
    if ($Response.Headers.ContainsKey('Server')) {
        $Server = $Response.Headers.Server
    }
    else {
        $Server = ""
    }

    # creates an object with properties from the html data
    $SiteData += New-Object -TypeName PSObject -Property @{
                                    "URL" = $URL
                                    "RedirectURL" = $RedirectedUrl
                                    "Title" = $Title
                                    "Server" = $Server
                                    }
    if ($Info) {$SiteData | Format-Table}

    return $SiteData
    }

    #create the pool where the threads will launch
    $RunspacePool = [RunspaceFactory]::CreateRunspacePool(1, $Threads)
    $RunspacePool.Open()

    $Jobs = @()


    ForEach ($URL in $URLs) {
        
        # maps the command line options to the scriptblock
        if ($Proxy -and -not $Info) {$Job = [powershell]::Create().AddScript($ScriptBlock).AddParameter("Url", $URL).AddParameter("Proxy", $Proxy)}
        elseif ($Info -and -not $Proxy) {$Job = [powershell]::Create().AddScript($ScriptBlock).AddParameter("Url", $URL).AddParameter("Info", $Info)}
        elseif ($Info -and $Proxy) {$Job = [powershell]::Create().AddScript($ScriptBlock).AddParameter("Url", $URL).AddParameter("Info", $Info).AddParameter("Proxy", $Proxy)}
        else {$Job = [powershell]::Create().AddScript($ScriptBlock).AddParameter("Url", $URL)}
        
        # starts a new job for each url
        $Job.RunspacePool = $RunspacePool
        $Jobs += New-Object PSObject -Property @{
            RunNum = $_
            Job = $Job
            Result = $Job.BeginInvoke()
        }
    }

    # combine the return value of each indivual job into the $Data variable
    $Data = @()
    ForEach ($Job in $Jobs) {
        $Data += $Job.Job.EndInvoke($Job.Result)
    }
    
    # display the returned data
    $Data

    # parse to a csv if specified
    if ($CSV) {
        if (-not (Test-Path -Path $CSV) ) {
            "url,redir,title,server,notes" | Out-File -FilePath $CSV -Encoding utf8
        }
        foreach($item in $Data) {
            $item.URL + "," + $item.RedirectURL + "," + $item.Title + "," + $item.Server | Out-File -FilePath $CSV -Append -Encoding utf8
        }
    }

    Write-Host "`n[+] File has been written to $CSV`n"
}