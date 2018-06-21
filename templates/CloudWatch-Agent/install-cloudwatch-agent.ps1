param(
    [Parameter(Mandatory = $true)]
    [string] $parametername
)

$url = "https://s3.amazonaws.com/amazoncloudwatch-agent/windows/amd64/latest/AmazonCloudWatchAgent.zip"
$output = "$PSScriptRoot\AmazonCloudWatchAgent.zip"
$unzipath = "$PSScriptRoot\AmazonCloudWatchAgent"

$start_time = Get-Date
(New-Object System.Net.WebClient).DownloadFile($url, $output)
Write-Output "Time taken to download agent zip file: $((Get-Date).Subtract($start_time).Seconds) second(s)"

$start_time = Get-Date
Expand-Archive $output -DestinationPath $unzipath
Write-Output "Time taken to unzip agent file: $((Get-Date).Subtract($start_time).Seconds) second(s)"

$start_time = Get-Date
Set-Location $unzipath
./install.ps1 
Write-Output "Time taken to install the cloudwatch agent: $((Get-Date).Subtract($start_time).Seconds) second(s)"

$start_time = Get-Date
Set-Location $unzipath
./amazon-cloudwatch-agent-ctl.ps1 -a fetch-config -m ec2 -c ssm:$parametername -s
Write-Output "Time taken to start the cloudwatch agent service: $((Get-Date).Subtract($start_time).Seconds) second(s)"
