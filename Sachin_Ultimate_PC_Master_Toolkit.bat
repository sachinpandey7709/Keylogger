@echo off
:: Admin check automatically - Ye part check karega ki file admin mode me hai ya nahi
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Kripya is file par Right-Click karein aur "Run as Administrator" chunein.
    pause
    exit
)

setlocal EnableExtensions EnableDelayedExpansion
title ULTIMATE PC MASTER TOOLKIT
color 0F

:menu
cls
echo ============================================================
echo                 ULTIMATE PC MASTER TOOLKIT
echo ============================================================
echo.
echo ================= SYSTEM TOOLS =================
echo 1. msconfig - System Configuration
echo 2. eventvwr - Event Viewer
echo 3. services.msc - Services Manager
echo 4. regedit - Registry Editor
echo 5. msinfo32 - System Information
echo 6. devmgmt.msc - Device Manager
echo 7. diskmgmt.msc - Disk Management
echo 8. cleanmgr - Disk Cleanup
echo 9. control - Control Panel
echo 10. appwiz.cpl - Programs and Features
echo 11. ncpa.cpl - Network Connections
echo 12. firewall.cpl - Windows Firewall
echo 13. powercfg.cpl - Power Options
echo 14. main.cpl - Mouse Properties
echo 15. dxdiag - DirectX Diagnostic Tool
echo 16. mdsched - Memory Diagnostic
echo 17. taskschd.msc - Task Scheduler
echo 18. explorer - File Explorer
echo 19. calc - Calculator
echo 20. cmd - Command Prompt
echo.
echo ================= BONUS TOOLS =================
echo 21. sysdm.cpl - System Properties
echo 22. gpedit.msc - Group Policy Editor
echo 23. optionalfeatures - Windows Features
echo 24. shell:startup - Startup Folder
echo 25. Open Temp Folder
echo 26. winver - Windows Version
echo.
echo ================= NETWORK / CMD =================
echo 27. ipconfig
echo 28. ipconfig /all
echo 29. ipconfig /release
echo 30. ipconfig /renew
echo 31. ipconfig /displaydns
echo 32. ipconfig /flushdns
echo 33. nslookup
echo 34. getmac /v
echo 35. powercfg /energy
echo 36. powercfg /batteryreport
echo 37. chkdsk /f (Needs Restart)
echo 38. chkdsk /r (Needs Restart)
echo 39. sfc /scannow
echo 40. DISM CheckHealth
echo 41. DISM ScanHealth
echo 42. DISM RestoreHealth
echo 43. tasklist
echo 44. taskkill task
echo 45. wlanreport
echo 46. show interfaces
echo 47. show IP address
echo 48. show DNS servers
echo 49. Firewall OFF
echo 50. Firewall ON
echo 51. ping
echo 52. ping -t
echo 53. tracert
echo 54. tracert -d
echo 55. netstat
echo 56. netstat -af
echo 57. netstat -o
echo 58. route print
echo 59. Restart to BIOS
echo 60. Cmd Colors Change
echo 61. taskmgr - Task Manager
echo.
echo ================= INTERNET / BROWSERS =================
echo 62. Chrome
echo 63. Microsoft Edge
echo 64. Firefox
echo 65. Opera
echo.
echo ================= GITHUB / ACCOUNT =================
echo 66. My Github
echo 67. Python Exe Github
echo.
echo 68. Exit
echo.
set /p choice=Select option: 

if "%choice%"=="1" start msconfig & goto menu
if "%choice%"=="2" start eventvwr & goto menu
if "%choice%"=="3" start services.msc & goto menu
if "%choice%"=="4" start regedit & goto menu
if "%choice%"=="5" start msinfo32 & goto menu
if "%choice%"=="6" start devmgmt.msc & goto menu
if "%choice%"=="7" start diskmgmt.msc & goto menu
if "%choice%"=="8" start cleanmgr & goto menu
if "%choice%"=="9" start control & goto menu
if "%choice%"=="10" start appwiz.cpl & goto menu
if "%choice%"=="11" start ncpa.cpl & goto menu
if "%choice%"=="12" start firewall.cpl & goto menu
if "%choice%"=="13" start powercfg.cpl & goto menu
if "%choice%"=="14" start main.cpl & goto menu
if "%choice%"=="15" start dxdiag & goto menu
if "%choice%"=="16" start mdsched & goto menu
if "%choice%"=="17" start taskschd.msc & goto menu
if "%choice%"=="18" start explorer & goto menu
if "%choice%"=="19" start calc & goto menu
if "%choice%"=="20" start cmd & goto menu
if "%choice%"=="21" start sysdm.cpl & goto menu
if "%choice%"=="22" start gpedit.msc & goto menu
if "%choice%"=="23" start optionalfeatures & goto menu
if "%choice%"=="24" start shell:startup & goto menu
if "%choice%"=="25" start %temp% & goto menu
if "%choice%"=="26" start winver & goto menu

if "%choice%"=="27" cls & ipconfig & pause & goto menu
if "%choice%"=="28" cls & ipconfig /all & pause & goto menu
if "%choice%"=="29" cls & ipconfig /release & pause & goto menu
if "%choice%"=="30" cls & ipconfig /renew & pause & goto menu
if "%choice%"=="31" cls & ipconfig /displaydns & pause & goto menu
if "%choice%"=="32" cls & ipconfig /flushdns & pause & goto menu
if "%choice%"=="33" cls & set /p domain=Enter domain: & nslookup !domain! & pause & goto menu
if "%choice%"=="34" cls & getmac /v & pause & goto menu
if "%choice%"=="35" cls & powercfg /energy & echo Report saved in current directory. & pause & goto menu
if "%choice%"=="36" cls & powercfg /batteryreport /output "%userprofile%\Desktop\battery-report.html" & echo Saved to Desktop & pause & goto menu
if "%choice%"=="37" cls & chkdsk /f & pause & goto menu
if "%choice%"=="38" cls & chkdsk /r & pause & goto menu
if "%choice%"=="39" cls & sfc /scannow & pause & goto menu
if "%choice%"=="40" cls & DISM /Online /Cleanup-Image /CheckHealth & pause & goto menu
if "%choice%"=="41" cls & DISM /Online /Cleanup-Image /ScanHealth & pause & goto menu
if "%choice%"=="42" cls & DISM /Online /Cleanup-Image /RestoreHealth & pause & goto menu
if "%choice%"=="43" cls & tasklist & pause & goto menu
if "%choice%"=="44" cls & set /p taskname=Enter process name (example chrome.exe): & taskkill /f /im !taskname! & pause & goto menu
if "%choice%"=="45" cls & netsh wlan show wlanreport & pause & goto menu
if "%choice%"=="46" cls & netsh interface show interface & pause & goto menu
if "%choice%"=="47" cls & ipconfig | findstr /i "IPv4" & pause & goto menu
if "%choice%"=="48" cls & netsh interface ip show dnsservers & pause & goto menu
if "%choice%"=="49" cls & netsh advfirewall set allprofiles state off & pause & goto menu
if "%choice%"=="50" cls & netsh advfirewall set allprofiles state on & pause & goto menu
if "%choice%"=="51" cls & set /p host=Enter host/IP: & ping !host! & pause & goto menu
if "%choice%"=="52" cls & set /p host=Enter host/IP: & ping -t !host! & goto menu
if "%choice%"=="53" cls & set /p host=Enter host/IP: & tracert !host! & pause & goto menu
if "%choice%"=="54" cls & set /p host=Enter host/IP: & tracert -d !host! & pause & goto menu
if "%choice%"=="55" cls & netstat & pause & goto menu
if "%choice%"=="56" cls & netstat -af & pause & goto menu
if "%choice%"=="57" cls & netstat -o & pause & goto menu
if "%choice%"=="58" cls & route print & pause & goto menu
if "%choice%"=="59" shutdown /r /fw /f /t 0
if "%choice%"=="60" cls & color -a & pause & goto menu
if "%choice%"=="61" start taskmgr & goto menu
if "%choice%"=="62" start chrome & goto menu
if "%choice%"=="63" start msedge & goto menu
if "%choice%"=="64" start firefox & goto menu
if "%choice%"=="65" start opera & goto menu
if "%choice%"=="66" start https://github.com/sachinpandey7709?tab=repositories & goto menu
if "%choice%"=="67" start https://github.com/brentvollebregt/auto-py-to-exe & goto menu
if "%choice%"=="68" exit

echo Invalid option selected.
pause
goto menu