# Start MySQL (no-admin, user-local install)
$mysqld = "$env:USERPROFILE\Apps\mysql-9.7.1-winx64\bin\mysqld.exe"
$defaults = "--defaults-file=$env:USERPROFILE\Apps\mysql-9.7.1-winx64\my.ini"
Start-Process -FilePath $mysqld -ArgumentList $defaults -WindowStyle Minimized
Write-Host "MySQL starting on port 3306..." -ForegroundColor Green